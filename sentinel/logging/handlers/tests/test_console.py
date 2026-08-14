"""
Tests for the console logging handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.handlers.console import ConsoleHandler
from sentinel.logging.models import LogRecord


def make_record() -> LogRecord:
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
        message="Hello Sentinel",
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