"""
Tests for logging constants.
"""

from __future__ import annotations

from pathlib import Path

from sentinel.logging.constants import (
    DEFAULT_BACKUP_COUNT,
    DEFAULT_CORRELATION_ID,
    DEFAULT_DATE_FORMAT,
    DEFAULT_ENCODING,
    DEFAULT_JSON_CONTEXT,
    DEFAULT_JSON_LEVEL,
    DEFAULT_JSON_LOGGER,
    DEFAULT_JSON_MESSAGE,
    DEFAULT_JSON_TIMESTAMP,
    DEFAULT_LOG_DIRECTORY,
    DEFAULT_LOG_FILE,
    DEFAULT_LOGGER_NAME,
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_MESSAGE_FORMAT,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_REQUEST_ID,
)


def test_logger_name() -> None:
    assert DEFAULT_LOGGER_NAME == "sentinel"


def test_log_directory() -> None:
    assert Path("logs") == DEFAULT_LOG_DIRECTORY


def test_log_file() -> None:
    assert DEFAULT_LOG_FILE == "sentinel.log"


def test_max_file_size() -> None:
    assert DEFAULT_MAX_FILE_SIZE == 10 * 1024 * 1024


def test_backup_count() -> None:
    assert DEFAULT_BACKUP_COUNT == 5


def test_queue_size() -> None:
    assert DEFAULT_QUEUE_SIZE == 1000


def test_encoding() -> None:
    assert DEFAULT_ENCODING == "utf-8"


def test_date_format() -> None:
    assert DEFAULT_DATE_FORMAT == "%Y-%m-%dT%H:%M:%S%z"


def test_message_format() -> None:
    assert DEFAULT_MESSAGE_FORMAT == (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )


def test_json_keys() -> None:
    assert DEFAULT_JSON_TIMESTAMP == "timestamp"
    assert DEFAULT_JSON_LEVEL == "level"
    assert DEFAULT_JSON_LOGGER == "logger"
    assert DEFAULT_JSON_MESSAGE == "message"
    assert DEFAULT_JSON_CONTEXT == "context"


def test_request_identifiers() -> None:
    assert DEFAULT_CORRELATION_ID == "correlation_id"
    assert DEFAULT_REQUEST_ID == "request_id"