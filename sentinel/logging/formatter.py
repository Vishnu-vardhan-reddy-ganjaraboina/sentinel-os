"""
Formatters for the Sentinel logging runtime.
"""

from __future__ import annotations

import json

from sentinel.logging.constants import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_MESSAGE_FORMAT,
)
from sentinel.logging.models import LogRecord


class LogFormatter:
    """
    Format Sentinel log records as text or JSON.
    """

    def __init__(
        self,
        *,
        date_format: str = DEFAULT_DATE_FORMAT,
        message_format: str = DEFAULT_MESSAGE_FORMAT,
    ) -> None:
        self._date_format = date_format
        self._message_format = message_format

    def format(self, record: LogRecord) -> str:
        """
        Format a log record as a human-readable string.
        """
        timestamp = record.timestamp.strftime(self._date_format)

        return self._message_format % {
            "asctime": timestamp,
            "levelname": record.level.name,
            "name": record.logger,
            "message": record.message,
        }

    def format_json(self, record: LogRecord) -> str:
        """
        Format a log record as a JSON object.
        """
        payload: dict[str, object] = {
            "timestamp": record.timestamp.isoformat(),
            "level": record.level.name,
            "logger": record.logger,
            "message": record.message,
            "context": dict(record.context),
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )


__all__ = (
    "LogFormatter",
)