"""
Tests for the public logging API.
"""

from __future__ import annotations

from sentinel.logging import (
    ConsoleHandler,
    FileHandler,
    LogContext,
    LogFormatter,
    LogHandler,
    LogLevel,
    LogManager,
    LogMetadata,
    LogRecord,
)


def test_public_logging_exports() -> None:
    assert ConsoleHandler is not None
    assert FileHandler is not None
    assert LogContext is not None
    assert LogFormatter is not None
    assert LogHandler is not None
    assert LogLevel is not None
    assert LogManager is not None
    assert LogMetadata is not None
    assert LogRecord is not None