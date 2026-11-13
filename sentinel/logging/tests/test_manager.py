"""
Tests for the Sentinel logging manager.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime

import pytest

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


class FailingHandler(LogHandler):
    def __init__(self, error: BaseException) -> None:
        self.error = error
        self.attempts = 0
        self.closed = False

    def emit(self, record: LogRecord) -> None:
        self.attempts += 1
        raise self.error

    def close(self) -> None:
        self.closed = True


class BlockingHandler(LogHandler):
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.records: list[LogRecord] = []
        self.closed = False

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)
        self.started.set()

        if not self.release.wait(timeout=5):
            raise AssertionError("BlockingHandler was not released")

    def close(self) -> None:
        self.closed = True


def make_record(message: str = "Test message") -> LogRecord:
    return LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message=message,
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


def test_concurrent_add_handler_is_safe() -> None:
    manager = LogManager()
    handlers = [RecordingHandler() for _ in range(50)]

    barrier = threading.Barrier(len(handlers))

    def add(handler: RecordingHandler) -> None:
        barrier.wait()
        manager.add_handler(handler)

    threads = [
        threading.Thread(target=add, args=(handler,))
        for handler in handlers
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(manager.handlers) == len(handlers)
    assert set(id(handler) for handler in manager.handlers) == {
        id(handler) for handler in handlers
    }


def test_concurrent_emit_is_safe() -> None:
    handler = RecordingHandler()
    manager = LogManager([handler])

    records = [make_record(f"message-{index}") for index in range(100)]

    barrier = threading.Barrier(len(records))

    def emit(record: LogRecord) -> None:
        barrier.wait()
        manager.emit(record)

    threads = [
        threading.Thread(target=emit, args=(record,))
        for record in records
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(handler.records) == len(records)
    assert {
        record.message for record in handler.records
    } == {
        record.message for record in records
    }


def test_concurrent_add_and_remove_is_safe() -> None:
    manager = LogManager()
    handlers = [RecordingHandler() for _ in range(50)]

    for handler in handlers:
        manager.add_handler(handler)

    barrier = threading.Barrier(len(handlers) * 2)

    def add(handler: RecordingHandler) -> None:
        barrier.wait()
        manager.add_handler(handler)

    def remove(handler: RecordingHandler) -> None:
        barrier.wait()
        manager.remove_handler(handler)

    threads = [
        threading.Thread(target=add, args=(handler,))
        for handler in handlers
    ]

    threads.extend(
        threading.Thread(target=remove, args=(handler,))
        for handler in handlers
    )

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    remaining = manager.handlers

    assert len(remaining) == len(set(id(handler) for handler in remaining))
    assert all(handler in handlers for handler in remaining)


def test_emit_does_not_hold_manager_lock_during_handler_execution() -> None:
    manager = LogManager()
    handler = BlockingHandler()
    manager.add_handler(handler)

    emit_thread = threading.Thread(
        target=manager.emit,
        args=(make_record(),),
    )

    emit_thread.start()

    assert handler.started.wait(timeout=5)

    replacement = RecordingHandler()

    start = time.monotonic()
    manager.add_handler(replacement)
    elapsed = time.monotonic() - start

    assert elapsed < 1.0
    assert replacement in manager.handlers

    handler.release.set()
    emit_thread.join(timeout=5)

    assert not emit_thread.is_alive()
    assert len(handler.records) == 1


def test_emit_attempts_all_handlers_when_one_fails() -> None:
    first_error = RuntimeError("first handler failed")
    failing = FailingHandler(first_error)
    successful = RecordingHandler()

    manager = LogManager([failing, successful])
    record = make_record()

    with pytest.raises(RuntimeError, match="first handler failed"):
        manager.emit(record)

    assert failing.attempts == 1
    assert successful.records == [record]


def test_emit_raises_exception_group_when_multiple_handlers_fail() -> None:
    first_error = RuntimeError("first handler failed")
    second_error = ValueError("second handler failed")

    first = FailingHandler(first_error)
    second = FailingHandler(second_error)

    manager = LogManager([first, second])

    with pytest.raises(ExceptionGroup) as exc_info:
        manager.emit(make_record())

    errors = exc_info.value.exceptions

    assert errors == (first_error, second_error)
    assert first.attempts == 1
    assert second.attempts == 1


def test_emit_preserves_successful_handlers_when_multiple_handlers_fail() -> None:
    first_error = RuntimeError("first handler failed")
    third_error = OSError("third handler failed")

    first = FailingHandler(first_error)
    second = RecordingHandler()
    third = FailingHandler(third_error)

    manager = LogManager([first, second, third])
    record = make_record()

    with pytest.raises(ExceptionGroup):
        manager.emit(record)

    assert first.attempts == 1
    assert second.records == [record]
    assert third.attempts == 1


def test_emit_groups_base_exceptions_without_masking_them() -> None:
    first_error = KeyboardInterrupt("first handler interrupted")
    second_error = SystemExit("second handler exited")

    first = FailingHandler(first_error)
    second = FailingHandler(second_error)
    manager = LogManager([first, second])

    with pytest.raises(BaseExceptionGroup) as exc_info:
        manager.emit(make_record())

    assert exc_info.value.exceptions == (first_error, second_error)
    assert first.attempts == 1
    assert second.attempts == 1
