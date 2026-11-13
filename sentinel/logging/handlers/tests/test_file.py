"""
Tests for the file logging handler.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast

import pytest

from sentinel.logging.enums import LogLevel
from sentinel.logging.handlers.file import FileHandler
from sentinel.logging.models import LogRecord


def make_record(message: str = "Hello Sentinel") -> LogRecord:
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
        message=message,
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


def test_file_handler_concurrent_emit_is_safe(
    tmp_path: Path,
) -> None:
    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    try:
        records = [
            make_record(f"message-{index}")
            for index in range(100)
        ]

        barrier = threading.Barrier(len(records))

        def emit(record: LogRecord) -> None:
            barrier.wait()
            handler.emit(record)

        threads = [
            threading.Thread(
                target=emit,
                args=(record,),
            )
            for record in records
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        content = handler.path.read_text(
            encoding="utf-8",
        )

        assert content.count("INFO") == 100

        for index in range(100):
            assert f"message-{index}" in content
    finally:
        handler.close()


def test_file_handler_concurrent_emit_and_close_completes(
    tmp_path: Path,
) -> None:
    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    errors: list[BaseException] = []

    def emit() -> None:
        try:
            handler.emit(make_record())
        except BaseException as exc:
            errors.append(exc)

    emit_thread = threading.Thread(target=emit)
    close_thread = threading.Thread(target=handler.close)

    emit_thread.start()
    close_thread.start()

    emit_thread.join(timeout=5)
    close_thread.join(timeout=5)

    assert not emit_thread.is_alive()
    assert not close_thread.is_alive()
    assert errors == []

    with pytest.raises(RuntimeError, match="FileHandler is closed"):
        handler.emit(make_record())


def test_file_handler_close_waits_for_active_emit(
    tmp_path: Path,
) -> None:
    emit_started = threading.Event()
    release_emit = threading.Event()
    close_completed = threading.Event()
    emit_errors: list[BaseException] = []
    close_errors: list[BaseException] = []

    class BlockingStream:
        def __init__(self, stream: TextIO) -> None:
            self._stream = stream

        def write(self, value: str) -> int:
            emit_started.set()

            if not release_emit.wait(timeout=5):
                raise AssertionError(
                    "Blocking file stream was not released"
                )

            return self._stream.write(value)

        def flush(self) -> None:
            self._stream.flush()

        def close(self) -> None:
            self._stream.close()

    handler = FileHandler(
        directory=tmp_path,
        filename="test.log",
    )

    original_stream = handler._stream  # noqa: SLF001
    cast(Any, handler)._stream = BlockingStream(original_stream)  # noqa: SLF001

    def emit() -> None:
        try:
            handler.emit(make_record())
        except BaseException as exc:
            emit_errors.append(exc)

    def close() -> None:
        try:
            handler.close()
        except BaseException as exc:
            close_errors.append(exc)
        finally:
            close_completed.set()

    emit_thread = threading.Thread(target=emit)
    close_thread = threading.Thread(target=close)

    try:
        emit_thread.start()

        assert emit_started.wait(timeout=5)

        close_thread.start()

        assert not close_completed.wait(timeout=0.1)

        release_emit.set()

        emit_thread.join(timeout=5)
        close_thread.join(timeout=5)

        assert not emit_thread.is_alive()
        assert not close_thread.is_alive()
        assert emit_errors == []
        assert close_errors == []
        assert close_completed.is_set()

        with pytest.raises(
            RuntimeError,
            match="FileHandler is closed",
        ):
            handler.emit(make_record())
    finally:
        release_emit.set()

        emit_thread.join(timeout=5)
        close_thread.join(timeout=5)

        if emit_thread.is_alive() or close_thread.is_alive():
            raise AssertionError(
                "Handler concurrency test threads did not finish"
            )
