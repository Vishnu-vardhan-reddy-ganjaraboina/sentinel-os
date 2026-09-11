"""
Centralized logging configuration for Sentinel OS.

This module configures the Sentinel logging system and provides
named loggers for every subsystem.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import RLock

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


_CONFIG_LOCK = RLock()


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

    Subsequent calls have no effect while Sentinel handlers are
    already installed.
    """
    if not isinstance(log_level, str):
        raise TypeError("log_level must be a string")

    if not log_level.strip():
        raise ValueError("log_level cannot be empty")

    if not isinstance(log_directory, (str, Path)):
        raise TypeError("log_directory must be a string or path")

    if not isinstance(log_file, str):
        raise TypeError("log_file must be a string")

    if not log_file.strip():
        raise ValueError("log_file cannot be empty")

    if not isinstance(max_bytes, int):
        raise TypeError("max_bytes must be an integer")

    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")

    if not isinstance(backup_count, int):
        raise TypeError("backup_count must be an integer")

    if backup_count < 0:
        raise ValueError("backup_count cannot be negative")

    level_name = log_level.strip().upper()
    level = getattr(logging, level_name, None)

    if not isinstance(level, int):
        raise ValueError(
            f"Invalid logging level: '{log_level}'"
        )

    with _CONFIG_LOCK:
        root_logger = logging.getLogger("sentinel")

        if root_logger.handlers:
            return

        directory = Path(log_directory)
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        log_path = directory / log_file

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

        root_logger.setLevel(level)
        root_logger.propagate = False

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        root_logger.info("Sentinel logging initialized.")


def get_logger(name: str) -> logging.Logger:
    """
    Return a Sentinel logger.

    Args:
        name:
            Logger name.

    Returns:
        A configured Sentinel logger.

    Raises:
        TypeError:
            If name is not a string.

        ValueError:
            If name is empty.
    """
    if not isinstance(name, str):
        raise TypeError("logger name must be a string")

    if not name.strip():
        raise ValueError("logger name cannot be empty")

    return logging.getLogger(f"sentinel.{name}")


def shutdown_logging() -> None:
    """
    Shutdown the Sentinel logging system safely.

    The operation is idempotent.
    """
    with _CONFIG_LOCK:
        root_logger = logging.getLogger("sentinel")

        handlers = root_logger.handlers[:]

        for handler in handlers:
            handler.flush()
            handler.close()
            root_logger.removeHandler(handler)

        root_logger.propagate = False

    logging.shutdown()
