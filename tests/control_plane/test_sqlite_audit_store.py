from datetime import datetime, timezone
from pathlib import Path

import pytest

from sentinel.control_plane.audit import ControlAuditEvent
from sentinel.control_plane.sqlite_audit_store import (
    SQLiteControlAuditStore,
)


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