"""
Constants for the Sentinel logging runtime.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_LOGGER_NAME = "sentinel"

DEFAULT_LOG_DIRECTORY = Path("logs")

DEFAULT_LOG_FILE = "sentinel.log"

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024

DEFAULT_BACKUP_COUNT = 5

DEFAULT_QUEUE_SIZE = 1000

DEFAULT_ENCODING = "utf-8"

DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

DEFAULT_MESSAGE_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

DEFAULT_JSON_TIMESTAMP = "timestamp"

DEFAULT_JSON_LEVEL = "level"

DEFAULT_JSON_LOGGER = "logger"

DEFAULT_JSON_MESSAGE = "message"

DEFAULT_JSON_CONTEXT = "context"

DEFAULT_CORRELATION_ID = "correlation_id"

DEFAULT_REQUEST_ID = "request_id"


__all__ = (
    "DEFAULT_BACKUP_COUNT",
    "DEFAULT_CORRELATION_ID",
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_ENCODING",
    "DEFAULT_JSON_CONTEXT",
    "DEFAULT_JSON_LEVEL",
    "DEFAULT_JSON_LOGGER",
    "DEFAULT_JSON_MESSAGE",
    "DEFAULT_JSON_TIMESTAMP",
    "DEFAULT_LOG_DIRECTORY",
    "DEFAULT_LOG_FILE",
    "DEFAULT_LOGGER_NAME",
    "DEFAULT_MAX_FILE_SIZE",
    "DEFAULT_MESSAGE_FORMAT",
    "DEFAULT_QUEUE_SIZE",
    "DEFAULT_REQUEST_ID",
)