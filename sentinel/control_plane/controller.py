"""
Kernel controller for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from typing import Any, Mapping


from sentinel.control_plane.audit import (
    ControlAuditEvent,
    ControlAuditRecorder,
)

from sentinel.control_plane.audit import ControlAuditEvent
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.policy import ControlPolicy
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.target import KernelControlTarget
from sentinel.control_plane.validator import ControlRequestValidator



class KernelController:
    """
    Execute and authorize Kernel Control Plane requests.

    The controller is responsible for:

    1. Building ControlRequest objects.
    2. Validating requests.
    3. Authorizing commands.
    4. Executing commands against the Kernel target.
    5. Converting execution failures into ControlResult objects.
    6. Recording audit events.

    The controller does not own Kernel lifecycle or service lifecycle.
    """

    __slots__ = (
        "_target",
        "_authorizer",
        "_context",
        "_audit_recorder",
    )

    def __init__(
        self,
        target: KernelControlTarget,
        authorizer: ControlAuthorizer,
        context: ControlContext,
        audit_recorder: ControlAuditRecorder | None = None,
    ) -> None:
        self._target = target
        self._authorizer = authorizer
        self._context = context
        self._audit_recorder = audit_recorder

    @property
    def target(self) -> KernelControlTarget:
        """Return the control target."""
        return self._target

    @property
    def authorizer(self) -> ControlAuthorizer:
        """Return the authorization component."""
        return self._authorizer

    @property
    def context(self) -> ControlContext:
        """Return the default controller context."""
        return self._context

    @property
    def audit_recorder(self) -> ControlAuditRecorder | None:
        """Return the configured audit recorder."""
        return self._audit_recorder

    def execute(
        self,
        command: KernelCommand,
        data: Mapping[str, Any] | None = None,
    ) -> ControlResult:
        """
        Execute a command using the controller's default context.
        """
        request = ControlRequest(
            command=command,
            context=self._context,
            data={} if data is None else data,
        )

        return self.execute_request(request)

    def execute_request(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        """
        Validate, authorize, execute, and audit a control request.
        """
        try:
            ControlRequestValidator.validate(
                request.command,
                request.data,
            )

            self._authorize(request)

            return self._execute_and_audit(request)

        except PermissionError as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )
            self._record_audit(request, result)
            return result

        except (TypeError, ValueError) as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )
            self._record_audit(request, result)
            return result

        except Exception as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )
            self._record_audit(request, result)
            return result

    def _authorize(
        self,
        request: ControlRequest,
    ) -> None:
        """
        Authorize a control request using the command policy.
        """
        permission = ControlPolicy.required_permission(
            request.command,
        )

        self._authorizer.require(
            request.context,
            permission,
        )

    def _execute_and_audit(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        """
        Execute a validated and authorized request, then audit it.
        """
        try:
            result = self._dispatch(
                request.command,
                request.data,
            )
        except PermissionError as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )
        except Exception as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )

        self._record_audit(request, result)

        return result

    def _dispatch(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Dispatch a command to its corresponding handler.
        """
        if command is KernelCommand.SYSTEM_STATUS:
            return self._system_status()

        if command is KernelCommand.SYSTEM_HEALTH:
            return self._system_health()

        if command is KernelCommand.SERVICE_LIST:
            return self._service_list()

        if command is KernelCommand.SERVICE_STATUS:
            return self._service_status(data)

        if command is KernelCommand.SERVICE_START:
            return self._service_start(data)

        if command is KernelCommand.SERVICE_STOP:
            return self._service_stop(data)

        if command is KernelCommand.SERVICE_RESTART:
            return self._service_restart(data)

        raise ValueError(
            f"Unsupported control command: '{command.value}'."
        )

    def _system_status(self) -> ControlResult:
        """
        Return the current Kernel service status.
        """
        services = self._target.service_names()

        return ControlResult(
            success=True,
            command=KernelCommand.SYSTEM_STATUS.value,
            data={
                "services": services,
                "service_count": len(services),
            },
        )

    def _system_health(self) -> ControlResult:
        """
        Return the current Kernel health information.

        A health result indicating an unhealthy system is still a
        successfully executed control command. Therefore, the command
        result remains successful while the actual health state is
        represented by data["healthy"].
        """
        health = self._target.health()

        return ControlResult(
            success=True,
            command=KernelCommand.SYSTEM_HEALTH.value,
            data=dict(health),
        )

    def _service_list(self) -> ControlResult:
        """
        Return all registered service names.
        """
        services = self._target.service_names()

        return ControlResult(
            success=True,
            command=KernelCommand.SERVICE_LIST.value,
            data={
                "services": services,
            },
        )

    def _service_status(
        self,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Return the state of a specific service.
        """
        service = self._service_name(data)

        state = self._target.service_state(service)

        return ControlResult(
            success=True,
            command=KernelCommand.SERVICE_STATUS.value,
            data={
                "service": service,
                "state": state.value,
            },
        )

    def _service_start(
        self,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Start a specific service.
        """
        service = self._service_name(data)

        self._target.start_service(service)

        return ControlResult(
            success=True,
            command=KernelCommand.SERVICE_START.value,
            data={
                "service": service,
                "state": self._target.service_state(service).value,
            },
        )

    def _service_stop(
        self,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Stop a specific service.
        """
        service = self._service_name(data)

        self._target.stop_service(service)

        return ControlResult(
            success=True,
            command=KernelCommand.SERVICE_STOP.value,
            data={
                "service": service,
                "state": self._target.service_state(service).value,
            },
        )

    def _service_restart(
        self,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Restart a specific service.
        """
        service = self._service_name(data)

        self._target.restart_service(service)

        return ControlResult(
            success=True,
            command=KernelCommand.SERVICE_RESTART.value,
            data={
                "service": service,
                "state": self._target.service_state(service).value,
            },
        )

    @staticmethod
    def _service_name(
        data: Mapping[str, Any],
    ) -> str:
        """
        Extract a validated service name from command data.
        """
        service = data["service"]

        if not isinstance(service, str):
            raise TypeError(
                "Service value must be a string."
            )

        return service

    def _record_audit(
        self,
        request: ControlRequest,
        result: ControlResult,
    ) -> None:
        """
        Record a control-plane audit event when an audit recorder exists.
        """
        if self._audit_recorder is None:
            return

        event = ControlAuditEvent(
            caller_id=request.context.caller_id,
            caller_type=request.context.caller_type,
            command=request.command.value,
            success=result.success,
            data=request.data,
            error=result.error,
        )

        self._audit_recorder.record(event)