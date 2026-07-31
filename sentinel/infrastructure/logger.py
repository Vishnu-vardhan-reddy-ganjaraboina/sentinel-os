"""
Centralized logging configuration for Sentinel OS.

This module configures the Sentinel logging system and provides
named loggers for every subsystem.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sentinel.infrastructure.constants import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_DIRECTORY,
    DEFAULT_LOG_ENCODING,
    DEFAULT_LOG_FILE,
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MAX_BYTES,
)


def configure_logging(
    *,
    log_level: str = DEFAULT_LOG_LEVEL,
    log_directory: str | Path = DEFAULT_LOG_DIRECTORY,
    log_file: str = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_LOG_MAX_BYTES,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
) -> None:
    """
    Configure Sentinel logging.

    This function should be called once during application startup.
    Subsequent calls have no effect.

    Args:
        log_level:
            Logging level.

        log_directory:
            Directory used for log files.

        log_file:
            Log filename.

        max_bytes:
            Maximum size of each log file before rotation.

        backup_count:
            Number of rotated log files to retain.
    """

    root_logger = logging.getLogger("sentinel")

    if root_logger.handlers:
        return

    root_logger.setLevel(getattr(logging, log_level.upper()))

    log_directory = Path(log_directory)

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_path = log_directory / log_file

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=DEFAULT_LOG_ENCODING,
    )

    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger.propagate = False

    root_logger.info("Sentinel logging initialized.")


def get_logger(name: str) -> logging.Logger:
    """
    Return a Sentinel logger.

    Args:
        name:
            Logger name.

    Returns:
        A configured Sentinel logger.
    """
    return logging.getLogger(f"sentinel.{name}")


def shutdown_logging() -> None:
    """
    Shutdown the Sentinel logging system.
    """
    root_logger = logging.getLogger("sentinel")

    handlers = root_logger.handlers[:]

    for handler in handlers:
        handler.flush()
        handler.close()
        root_logger.removeHandler(handler)

    logging.shutdown()