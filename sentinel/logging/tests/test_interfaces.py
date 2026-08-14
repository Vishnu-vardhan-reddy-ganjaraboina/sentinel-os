"""
Tests for logging interfaces.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.interfaces import LogHandler
from sentinel.logging.models import LogRecord


def make_record() -> LogRecord:
    return LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Test message",
    )


def test_log_handler_is_abstract() -> None:
    with pytest.raises(TypeError):
        LogHandler()  # type: ignore[abstract]


def test_log_handler_requires_emit_and_close() -> None:
    assert hasattr(LogHandler, "emit")
    assert hasattr(LogHandler, "close")


def test_concrete_handler_can_implement_interface() -> None:
    class TestHandler(LogHandler):
        def __init__(self) -> None:
            self.records: list[LogRecord] = []
            self.closed = False

        def emit(self, record: LogRecord) -> None:
            self.records.append(record)

        def close(self) -> None:
            self.closed = True

    handler = TestHandler()
    record = make_record()

    handler.emit(record)
    handler.close()

    assert handler.records == [record]
    assert handler.closed is True