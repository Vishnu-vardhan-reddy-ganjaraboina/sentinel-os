"""
Console logging handler for Sentinel OS.
"""

from __future__ import annotations

import sys
from typing import TextIO

from sentinel.logging.formatter import LogFormatter
from sentinel.logging.interfaces import LogHandler
from sentinel.logging.models import LogRecord


class ConsoleHandler(LogHandler):
    """
    Write formatted log records to a text stream.
    """

    def __init__(
        self,
        *,
        formatter: LogFormatter | None = None,
        stream: TextIO | None = None,
    ) -> None:
        self._formatter = formatter or LogFormatter()
        self._stream = stream or sys.stdout
        self._closed = False

    def emit(self, record: LogRecord) -> None:
        """
        Write a formatted record to the configured stream.
        """
        if self._closed:
            raise RuntimeError("ConsoleHandler is closed")

        message = self._formatter.format(record)
        self._stream.write(f"{message}\n")
        self._stream.flush()

    def close(self) -> None:
        """
        Mark the handler as closed.
        """
        self._closed = True


__all__ = (
    "ConsoleHandler",
)