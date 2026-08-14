"""
Tests for the file logging handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.handlers.file import FileHandler
from sentinel.logging.models import LogRecord


def make_record() -> LogRecord:
    return LogRecord(
        timestamp=datetime(
            2026,
            8,
            14,
            10,
            0,
            tzinfo=UTC,
        ),
        level=LogLevel.INFO,
        logger="sentinel.test",
        message="Hello Sentinel",
    )


def test_file_handler_creates_directory_and_file(
    tmp_path: Path,
) -> None:
    log_directory = tmp_path / "logs"

    handler = FileHandler(
        directory=log_directory,
        filename="test.log",
    )

    try:
        assert log_directory.exists()
        assert handler.path.exists()
        assert handler.path.name == "test.log"
    finally:
        handler.close()


def test_file_handler_writes_record(
    tmp_path: Path,
) -> None:
    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    handler.emit(make_record())
    handler.close()

    content = handler.path.read_text(encoding="utf-8")

    assert "INFO" in content
    assert "sentinel.test" in content
    assert "Hello Sentinel" in content


def test_file_handler_appends(
    tmp_path: Path,
) -> None:
    first = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )
    first.emit(make_record())
    first.close()

    second = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )
    second.emit(
        LogRecord(
            timestamp=datetime.now(UTC),
            level=LogLevel.ERROR,
            logger="sentinel.test",
            message="Second message",
        ),
    )
    second.close()

    content = (tmp_path / "test.log").read_text(
        encoding="utf-8",
    )

    assert "Hello Sentinel" in content
    assert "Second message" in content


def test_file_handler_rejects_emit_after_close(
    tmp_path: Path,
) -> None:
    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    handler.close()

    with pytest.raises(RuntimeError, match="FileHandler is closed"):
        handler.emit(make_record())


def test_file_handler_close_is_idempotent(
    tmp_path: Path,
) -> None:
    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    handler.close()
    handler.close()