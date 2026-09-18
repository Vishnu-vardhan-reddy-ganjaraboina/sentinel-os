from __future__ import annotations

from sentinel.control_plane.commands import KernelCommand


def test_kernel_commands_are_string_enums() -> None:
    assert KernelCommand.SYSTEM_STATUS.value == "system.status"
    assert KernelCommand.SYSTEM_HEALTH.value == "system.health"


def test_service_commands_have_expected_values() -> None:
    assert KernelCommand.SERVICE_LIST.value == "service.list"
    assert KernelCommand.SERVICE_STATUS.value == "service.status"
    assert KernelCommand.SERVICE_START.value == "service.start"
    assert KernelCommand.SERVICE_STOP.value == "service.stop"
    assert KernelCommand.SERVICE_RESTART.value == "service.restart"


def test_kernel_command_order_is_stable() -> None:
    assert list(KernelCommand) == [
        KernelCommand.SYSTEM_STATUS,
        KernelCommand.SYSTEM_HEALTH,
        KernelCommand.SERVICE_LIST,
        KernelCommand.SERVICE_STATUS,
        KernelCommand.SERVICE_START,
        KernelCommand.SERVICE_STOP,
        KernelCommand.SERVICE_RESTART,
    ]