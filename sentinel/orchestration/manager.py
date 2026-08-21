"""
Manager for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.brain.manager import BrainManager
from sentinel.capabilities.manager import CapabilityManager
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.exceptions import (
    OrchestrationExecutionError,
    OrchestrationValidationError,
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

        self._brain = (
            brain
            if brain is not None
            else BrainManager()
        )

        self._capabilities = (
            capabilities
            if capabilities is not None
            else CapabilityManager()
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
    def security(self) -> SecurityManager:
        """Return the Security manager."""
        return self._security

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

        A custom handler takes precedence when configured.
        Otherwise the request is passed through the Brain and any
        capability identified by the resulting plan is authorized
        and executed.

        Successful orchestration results are persisted in Memory.
        """
        self._validate(request)

        try:
            if self._handler is not None:
                result = self._handler(request)
            else:
                result = self._execute_with_brain(request)

        except AuthorizationError:
            raise

        except Exception as exc:
            raise OrchestrationExecutionError(
                f"Orchestration request '{request.id}' failed."
            ) from exc

        orchestration_result = OrchestrationResult(
            request_id=request.id,
            success=True,
            data=result,
        )

        self._persist_result(orchestration_result)

        return orchestration_result

    def can_execute(
        self,
        request: OrchestrationRequest,
    ) -> bool:
        """
        Return whether the request can be executed.
        """
        return bool(request.id.strip())

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

        context_data = dict(request.context)
        context_data["memories"] = memory_context
        context_data["knowledge"] = knowledge_context
        context_data["capabilities"] = self._get_capability_context()

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

            self._authorize_capability(capability_id)

            capability_result = self._capabilities.execute(
                capability_id,
                **arguments,
            )

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

        capability = self._capabilities.registry.get(
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

        if self._memory.exists(memory_id):
            self._memory.remove(memory_id)

        self._memory.create(
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
        if not request.id.strip():
            raise OrchestrationValidationError(
                "Orchestration request ID cannot be empty."
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