"""
Tests for logging data models.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.models import (
    LogContext,
    LogMetadata,
    LogRecord,
)


def test_empty_context() -> None:
    context = LogContext.empty()

    assert len(context) == 0
    assert dict(context) == {}


def test_context_from_mapping() -> None:
    context = LogContext.from_mapping(
        {
            "request_id": "abc123",
            "user_id": 42,
        },
    )

    assert context["request_id"] == "abc123"
    assert context["user_id"] == 42
    assert len(context) == 2


def test_context_is_immutable() -> None:
    context = LogContext.from_mapping(
        {
            "request_id": "abc123",
        },
    )

    with pytest.raises(TypeError):
        context["request_id"] = "changed"  # type: ignore[index]


def test_context_does_not_share_input_mapping() -> None:
    values = {
        "request_id": "abc123",
    }

    context = LogContext.from_mapping(values)

    values["request_id"] = "changed"

    assert context["request_id"] == "abc123"


def test_context_repr() -> None:
    context = LogContext.from_mapping(
        {
            "request_id": "abc123",
        },
    )

    assert repr(context) == "LogContext({'request_id': 'abc123'})"

def test_default_log_metadata() -> None:
    metadata = LogMetadata()

    assert metadata.process_id == 0
    assert metadata.thread_id == 0
    assert metadata.module == ""
    assert metadata.function == ""
    assert metadata.line_number == 0


def test_log_metadata() -> None:
    metadata = LogMetadata(
        process_id=100,
        thread_id=200,
        module="database",
        function="connect",
        line_number=42,
    )

    assert metadata.process_id == 100
    assert metadata.thread_id == 200
    assert metadata.module == "database"
    assert metadata.function == "connect"
    assert metadata.line_number == 42


def test_log_metadata_is_immutable() -> None:
    metadata = LogMetadata(
        process_id=100,
    )

    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        metadata.process_id = 200  # type: ignore[misc]

def test_log_record() -> None:
    timestamp = datetime(
        2026,
        8,
        13,
        12,
        0,
        tzinfo=UTC,
    )

    record = LogRecord(
        timestamp=timestamp,
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Test message",
    )

    assert record.timestamp == timestamp
    assert record.level is LogLevel.INFO
    assert record.logger == "sentinel.test"
    assert record.message == "Test message"


def test_log_record_default_context() -> None:
    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.DEBUG,
        logger="sentinel.test",
        message="Debug message",
    )

    assert len(record.context) == 0


def test_log_record_default_metadata() -> None:
    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Test message",
    )

    assert record.metadata.process_id == 0
    assert record.metadata.thread_id == 0
    assert record.metadata.module == ""
    assert record.metadata.function == ""
    assert record.metadata.line_number == 0


def test_log_record_with_context() -> None:
    context = LogContext.from_mapping(
        {
            "user_id": 42,
            "request_id": "abc123",
        },
    )

    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.auth",
        message="User authenticated",
        context=context,
    )

    assert record.context["user_id"] == 42
    assert record.context["request_id"] == "abc123"


def test_log_record_with_metadata() -> None:
    metadata = LogMetadata(
        process_id=100,
        thread_id=200,
        module="database",
        function="connect",
        line_number=50,
    )

    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=LogLevel.INFO,
        logger="sentinel.database",
        message="Database connected",
        metadata=metadata,
    )

    assert record.metadata.process_id == 100
    assert record.metadata.thread_id == 200
    assert record.metadata.module == "database"
    assert record.metadata.function == "connect"
    assert record.metadata.line_number == 50