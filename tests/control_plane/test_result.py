from __future__ import annotations

from sentinel.control_plane.result import ControlResult


def test_control_result_defaults() -> None:
    result = ControlResult(
        success=True,
        command="system.status",
    )

    assert result.success is True
    assert result.command == "system.status"
    assert result.data == {}
    assert result.error is None


def test_control_result_contains_data() -> None:
    result = ControlResult(
        success=True,
        command="service.status",
        data={
            "service": "memory",
            "state": "running",
        },
    )

    assert result.data == {
        "service": "memory",
        "state": "running",
    }


def test_control_result_can_contain_error() -> None:
    result = ControlResult(
        success=False,
        command="service.stop",
        error="Service is not running.",
    )

    assert result.success is False
    assert result.error == "Service is not running."


def test_control_result_is_immutable() -> None:
    result = ControlResult(
        success=True,
        command="system.status",
    )

    try:
        result.success = False  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("ControlResult should be immutable.")