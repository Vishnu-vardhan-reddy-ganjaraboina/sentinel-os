from __future__ import annotations

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.policy import ControlPolicy


def test_read_commands_require_read_permission() -> None:
    read_commands = (
        KernelCommand.SYSTEM_STATUS,
        KernelCommand.SYSTEM_HEALTH,
        KernelCommand.SERVICE_LIST,
        KernelCommand.SERVICE_STATUS,
    )

    for command in read_commands:
        assert ControlPolicy.required_permission(command) is ControlPermission.READ


def test_service_control_commands_require_control_permission() -> None:
    control_commands = (
        KernelCommand.SERVICE_START,
        KernelCommand.SERVICE_STOP,
        KernelCommand.SERVICE_RESTART,
    )

    for command in control_commands:
        assert (
            ControlPolicy.required_permission(command)
            is ControlPermission.CONTROL
        )


def test_every_kernel_command_has_a_permission() -> None:
    for command in KernelCommand:
        permission = ControlPolicy.required_permission(command)

        assert isinstance(permission, ControlPermission)