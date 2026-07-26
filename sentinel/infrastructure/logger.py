"""
Logging infrastructure for Sentinel OS.

This module provides centralized logging configuration and access to
named loggers used throughout the Sentinel platform.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    *,
    level: int = logging.INFO,
    log_directory: str | Path = "logs",
    log_file: str = "sentinel.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Configure Sentinel logging.

    Safe to call multiple times.

    Args:
        level:
            Logging level.

        log_directory:
            Directory where log files are stored.

        log_file:
            Log file name.

        max_bytes:
            Maximum size of a log file before rotation.

        backup_count:
            Number of rotated log files to retain.
    """
    root_logger = logging.getLogger("sentinel")

    if root_logger.handlers:
        return

    root_logger.setLevel(level)

    log_directory = Path(log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_directory / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Return a named Sentinel logger.

    Args:
        name:
            Logger name.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(f"sentinel.{name}")