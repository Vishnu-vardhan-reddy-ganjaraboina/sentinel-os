from __future__ import annotations

from typing import Any, Mapping

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.controller import KernelController



class ControlPlane:
    """
    Application-facing boundary for Sentinel OS control operations.

    Higher-level components such as the CLI, automation system,
    API layer, and future AI agents should communicate with the
    Kernel through this boundary rather than accessing the Kernel
    directly.
    """

    def __init__(
        self,
        controller: KernelController,
    ) -> None:
        self._controller = controller

    @property
    def controller(self) -> KernelController:
        """Return the underlying controller."""
        return self._controller

    @property
    def context(self) -> ControlContext:
        """Return the controller's configured control context."""
        return self._controller.context

    def execute(
        self,
        command: KernelCommand,
        data: Mapping[str, Any] | None = None,
    ) -> ControlResult:
        """
        Execute a Kernel control command.

        Authorization and audit recording remain owned by
        KernelController.
        """
        return self._controller.execute(
            command,
            data,
        )

    def execute_request(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        """
        Execute a complete structured Control Plane request.

        Authorization and audit recording remain owned by
        KernelController.
        """
        return self._controller.execute_request(request)