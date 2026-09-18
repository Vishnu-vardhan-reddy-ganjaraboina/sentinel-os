"""
Authorization policy for Sentinel Kernel Control Plane commands.
"""

from __future__ import annotations

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.permissions import ControlPermission


class ControlPolicy:
    """Map Kernel Control Plane commands to required permissions."""

    __slots__ = ()

    _COMMAND_PERMISSIONS = {
        KernelCommand.SYSTEM_STATUS: ControlPermission.READ,
        KernelCommand.SYSTEM_HEALTH: ControlPermission.READ,
        KernelCommand.SERVICE_LIST: ControlPermission.READ,
        KernelCommand.SERVICE_STATUS: ControlPermission.READ,
        KernelCommand.SERVICE_START: ControlPermission.CONTROL,
        KernelCommand.SERVICE_STOP: ControlPermission.CONTROL,
        KernelCommand.SERVICE_RESTART: ControlPermission.CONTROL,
    }

    @classmethod
    def required_permission(
        cls,
        command: KernelCommand,
    ) -> ControlPermission:
        """Return the permission required for a command."""
        return cls._COMMAND_PERMISSIONS[command]