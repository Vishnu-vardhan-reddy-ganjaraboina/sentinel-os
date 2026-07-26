"""
Unit tests for Sentinel logging.
"""

from __future__ import annotations

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