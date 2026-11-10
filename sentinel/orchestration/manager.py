"""
Manager for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock, RLock
from typing import Any

from sentinel.brain.intent_resolver import DefaultIntentResolver
from sentinel.brain.manager import BrainManager
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.validation import (
    CapabilityArgumentValidationError,
    validate_capability_arguments,
)
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.exceptions import (
    OrchestrationExecutionError,
    OrchestrationValidationError,
)
from sentinel.orchestration.interfaces import (
    OrchestrationRequest as OrchestrationRequestInterface,
)
from sentinel.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)
from sentinel.security.constants import Permission
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class OrchestrationManager:
    """
    High-level manager for orchestration operations.

    The manager validates requests, retrieves relevant Memory and
    Knowledge context, delegates reasoning to the Brain, authorizes
    capability execution through Security, executes authorized
    capabilities, and persists successful results in Memory.
    """

    def __init__(
        self,
        handler: Callable[[OrchestrationRequest], Any] | None = None,
        brain: BrainManager | None = None,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
        knowledge: KnowledgeService | None = None,
    ) -> None:
        self._handler = handler

        self._state_lock = RLock()
        self._request_locks: dict[str, tuple[Lock, int]] = {}

        self._capabilities = (
            capabilities
            if capabilities is not None
            else CapabilityManager()
        )
        self._brain = (
            brain
            if brain is not None
            else BrainManager(
                intent_resolver=DefaultIntentResolver(
                    capabilities=self._capabilities,
                )
            )
        )
        self._security = (
            security
            if security is not None
            else SecurityManager()
        )

        self._identity = identity

        self._memory = (
            memory
            if memory is not None
            else MemoryService()
        )

        self._knowledge = knowledge

    @property
    def handler(
        self,
    ) -> Callable[[OrchestrationRequest], Any] | None:
        """Return the configured custom handler."""
        return self._handler

    @property
    def brain(self) -> BrainManager:
        """Return the Brain manager."""
        return self._brain

    @property
    def capabilities(self) -> CapabilityManager:
        """Return the capability manager."""
        return self._capabilities


    @property
    def identity(self) -> SecurityIdentity | None:
        """Return the identity used for authorization."""
        return self._identity

    @property
    def memory(self) -> MemoryService:
        """Return the shared Memory service."""
        return self._memory

    @property
    def knowledge(self) -> KnowledgeService | None:
        """Return the shared Knowledge service."""
        return self._knowledge

    def execute(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """
        Execute an orchestration request.

        Requests sharing an ID are serialized. Different request IDs
        may execute concurrently.
        """
        self._validate(request)
        request_id = request.id

        request_lock = self._acquire_request_lock(request_id)

        try:
            try:
                if self._handler is not None:
                    result = self._handler(request)
                else:
                    result = self._execute_with_brain(request)

            except AuthorizationError:
                raise

            except OrchestrationExecutionError:
                raise

            except Exception as exc:
                raise OrchestrationExecutionError(
                    f"Orchestration request '{request_id}' failed."
                ) from exc

            orchestration_result = OrchestrationResult(
                request_id=request_id,
                success=True,
                data=result,
            )

            self._persist_result(orchestration_result)

            return orchestration_result

        finally:
            self._release_request_lock(request_id, request_lock)

    def execute_goal(
        self,
        request_id: str,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """
        Resolve a user goal into an Intent and execute it.

        Intent resolution is performed by the configured Brain manager.
        Execution continues through the normal orchestration pipeline.
        """
        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string.")

        if not request_id.strip():
            raise ValueError("request_id must not be empty.")

        if not isinstance(input, str):
            raise TypeError("input must be a string.")

        if not input.strip():
            raise ValueError("input must not be empty.")

        if context is not None and not isinstance(context, dict):
            raise TypeError("context must be a dictionary or None.")

        intent = self._brain.resolve_intent(
            input=input,
            context=context,
        )

        request = OrchestrationRequest(
            request_id=request_id,
            input=input,
            context=context,
            intent=intent,
        )

        return self.execute(request)
    def can_execute(
        self,
        request: OrchestrationRequest,
    ) -> bool:
        """
        Return whether the request can be executed.
        """
        try:
            self._validate(request)
        except (TypeError, OrchestrationValidationError):
            return False

        return True

    def _acquire_request_lock(self, request_id: str) -> Lock:
        """
        Acquire the lock associated with a request ID.

        Reference counting keeps the lock registered while callers
        are waiting for or holding it.
        """
        with self._state_lock:
            entry = self._request_locks.get(request_id)

            if entry is None:
                request_lock = Lock()
                self._request_locks[request_id] = (request_lock, 1)
            else:
                request_lock, users = entry
                self._request_locks[request_id] = (
                    request_lock,
                    users + 1,
                )

        try:
            request_lock.acquire()
        except BaseException:
            self._remove_request_lock_reference(
                request_id,
                request_lock,
            )
            raise

        return request_lock

    def _release_request_lock(
        self,
        request_id: str,
        request_lock: Lock,
    ) -> None:
        """
        Release a request lock and remove its reference.
        """
        request_lock.release()

        self._remove_request_lock_reference(
            request_id,
            request_lock,
        )

    def _remove_request_lock_reference(
        self,
        request_id: str,
        request_lock: Lock,
    ) -> None:
        """
        Remove one reference and delete unused request locks.
        """
        with self._state_lock:
            entry = self._request_locks.get(request_id)

            if entry is None or entry[0] is not request_lock:
                return

            users = entry[1] - 1

            if users == 0:
                del self._request_locks[request_id]
            else:
                self._request_locks[request_id] = (
                    request_lock,
                    users,
                )

    def _execute_with_brain(
        self,
        request: OrchestrationRequest,
    ) -> dict[str, Any]:
        """
        Execute a request through the Brain subsystem.

        Relevant memories and knowledge are retrieved from their
        shared services and made available to the Brain through
        the execution context.
        """
        memories = self._memory.search(
            str(request.input),
        )

        memory_context = [
            memory.to_dict()
            for memory in memories
            if not memory.expired
        ]

        knowledge_context: list[dict[str, Any]] = []

        if self._knowledge is not None:
            chunks = self._knowledge.search(
                str(request.input),
            )

            knowledge_context = [
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "index": chunk.index,
                    "metadata": chunk.metadata.copy(),
                }
                for chunk in chunks
            ]

        context_data = self._build_brain_context(
            request=request,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )

        context = self._brain.create_context(
            context_id=request.id,
            **context_data,
        )

        result = self._brain.execute(
            request=request.input,
            context=context,
        )

        result_context = result.get("context")

        if isinstance(result_context, dict):
            result_context["memories"] = memory_context
            result_context["knowledge"] = knowledge_context

            result_data = result_context.get("data")
            if isinstance(result_data, dict):
                discovery = result_data.get("capability_discovery")
                if (
                    isinstance(discovery, dict)
                    and discovery.get("selection_reason")
                    == "needs_clarification"
                ):
                    missing = discovery.get("missing_required_arguments")
                    capability_id = discovery.get("capability_id")

                    if (
                        isinstance(missing, list)
                        and missing
                        and all(isinstance(item, str) for item in missing)
                        and isinstance(capability_id, str)
                    ):
                        names = ", ".join(missing)
                        return {
                            "status": "needs_clarification",
                            "capability_id": capability_id,
                            "missing_arguments": missing,
                            "message": (
                                "Please provide the required information: "
                                f"{names}."
                            ),
                        }

        return self._execute_plan(result)

    def _execute_plan(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Authorize and execute capability steps contained in a Brain result.
        """
        plan = result.get("plan")

        if not isinstance(plan, dict):
            raise OrchestrationExecutionError(
                "Brain returned an invalid plan."
            )

        steps = plan.get("steps")

        if not isinstance(steps, list):
            raise OrchestrationExecutionError(
                "Brain plan contains invalid steps."
            )

        capability_results: list[dict[str, Any]] = []

        for step in steps:
            if not isinstance(step, dict):
                raise OrchestrationExecutionError(
                    "Brain plan contains an invalid step."
                )

            capability_id = step.get("capability_id")

            if capability_id is None:
                continue

            if not isinstance(capability_id, str) or not capability_id:
                raise OrchestrationExecutionError(
                    "Brain plan contains an invalid capability ID."
                )

            arguments = step.get("arguments", {})

            if not isinstance(arguments, dict):
                raise OrchestrationExecutionError(
                    f"Arguments for capability '{capability_id}' "
                    "must be a dictionary."
                )

            self._validate_capability(
                capability_id,
            )

            self._authorize_capability(capability_id)

            capability = self._capabilities.get(capability_id)

            try:
                validate_capability_arguments(
                    capability.metadata.input_schema,
                    arguments,
                )
            except CapabilityArgumentValidationError as exc:
                raise OrchestrationExecutionError(
                    f"Invalid arguments for capability '{capability_id}': "
                    f"{exc}"
                ) from exc

            try:
                capability_result = self._capabilities.execute_instance(
                    capability,
                    **arguments,
                )
            except OrchestrationExecutionError:
                raise
            except Exception as exc:
                raise OrchestrationExecutionError(
                    f"Capability '{capability_id}' execution failed."
                ) from exc

            capability_results.append(
                {
                    "step": step.get("step"),
                    "capability_id": capability_id,
                    "result": capability_result,
                }
            )

        if capability_results:
            result["capability_results"] = capability_results

        return result

    def _validate_capability(
        self,
        capability_id: str,
    ) -> None:
        """
        Validate that a capability exists and is enabled.

        Capability validation is deliberately performed before
        authorization and execution.
        """
        if not self._capabilities.exists(capability_id):
            raise OrchestrationExecutionError(
                f"Capability '{capability_id}' is not registered."
            )

        capability = self._capabilities.get(
            capability_id,
        )

        if not capability.enabled:
            raise OrchestrationExecutionError(
                f"Capability '{capability_id}' is disabled."
            )

    def _authorize_capability(
        self,
        capability_id: str,
    ) -> None:
        """
        Authorize execution of a capability.

        Every capability execution requires Permission.EXECUTE.
        """
        if self._identity is None:
            raise AuthorizationError(
                f"Identity is required to execute capability "
                f"'{capability_id}'."
            )

        if not self._security.authorize(
            self._identity,
            Permission.EXECUTE,
        ):
            raise AuthorizationError(
                f"Identity '{self._identity.id}' is not authorized "
                f"to execute capability '{capability_id}'."
            )

    def _persist_result(
        self,
        result: OrchestrationResult,
    ) -> None:
        """
        Persist a successful orchestration result in shared Memory.
        """
        memory_id = f"orchestration:{result.request_id}"

        self._memory.upsert(
            memory_id=memory_id,
            content=result.to_dict(),
        )

    def _validate(
        self,
        request: OrchestrationRequest,
    ) -> None:
        """
        Validate an orchestration request.
        """
        if not isinstance(request, OrchestrationRequestInterface):
            raise TypeError(
                "request must implement OrchestrationRequest."
            )

        request_id = request.id

        if not isinstance(request_id, str):
            raise OrchestrationValidationError(
                "Orchestration request ID must be a string."
            )

        if not request_id.strip():
            raise OrchestrationValidationError(
                "Orchestration request ID cannot be empty."
            )

        if not isinstance(request.input, str):
            raise OrchestrationValidationError(
                "Orchestration request input must be a string."
            )

        if not request.input.strip():
            raise OrchestrationValidationError(
                "Orchestration request input cannot be empty."
            )

        if not isinstance(request.context, dict):
            raise OrchestrationValidationError(
                "Orchestration request context must be a dictionary."
            )

    def _get_capability_context(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return capability metadata for Brain planning.

        Only descriptive metadata is exposed to the Brain.
        Capability instances and executable methods are never placed
        into the Brain context.
        """
        return [
            {
                "capability_id": capability.id,
                "name": capability.name,
                "description": capability.description,
                "version": capability.version,
                "enabled": capability.enabled,
                "metadata": capability.metadata.to_dict(),
            }
            for capability in self._capabilities.list()
            if capability.enabled
        ]

    def _build_brain_context(
        self,
        request: OrchestrationRequest,
        memory_context: list[dict[str, Any]],
        knowledge_context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Build the context supplied to the Brain.

        Intent provides structured defaults for Brain planning.
        Explicit request context takes precedence over Intent-derived
        values.
        """
        context_data: dict[str, Any] = {}

        if request.intent is not None:
            context_data.update(
                dict(request.intent.context)
            )

            if request.intent.capability_id is not None:
                context_data["capability_id"] = (
                    request.intent.capability_id
                )

            context_data["capability_arguments"] = dict(
                request.intent.arguments
            )

        context_data.update(request.context)

        context_data["memories"] = memory_context
        context_data["knowledge"] = knowledge_context
        context_data["capabilities"] = self._get_capability_context()

        return context_data
