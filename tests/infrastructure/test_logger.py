"""
Unit tests for Sentinel logging.
"""

from __future__ import annotations

import pytest
import logging
from pathlib import Path

from sentinel.infrastructure.logger import (
    configure_logging,
    get_logger,
    shutdown_logging,
)


def test_get_logger() -> None:
    logger = get_logger("kernel")

    assert logger.name == "sentinel.kernel"


def test_configure_logging(tmp_path: Path) -> None:
    configure_logging(
        log_directory=tmp_path,
    )

    logger = get_logger("test")

    logger.info("hello")

    shutdown_logging()

    assert (tmp_path / "sentinel.log").exists()


def test_multiple_configuration(tmp_path: Path) -> None:
    configure_logging(
        log_directory=tmp_path,
    )

    configure_logging(
        log_directory=tmp_path,
    )

    logger = logging.getLogger("sentinel")

    assert len(logger.handlers) == 2

    shutdown_logging()


def test_shutdown_logging(tmp_path: Path) -> None:
    configure_logging(
        log_directory=tmp_path,
    )

    shutdown_logging()

    logger = logging.getLogger("sentinel")

    assert logger.handlers == []

def test_invalid_log_level(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid logging level"):
        configure_logging(
            log_directory=tmp_path,
            log_level="NOT_A_LEVEL",
        )


def test_invalid_log_size(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        configure_logging(
            log_directory=tmp_path,
            max_bytes=0,
        )

    with pytest.raises(ValueError):
        configure_logging(
            log_directory=tmp_path,
            backup_count=-1,
        )


def test_get_logger_rejects_invalid_name() -> None:
    with pytest.raises(TypeError):
        get_logger(123)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        get_logger("   ")


def test_shutdown_is_idempotent(tmp_path: Path) -> None:
    configure_logging(log_directory=tmp_path)

    shutdown_logging()
    shutdown_logging()

    assert logging.getLogger("sentinel").handlers == []