from __future__ import annotations

import pytest

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest


def create_context() -> ControlContext:
    return ControlContext(
        caller_id="test-caller",
        caller_type="test",
    )


def test_control_request_stores_command_and_context() -> None:
    context = create_context()

    request = ControlRequest(
        command=KernelCommand.SYSTEM_STATUS,
        context=context,
    )

    assert request.command is KernelCommand.SYSTEM_STATUS
    assert request.context is context
    assert request.data == {}


def test_control_request_stores_data() -> None:
    request = ControlRequest(
        command=KernelCommand.SERVICE_START,
        context=create_context(),
        data={"service": "memory"},
    )

    assert request.data == {
        "service": "memory",
    }


def test_control_request_copies_data() -> None:
    data = {
        "service": "memory",
    }

    request = ControlRequest(
        command=KernelCommand.SERVICE_START,
        context=create_context(),
        data=data,
    )

    data["service"] = "changed"

    assert request.data == {
        "service": "memory",
    }


def test_control_request_is_immutable() -> None:
    request = ControlRequest(
        command=KernelCommand.SYSTEM_STATUS,
        context=create_context(),
    )

    with pytest.raises(AttributeError):
        request.command = KernelCommand.SYSTEM_HEALTH  # type: ignore[misc]