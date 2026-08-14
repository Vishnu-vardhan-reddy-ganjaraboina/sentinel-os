"""
File logging handler for Sentinel OS.
"""

from __future__ import annotations

from pathlib import Path

from sentinel.logging.constants import (
    DEFAULT_ENCODING,
    DEFAULT_LOG_DIRECTORY,
    DEFAULT_LOG_FILE,
)
from sentinel.logging.formatter import LogFormatter
from sentinel.logging.interfaces import LogHandler
from sentinel.logging.models import LogRecord


class FileHandler(LogHandler):
    """
    Write formatted log records to a file.
    """

    def __init__(
        self,
        *,
        formatter: LogFormatter | None = None,
        directory: str | Path = DEFAULT_LOG_DIRECTORY,
        filename: str = DEFAULT_LOG_FILE,
        encoding: str = DEFAULT_ENCODING,
    ) -> None:
        self._formatter = formatter or LogFormatter()
        self._directory = Path(directory)
        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._path = self._directory / filename
        self._encoding = encoding
        self._closed = False
        self._stream = self._path.open(
            mode="a",
            encoding=self._encoding,
        )

    @property
    def path(self) -> Path:
        """
        Return the path of the log file.
        """
        return self._path

    def emit(self, record: LogRecord) -> None:
        """
        Write a formatted record to the log file.
        """
        if self._closed:
            raise RuntimeError("FileHandler is closed")

        message = self._formatter.format(record)
        self._stream.write(f"{message}\n")
        self._stream.flush()

    def close(self) -> None:
        """
        Close the log file.
        """
        if not self._closed:
            self._stream.flush()
            self._stream.close()
            self._closed = True


__all__ = (
    "FileHandler",
)