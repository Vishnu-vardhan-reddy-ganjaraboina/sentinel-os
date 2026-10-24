from __future__ import annotations

import sqlite3

import pytest

from sentinel.storage.backends.in_memory import MemoryBackend
from sentinel.storage.backends.sqlite import SQLiteBackend
from sentinel.storage.exceptions import StorageWriteError


class _ConnectionProxy:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        fail_commit: bool = False,
        fail_rollback: bool = False,
    ) -> None:
        self._connection = connection
        self._fail_commit = fail_commit
        self._fail_rollback = fail_rollback

    def commit(self) -> None:
        if self._fail_commit:
            raise sqlite3.OperationalError(
                "simulated commit failure"
            )

        self._connection.commit()

    def rollback(self) -> None:
        if self._fail_rollback:
            raise sqlite3.OperationalError(
                "simulated rollback failure"
            )

        self._connection.rollback()

    def __getattr__(self, name: str):
        return getattr(self._connection, name)


def test_memory_atomic_commit() -> None:
    backend = MemoryBackend()

    backend.set("old", "value")

    with backend.atomic():
        backend.delete("old")
        backend.set("new", "value")

    assert not backend.exists("old")
    assert backend.get("new") == "value"


def test_memory_atomic_rollback() -> None:
    backend = MemoryBackend()

    backend.set("old", "value")

    with pytest.raises(RuntimeError, match="failure"):
        with backend.atomic():
            backend.delete("old")
            backend.set("new", "value")
            raise RuntimeError("failure")

    assert backend.get("old") == "value"
    assert not backend.exists("new")


def test_memory_nested_atomic() -> None:
    backend = MemoryBackend()

    with backend.atomic():
        backend.set("one", 1)

        with backend.atomic():
            backend.set("two", 2)

    assert backend.get("one") == 1
    assert backend.get("two") == 2


def test_sqlite_atomic_commit(tmp_path) -> None:
    backend = SQLiteBackend(tmp_path / "storage.db")

    backend.set("old", "value")

    with backend.atomic():
        backend.delete("old")
        backend.set("new", "value")

    assert not backend.exists("old")
    assert backend.get("new") == "value"

    backend.close()


def test_sqlite_atomic_rollback(tmp_path) -> None:
    backend = SQLiteBackend(tmp_path / "storage.db")

    backend.set("old", "value")

    with pytest.raises(RuntimeError, match="failure"):
        with backend.atomic():
            backend.delete("old")
            backend.set("new", "value")
            raise RuntimeError("failure")

    assert backend.get("old") == "value"
    assert not backend.exists("new")

    backend.close()


def test_sqlite_nested_atomic(tmp_path) -> None:
    backend = SQLiteBackend(tmp_path / "storage.db")

    with backend.atomic():
        backend.set("one", 1)

        with backend.atomic():
            backend.set("two", 2)

    assert backend.get("one") == 1
    assert backend.get("two") == 2

    backend.close()


def test_sqlite_atomic_commit_failure_rolls_back(tmp_path) -> None:
    backend = SQLiteBackend(tmp_path / "storage.db")

    backend.set("stable", "before")

    connection = backend._connection

    backend._connection = _ConnectionProxy(
        connection,
        fail_commit=True,
    )

    with pytest.raises(
        StorageWriteError,
        match="Failed to commit transaction",
    ):
        with backend.atomic():
            backend.set("stable", "after")

    backend._connection = connection

    assert backend.get("stable") == "before"

    backend.close()


def test_sqlite_atomic_commit_and_rollback_failure_preserves_rollback_error(
    tmp_path,
) -> None:
    backend = SQLiteBackend(tmp_path / "storage.db")

    connection = backend._connection

    backend._connection = _ConnectionProxy(
        connection,
        fail_commit=True,
        fail_rollback=True,
    )

    with pytest.raises(
        sqlite3.OperationalError,
        match="simulated rollback failure",
    ):
        with backend.atomic():
            backend.set("key", "value")

    backend._connection = connection

    backend.close()
