"""
Tests for the console logging handler.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from io import StringIO

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.handlers.console import ConsoleHandler
from sentinel.logging.models import LogRecord


def make_record(message: str = "Hello Sentinel") -> LogRecord:
    return LogRecord(
        timestamp=datetime(
            2026,
            8,
            14,
            10,
            0,
            tzinfo=UTC,
        ),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message=message,
    )


def test_console_handler_writes_record() -> None:
    stream = StringIO()
    handler = ConsoleHandler(stream=stream)

    handler.emit(make_record())

    output = stream.getvalue()

    assert "INFO" in output
    assert "sentinel.test" in output
    assert "Hello Sentinel" in output


def test_console_handler_can_close() -> None:
    stream = StringIO()
    handler = ConsoleHandler(stream=stream)

    handler.close()

    with pytest.raises(RuntimeError, match="ConsoleHandler is closed"):
        handler.emit(make_record())


def test_console_handler_flushes_stream() -> None:
    class TrackingStream(StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.flush_count = 0

        def flush(self) -> None:
            self.flush_count += 1
            super().flush()

    stream = TrackingStream()
    handler = ConsoleHandler(stream=stream)

    handler.emit(make_record())

    assert stream.flush_count == 1


def test_console_handler_concurrent_emit_is_safe() -> None:
    stream = StringIO()
    handler = ConsoleHandler(stream=stream)

    records = [
        make_record(f"message-{index}")
        for index in range(100)
    ]

    barrier = threading.Barrier(len(records))

    def emit(record: LogRecord) -> None:
        barrier.wait()
        handler.emit(record)

    threads = [
        threading.Thread(target=emit, args=(record,))
        for record in records
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    output = stream.getvalue()

    assert output.count("INFO") == 100

    for index in range(100):
        assert f"message-{index}" in output


def test_console_handler_concurrent_emit_and_close_completes() -> None:
    stream = StringIO()
    handler = ConsoleHandler(stream=stream)

    errors: list[BaseException] = []

    def emit() -> None:
        try:
            handler.emit(make_record())
        except BaseException as exc:
            errors.append(exc)

    emit_thread = threading.Thread(target=emit)
    close_thread = threading.Thread(target=handler.close)

    emit_thread.start()
    close_thread.start()

    emit_thread.join(timeout=5)
    close_thread.join(timeout=5)

    assert not emit_thread.is_alive()
    assert not close_thread.is_alive()
    assert errors == []

    with pytest.raises(RuntimeError, match="ConsoleHandler is closed"):
        handler.emit(make_record())


def test_console_handler_close_waits_for_active_emit() -> None:
    emit_started = threading.Event()
    release_emit = threading.Event()
    close_completed = threading.Event()
    emit_errors: list[BaseException] = []
    close_errors: list[BaseException] = []

    class BlockingStream(StringIO):
        def write(self, value: str) -> int:
            emit_started.set()

            if not release_emit.wait(timeout=5):
                raise AssertionError(
                    "Blocking stream was not released"
                )

            return super().write(value)

    stream = BlockingStream()
    handler = ConsoleHandler(stream=stream)

    def emit() -> None:
        try:
            handler.emit(make_record())
        except BaseException as exc:
            emit_errors.append(exc)

    def close() -> None:
        try:
            handler.close()
        except BaseException as exc:
            close_errors.append(exc)
        finally:
            close_completed.set()

    emit_thread = threading.Thread(target=emit)
    close_thread = threading.Thread(target=close)

    try:
        emit_thread.start()

        assert emit_started.wait(timeout=5)

        close_thread.start()

        assert not close_completed.wait(timeout=0.1)

        release_emit.set()

        emit_thread.join(timeout=5)
        close_thread.join(timeout=5)

        assert not emit_thread.is_alive()
        assert not close_thread.is_alive()
        assert emit_errors == []
        assert close_errors == []
        assert close_completed.is_set()

        with pytest.raises(
            RuntimeError,
            match="ConsoleHandler is closed",
        ):
            handler.emit(make_record())
    finally:
        release_emit.set()

        emit_thread.join(timeout=5)
        close_thread.join(timeout=5)
