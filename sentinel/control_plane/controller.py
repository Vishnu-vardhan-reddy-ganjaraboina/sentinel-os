"""
Command controller for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.policy import ControlPolicy
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.target import KernelControlTarget
from sentinel.core.exceptions import SentinelError


class KernelController:
    """
    Execute Kernel Control Plane requests against a control target.

    Authorization is evaluated before a command is executed.
    """

    __slots__ = ("_target", "_authorizer", "_context")

    def __init__(
        self,
        target: KernelControlTarget,
        authorizer: ControlAuthorizer,
        context: ControlContext,
    ) -> None:
        self._target = target
        self._authorizer = authorizer
        self._context = context

    @property
    def target(self) -> KernelControlTarget:
        """Return the configured control target."""
        return self._target

    @property
    def authorizer(self) -> ControlAuthorizer:
        """Return the configured authorizer."""
        return self._authorizer

    @property
    def context(self) -> ControlContext:
        """Return the caller context."""
        return self._context

    def execute(
        self,
        command: KernelCommand,
        data: Mapping[str, Any] | None = None,
    ) -> ControlResult:
        """
        Execute a command using the controller's configured context.
        """
        request = ControlRequest(
            command=command,
            context=self._context,
            data=data or {},
        )

        return self.execute_request(request)

    def execute_request(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        """
        Authorize and execute a structured Control Plane request.
        """
        command = request.command

        try:
            permission = ControlPolicy.required_permission(command)

            self._authorizer.require(
                request.context,
                permission,
            )

            command_data = dict(request.data)

            if command is KernelCommand.SYSTEM_STATUS:
                return self._system_status(command)

            if command is KernelCommand.SYSTEM_HEALTH:
                return self._system_health(command)

            if command is KernelCommand.SERVICE_LIST:
                return self._service_list(command)

            if command is KernelCommand.SERVICE_STATUS:
                return self._service_status(command, command_data)

            if command is KernelCommand.SERVICE_START:
                return self._service_start(command, command_data)

            if command is KernelCommand.SERVICE_STOP:
                return self._service_stop(command, command_data)

            if command is KernelCommand.SERVICE_RESTART:
                return self._service_restart(command, command_data)

            return ControlResult(
                success=False,
                command=str(command),
                error=f"Unsupported command: {command}",
            )

        except PermissionError as exc:
            return ControlResult(
                success=False,
                command=str(command),
                error=str(exc),
            )
        except SentinelError as exc:
            return ControlResult(
                success=False,
                command=str(command),
                error=str(exc),
            )
        except Exception as exc:
            return ControlResult(
                success=False,
                command=str(command),
                error=str(exc),
            )

    def _system_status(self, command: KernelCommand) -> ControlResult:
        services = self._target.service_names()

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "services": services,
                "service_count": len(services),
            },
        )

    def _system_health(self, command: KernelCommand) -> ControlResult:
        return ControlResult(
            success=True,
            command=str(command),
            data=dict(self._target.health()),
        )

    def _service_list(self, command: KernelCommand) -> ControlResult:
        services = self._target.service_names()

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "services": services,
            },
        )

    def _service_status(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        name = self._require_service_name(data)
        state = self._target.service_state(name)

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "service": name,
                "state": state.value,
                "running": state.value == "running",
            },
        )

    def _service_start(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        name = self._require_service_name(data)

        self._target.start_service(name)

        state = self._target.service_state(name)

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "service": name,
                "state": state.value,
            },
        )

    def _service_stop(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        name = self._require_service_name(data)

        self._target.stop_service(name)

        state = self._target.service_state(name)

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "service": name,
                "state": state.value,
            },
        )

    def _service_restart(
        self,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> ControlResult:
        name = self._require_service_name(data)

        self._target.restart_service(name)

        state = self._target.service_state(name)

        return ControlResult(
            success=True,
            command=str(command),
            data={
                "service": name,
                "state": state.value,
            },
        )

    @staticmethod
    def _require_service_name(data: Mapping[str, Any]) -> str:
        name = data.get("service")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Command requires a non-empty 'service' value.")

        return name