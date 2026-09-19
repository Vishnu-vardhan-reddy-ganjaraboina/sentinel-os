from __future__ import annotations

import pytest

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
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

def test_request_rejects_invalid_command() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type="system",
    )

    with pytest.raises(TypeError):
        ControlRequest(
            command="service.list",  # type: ignore[arg-type]
            context=context,
        )

def test_request_rejects_invalid_context() -> None:
    with pytest.raises(TypeError):
        ControlRequest(
            command=KernelCommand.SERVICE_LIST,
            context=object(),  # type: ignore[arg-type]
        )

def test_request_copies_data() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type="system",
    )

    data = {
        "name": "memory",
    }

    request = ControlRequest(
        command=KernelCommand.SERVICE_STATUS,
        context=context,
        data=data,
    )

    data["name"] = "knowledge"

    assert request.data["name"] == "memory"

def test_request_data_is_independently_copied() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type="system",
    )

    request = ControlRequest(
        command=KernelCommand.SERVICE_LIST,
        context=context,
        data={"value": 1},
    )

    assert request.data == {"value": 1}