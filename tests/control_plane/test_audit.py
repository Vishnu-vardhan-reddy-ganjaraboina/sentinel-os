from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sentinel.control_plane.audit import (
    ControlAuditEvent,
    InMemoryControlAuditRecorder,
)


def test_audit_event_defaults() -> None:
    event = ControlAuditEvent(
        caller_id="test-user",
        caller_type="user",
        command="service.status",
        success=True,
    )

    assert event.caller_id == "test-user"
    assert event.caller_type == "user"
    assert event.command == "service.status"
    assert event.success is True
    assert event.error is None
    assert event.data == {}
    assert event.timestamp.tzinfo is not None


def test_audit_event_accepts_data() -> None:
    event = ControlAuditEvent(
        caller_id="agent-1",
        caller_type="agent",
        command="service.restart",
        success=True,
        data={"service": "execution"},
    )

    assert event.data == {
        "service": "execution",
    }


def test_audit_event_data_is_isolated() -> None:
    data = {
        "service": "execution",
    }

    event = ControlAuditEvent(
        caller_id="agent-1",
        caller_type="agent",
        command="service.restart",
        success=True,
        data=data,
    )

    data["service"] = "memory"

    assert event.data["service"] == "execution"


@pytest.mark.parametrize(
    "field,value",
    [
        ("caller_id", ""),
        ("caller_id", "   "),
        ("caller_type", ""),
        ("caller_type", "   "),
        ("command", ""),
        ("command", "   "),
    ],
)
def test_audit_event_rejects_empty_required_fields(
    field: str,
    value: str,
) -> None:
    kwargs = {
        "caller_id": "caller",
        "caller_type": "user",
        "command": "service.status",
        "success": True,
        field: value,
    }

    with pytest.raises(ValueError):
        ControlAuditEvent(**kwargs)  # type: ignore[arg-type]


def test_audit_event_rejects_success_with_error() -> None:
    with pytest.raises(ValueError):
        ControlAuditEvent(
            caller_id="user",
            caller_type="user",
            command="service.status",
            success=True,
            error="unexpected",
        )


def test_audit_event_rejects_failure_without_error() -> None:
    with pytest.raises(ValueError):
        ControlAuditEvent(
            caller_id="user",
            caller_type="user",
            command="service.status",
            success=False,
        )


def test_audit_event_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValueError):
        ControlAuditEvent(
            caller_id="user",
            caller_type="user",
            command="service.status",
            success=True,
            timestamp=datetime.now(),
        )


def test_audit_event_accepts_timezone_aware_timestamp() -> None:
    timestamp = datetime.now(timezone.utc)

    event = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
        timestamp=timestamp,
    )

    assert event.timestamp == timestamp


def test_in_memory_recorder_stores_events() -> None:
    recorder = InMemoryControlAuditRecorder()

    event = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
    )

    recorder.record(event)

    assert recorder.events == (event,)


def test_in_memory_recorder_preserves_order() -> None:
    recorder = InMemoryControlAuditRecorder()

    first = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
    )

    second = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.health",
        success=True,
    )

    recorder.record(first)
    recorder.record(second)

    assert recorder.events == (
        first,
        second,
    )


def test_in_memory_recorder_rejects_invalid_event() -> None:
    recorder = InMemoryControlAuditRecorder()

    with pytest.raises(TypeError):
        recorder.record(object())  # type: ignore[arg-type]


def test_in_memory_recorder_clear() -> None:
    recorder = InMemoryControlAuditRecorder()

    recorder.record(
        ControlAuditEvent(
            caller_id="user",
            caller_type="user",
            command="service.status",
            success=True,
        )
    )

    recorder.clear()

    assert recorder.events == ()