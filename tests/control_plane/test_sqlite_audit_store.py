import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sentinel.control_plane.audit import ControlAuditEvent
from sentinel.control_plane.audit_query import ControlAuditQuery
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
        timestamp=datetime.now(UTC),
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
        tzinfo=UTC,
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
def test_concurrent_appends_are_serialized(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = SQLiteControlAuditStore(tmp_path / "audit.db")

    event_count = 100

    def append_event(index: int) -> None:
        store.append(
            make_event(
                caller_id=f"user-{index}",
                command=f"service.status.{index}",
            )
        )

    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(append_event, range(event_count)))

        events = store.events()

        assert len(events) == event_count
        assert {
            event.caller_id
            for event in events
        } == {
            f"user-{index}"
            for index in range(event_count)
        }
    finally:
        store.close()


def test_concurrent_append_and_query_are_safe(
    tmp_path: Path,
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = SQLiteControlAuditStore(tmp_path / "audit.db")

    event_count = 100

    def append_event(index: int) -> None:
        store.append(
            make_event(
                caller_id=f"user-{index}",
                command="service.status",
            )
        )

    def query_events(_: int) -> tuple[ControlAuditEvent, ...]:
        return store.query(
            ControlAuditQuery(command="service.status")
        )

    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            append_futures = [
                executor.submit(append_event, index)
                for index in range(event_count)
            ]

            query_futures = [
                executor.submit(query_events, index)
                for index in range(event_count)
            ]

            for future in append_futures:
                future.result()

            for future in query_futures:
                future.result()

        assert len(store.events()) == event_count
    finally:
        store.close()


def test_close_is_idempotent(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(tmp_path / "audit.db")

    store.close()
    store.close()
    store.disconnect()
    store.disconnect()

    with pytest.raises(RuntimeError):
        store.events()


def test_reconnect_preserves_persisted_events(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    store = SQLiteControlAuditStore(database)

    event = make_event()

    store.append(event)
    store.close()

    store.connect()

    try:
        assert store.events() == (event,)
    finally:
        store.close()


def test_multiple_store_instances_can_persist(
    tmp_path: Path,
) -> None:
    database = tmp_path / "audit.db"

    first = SQLiteControlAuditStore(database)
    second = SQLiteControlAuditStore(database)

    first_event = make_event(caller_id="first")
    second_event = make_event(caller_id="second")

    try:
        first.append(first_event)
        second.append(second_event)

        assert first.events() == (
            first_event,
            second_event,
        )

        assert second.events() == (
            first_event,
            second_event,
        )
    finally:
        first.close()
        second.close()

def test_append_sql_failure_rolls_back_transaction(
    tmp_path: Path,
) -> None:
    store = SQLiteControlAuditStore(tmp_path / "audit.db")

    event = make_event(caller_id="recovered")

    try:
        with pytest.raises(sqlite3.IntegrityError):
            store._connection.execute(  # type: ignore[union-attr]
                """
                INSERT INTO control_audit_events (
                    timestamp,
                    caller_id,
                    caller_type,
                    command,
                    success,
                    data,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    "invalid",
                    "user",
                    "service.status",
                    1,
                    "{}",
                    None,
                ),
            )

        store._connection.rollback()  # type: ignore[union-attr]

        store.append(event)

        assert store.events() == (event,)
    finally:
        store.close()


def test_nested_audit_data_round_trips_through_sqlite(
    tmp_path: Path,
) -> None:
    store = SQLiteControlAuditStore(tmp_path / "nested-audit.db")
    event = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
        data={
            "metadata": {"role": "user"},
            "tags": ["safe", "verified"],
        },
    )

    store.append(event)
    restored = store.events()[0]

    assert restored.data["metadata"]["role"] == "user"
    assert restored.data["tags"] == ("safe", "verified")
    store.close()


def test_append_rejects_non_json_audit_data(tmp_path: Path) -> None:
    store = SQLiteControlAuditStore(tmp_path / "invalid-audit.db")
    event = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
        data={"invalid": object()},
    )

    with pytest.raises(TypeError):
        store.append(event)

    store.close()


def test_append_rejects_non_string_audit_data_keys(
    tmp_path: Path,
) -> None:
    store = SQLiteControlAuditStore(tmp_path / "invalid-key-audit.db")
    event = ControlAuditEvent(
        caller_id="user",
        caller_type="user",
        command="service.status",
        success=True,
        data={1: "value"},
    )

    with pytest.raises(TypeError):
        store.append(event)

    store.close()
