"""
Manager for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.brain.manager import BrainManager
from sentinel.capabilities.manager import CapabilityManager
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

    The manager validates requests, delegates reasoning to the Brain,
    authorizes capability execution through Security, executes
    authorized capabilities, and persists successful results in Memory.
    """

    def __init__(
        self,
        handler: Callable[[OrchestrationRequest], Any] | None = None,
        brain: BrainManager | None = None,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
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
        """Return the Memory service."""
        return self._memory

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

        Successful orchestration results are persisted in shared Memory.
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

        Relevant memories are retrieved from the shared Memory service
        and made available to the Brain through the execution context.
        """
        memories = self._memory.search(
            str(request.input),
        )

        memory_context = [
            memory.to_dict()
            for memory in memories
            if not memory.expired
        ]

        context_data = dict(request.context)
        context_data["memories"] = memory_context

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