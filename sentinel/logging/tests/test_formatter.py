"""
Tests for logging formatters.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sentinel.logging.enums import LogLevel
from sentinel.logging.formatter import LogFormatter
from sentinel.logging.models import LogContext, LogRecord


def make_record() -> LogRecord:
    return LogRecord(
        timestamp=datetime(
            2026,
            8,
            13,
            13,
            0,
            0,
            tzinfo=UTC,
        ),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Test message",
        context=LogContext.from_mapping(
            {
                "request_id": "abc123",
            },
        ),
    )


def test_format() -> None:
    formatter = LogFormatter()

    result = formatter.format(make_record())

    assert "2026-08-13T13:00:00+0000" in result
    assert "INFO" in result
    assert "sentinel.test" in result
    assert "Test message" in result


def test_format_json() -> None:
    formatter = LogFormatter()

    result = formatter.format_json(make_record())
    payload = json.loads(result)

    assert payload["timestamp"] == "2026-08-13T13:00:00+00:00"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "sentinel.test"
    assert payload["message"] == "Test message"
    assert payload["context"] == {
        "request_id": "abc123",
    }


def test_custom_message_format() -> None:
    formatter = LogFormatter(
        message_format="%(levelname)s: %(message)s",
    )

    result = formatter.format(make_record())

    assert result == "INFO: Test message"