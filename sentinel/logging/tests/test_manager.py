"""
Tests for the Sentinel logging manager.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sentinel.logging.enums import LogLevel
from sentinel.logging.interfaces import LogHandler
from sentinel.logging.manager import LogManager
from sentinel.logging.models import LogRecord


class RecordingHandler(LogHandler):
    def __init__(self) -> None:
        self.records: list[LogRecord] = []
        self.closed = False

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)

    def close(self) -> None:
        self.closed = True


def make_record() -> LogRecord:
    return LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Test message",
    )


def test_manager_starts_empty() -> None:
    manager = LogManager()

    assert manager.handlers == ()


def test_manager_accepts_initial_handlers() -> None:
    handler = RecordingHandler()

    manager = LogManager([handler])

    assert manager.handlers == (handler,)


def test_add_handler() -> None:
    manager = LogManager()
    handler = RecordingHandler()

    manager.add_handler(handler)

    assert manager.handlers == (handler,)


def test_duplicate_handler_is_not_added() -> None:
    manager = LogManager()
    handler = RecordingHandler()

    manager.add_handler(handler)
    manager.add_handler(handler)

    assert manager.handlers == (handler,)


def test_remove_handler() -> None:
    handler = RecordingHandler()
    manager = LogManager([handler])

    manager.remove_handler(handler)

    assert manager.handlers == ()


def test_remove_missing_handler_is_safe() -> None:
    manager = LogManager()

    manager.remove_handler(RecordingHandler())

    assert manager.handlers == ()


def test_emit_sends_record_to_all_handlers() -> None:
    first = RecordingHandler()
    second = RecordingHandler()
    manager = LogManager([first, second])

    record = make_record()

    manager.emit(record)

    assert first.records == [record]
    assert second.records == [record]


def test_removed_handler_does_not_receive_records() -> None:
    first = RecordingHandler()
    second = RecordingHandler()
    manager = LogManager([first, second])

    manager.remove_handler(first)

    record = make_record()
    manager.emit(record)

    assert first.records == []
    assert second.records == [record]


def test_close_closes_all_handlers() -> None:
    first = RecordingHandler()
    second = RecordingHandler()
    manager = LogManager([first, second])

    manager.close()

    assert first.closed is True
    assert second.closed is True