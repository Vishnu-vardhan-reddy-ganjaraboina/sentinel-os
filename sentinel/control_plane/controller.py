"""
Kernel controller for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sentinel.control_plane.audit import (
    ControlAuditEvent,
    ControlAuditRecorder,
)
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.callers import ControlCallerType
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.interfaces import ControlAuthorizerProtocol
from sentinel.control_plane.policy import ControlPolicy
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.target import KernelControlTarget
from sentinel.control_plane.validator import ControlRequestValidator

_SENSITIVE_AUDIT_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "credential",
    "credentials",
    "private_key",
    "client_secret",
}


def _safe_audit_error(
    command: KernelCommand,
    error: str | None,
) -> str | None:
    """Return a safe, bounded error description for audit records."""
    if error is None:
        return None

    # Preserve known controller-generated messages that contain no
    # arbitrary exception details or credential values.
    if error == "Permission denied: 'control' permission required.":
        return error

    if error == "Service value must be a string.":
        return error


    return f"Command '{command.value}' failed."


def _sanitize_audit_value(value: Any) -> Any:
    """Redact sensitive fields in audit data without changing the request."""
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}

        for key, item in value.items():
            raw_key = str(key).replace("-", "_").replace(".", "_")
            normalized_key = "".join(
                "_" + char.lower()
                if char.isupper()
                and index > 0
                and (
                    raw_key[index - 1].islower()
                    or raw_key[index - 1].isdigit()
                )
                else char.lower()
                for index, char in enumerate(raw_key)
            )
            key_parts = normalized_key.split("_")

            sensitive = (
                normalized_key in _SENSITIVE_AUDIT_KEYS
                or any(
                    part in _SENSITIVE_AUDIT_KEYS
                    for part in key_parts
                )
            )

            if sensitive:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_audit_value(item)

        return sanitized

    if isinstance(value, (list, tuple)):
        return [_sanitize_audit_value(item) for item in value]

    return value

class KernelController:
    """
    Execute and authorize Kernel Control Plane requests.

    Responsibilities:

    1. Build ControlRequest objects.
    2. Validate requests.
    3. Authorize commands.
    4. Dispatch commands to the Kernel control target.
    5. Convert execution failures into ControlResult objects.
    6. Record audit events.

    The controller does not own Kernel lifecycle or service lifecycle.
    """

    __slots__ = (
        "_target",
        "_authorizer",
        "_context",
        "_audit_recorder",
        "_use_caller_policy",
    )

    def __init__(
        self,
        target: KernelControlTarget,
        authorizer: ControlAuthorizerProtocol,
        context: ControlContext,
        audit_recorder: ControlAuditRecorder | None = None,
        use_caller_policy: bool = True,
    ) -> None:
        self._target = target
        self._authorizer = authorizer
        self._context = context
        self._audit_recorder = audit_recorder
        self._use_caller_policy = use_caller_policy

    @property
    def target(self) -> KernelControlTarget:
        """Return the control target."""
        return self._target

    @property
    def authorizer(self) -> ControlAuthorizerProtocol:
        """Return the configured authorizer."""
        return self._authorizer

    @property
    def context(self) -> ControlContext:
        """Return the controller's default context."""
        return self._context

    @property
    def audit_recorder(self) -> ControlAuditRecorder | None:
        """Return the configured audit recorder."""
        return self._audit_recorder

    @property
    def use_caller_policy(self) -> bool:
        """Return whether caller-type policy resolution is enabled."""
        return self._use_caller_policy

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
        Validate, authorize, execute, and audit a structured request.
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

            return self._audit_result(request, result)

        except (TypeError, ValueError) as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )

            return self._audit_result(request, result)

        except Exception as exc:
            result = ControlResult(
                success=False,
                command=request.command.value,
                error=str(exc),
            )

            return self._audit_result(request, result)

    def _authorize(
        self,
        request: ControlRequest,
    ) -> None:
        """
        Authorize the requested command.

        The required Control Plane permission is determined by
        ControlPolicy. The appropriate authorizer is then resolved
        for the request.
        """
        permission = ControlPolicy.required_permission(
            request.command,
        )

        authorizer = self._authorizer_for_request(request)

        authorizer.require(
            request.context,
            permission,
        )

    def _authorizer_for_request(
        self,
        request: ControlRequest,
    ) -> ControlAuthorizerProtocol:
        """
        Resolve the authorizer for a request.

        When caller-policy resolution is enabled, known Sentinel
        caller types use their caller-specific permissions.

        When caller-policy resolution is disabled, the configured
        authorizer is always used directly.

        The latter mode allows external authorization backends such
        as SecurityControlAuthorizer to remain authoritative.
        """
        if not self._use_caller_policy:
            return self._authorizer

        if request.context is self._context:
            return self._authorizer

        if isinstance(request.context.caller_type, ControlCallerType):
            return ControlAuthorizer.from_context(
                request.context,
            )

        return ControlAuthorizer(permissions=())

    def _execute_and_audit(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        """
        Execute a validated and authorized request and audit the result.
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

        return self._audit_result(request, result)

    def _dispatch(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        """
        Dispatch a validated and authorized command.
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

        An unhealthy system is still a successfully executed health
        command. The actual health state is represented by
        data["healthy"].
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
        Extract a validated service name.
        """
        service = data["service"]

        if not isinstance(service, str):
            raise TypeError(
                "Service value must be a string."
            )

        return service

    def _audit_result(
        self,
        request: ControlRequest,
        result: ControlResult,
    ) -> ControlResult:
        """Preserve the operation result when audit recording fails."""
        try:
            self._record_audit(request, result)
        except Exception:
            return ControlResult(
                success=result.success,
                command=result.command,
                data=result.data,
                error=_safe_audit_error(request.command, result.error),
                audit_error="Audit recording failed.",
            )

        return result

    def _record_audit(
        self,
        request: ControlRequest,
        result: ControlResult,
    ) -> None:
        """
        Record an audit event when an audit recorder is configured.
        """
        if self._audit_recorder is None:
            return

        event = ControlAuditEvent(
            caller_id=request.context.caller_id,
            caller_type=request.context.caller_type,
            command=request.command.value,
            success=result.success,
            data=_sanitize_audit_value(request.data),
            error=_safe_audit_error(request.command, result.error),
        )

        self._audit_recorder.record(event)
