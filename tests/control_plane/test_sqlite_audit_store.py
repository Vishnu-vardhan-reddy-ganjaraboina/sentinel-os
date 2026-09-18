from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from sentinel.control_plane.audit import ControlAuditEvent
from sentinel.control_plane.sqlite_audit_store import (
    SQLiteControlAuditStore,
)

from sentinel.control_plane.audit_query import ControlAuditQuery


def make_event(
    *,
    caller_id: str = "user-1",
    command: str = "service.status",
    success: bool = True,
) -> ControlAuditEvent:
    return ControlAuditEvent(
        caller_id=caller_id,
        caller_type="user",
        command=command,
        success=success,
        timestamp=datetime.now(timezone.utc),
        data={"service": "memory"},
        error=None if success else "operation failed",
    )


def test_append_and_read_event(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    event = make_event()

    store.append(event)

    assert store.events() == (event,)

    store.close()


def test_events_preserve_insertion_order(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    first = make_event(caller_id="first")
    second = make_event(caller_id="second")

    store.append(first)
    store.append(second)

    assert store.events() == (first, second)

    store.close()


def test_failed_event_round_trip(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    event = make_event(success=False)

    store.append(event)

    restored = store.events()[0]

    assert restored.success is False
    assert restored.error == "operation failed"
    assert restored.data == {"service": "memory"}

    store.close()


def test_persistence_across_instances(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"

    first = SQLiteControlAuditStore(database)

    event = make_event()

    first.append(event)
    first.close()

    second = SQLiteControlAuditStore(database)

    assert second.events() == (event,)

    second.close()


def test_append_rejects_invalid_event(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    with pytest.raises(TypeError):
        store.append("invalid")  # type: ignore[arg-type]

    store.close()


def test_events_require_connection(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    store.close()

    with pytest.raises(RuntimeError):
        store.events()

def test_query_by_caller_id(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    first = make_event(caller_id="user-1")
    second = make_event(caller_id="user-2")

    store.append(first)
    store.append(second)

    result = store.query(
        ControlAuditQuery(caller_id="user-1")
    )

    assert result == (first,)

    store.close()


def test_query_by_command(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    first = make_event(command="service.status")
    second = make_event(command="service.start")

    store.append(first)
    store.append(second)

    result = store.query(
        ControlAuditQuery(command="service.start")
    )

    assert result == (second,)

    store.close()


def test_query_by_success(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    successful = make_event(success=True)
    failed = make_event(success=False)

    store.append(successful)
    store.append(failed)

    result = store.query(
        ControlAuditQuery(success=False)
    )

    assert result == (failed,)

    store.close()


def test_query_combines_filters(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    matching = make_event(
        caller_id="admin",
        command="service.stop",
        success=False,
    )

    other_caller = make_event(
        caller_id="user",
        command="service.stop",
        success=False,
    )

    other_command = make_event(
        caller_id="admin",
        command="service.start",
        success=False,
    )

    store.append(matching)
    store.append(other_caller)
    store.append(other_command)

    result = store.query(
        ControlAuditQuery(
            caller_id="admin",
            command="service.stop",
            success=False,
        )
    )

    assert result == (matching,)

    store.close()


def test_query_limit(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    first = make_event(caller_id="first")
    second = make_event(caller_id="second")
    third = make_event(caller_id="third")

    store.append(first)
    store.append(second)
    store.append(third)

    result = store.query(
        ControlAuditQuery(limit=2)
    )

    assert result == (first, second)

    store.close()


def test_query_time_range(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    first_timestamp = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    second_timestamp = first_timestamp + timedelta(hours=1)

    third_timestamp = first_timestamp + timedelta(hours=2)

    first = ControlAuditEvent(
        caller_id="user-1",
        caller_type="user",
        command="service.status",
        success=True,
        timestamp=first_timestamp,
    )

    second = ControlAuditEvent(
        caller_id="user-2",
        caller_type="user",
        command="service.status",
        success=True,
        timestamp=second_timestamp,
    )

    third = ControlAuditEvent(
        caller_id="user-3",
        caller_type="user",
        command="service.status",
        success=True,
        timestamp=third_timestamp,
    )

    store.append(first)
    store.append(second)
    store.append(third)

    result = store.query(
        ControlAuditQuery(
            since=second_timestamp,
            until=third_timestamp,
        )
    )

    assert result == (second, third)

    store.close()


def test_query_rejects_invalid_query(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(
        tmp_path / "audit.db"
    )

    with pytest.raises(TypeError):
        store.query("invalid")  # type: ignore[arg-type]

    store.close()