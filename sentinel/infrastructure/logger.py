"""
Logging infrastructure for Sentinel OS.

This module provides a shared application logger built on top of
Python's standard logging library.
"""

from __future__ import annotations

import logging
from pathlib import Path


class Logger:
    """Configure and expose the Sentinel logger."""

    LOGGER_NAME = "sentinel"

    def __init__(
        self,
        level: int = logging.INFO,
        log_directory: str = "logs",
        log_file: str = "sentinel.log",
    ) -> None:
        self._logger = logging.getLogger(self.LOGGER_NAME)

        # Prevent duplicate handlers
        if self._logger.handlers:
            return

        self._logger.setLevel(level)

        Path(log_directory).mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(
            Path(log_directory) / log_file,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

        self._logger.propagate = False

    @property
    def instance(self) -> logging.Logger:
        """Return the configured logger."""
        return self._logger


logger = Logger().instance