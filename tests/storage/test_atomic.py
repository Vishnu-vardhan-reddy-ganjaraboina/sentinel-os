from __future__ import annotations

import pytest

from sentinel.storage.backends.in_memory import MemoryBackend
from sentinel.storage.backends.sqlite import SQLiteBackend


def test_memory_atomic_commit() -> None:
    backend = MemoryBackend()

    backend.set(
        "old",
        "value",
    )

    with backend.atomic():
        backend.delete("old")
        backend.set(
            "new",
            "value",
        )

    assert not backend.exists("old")
    assert backend.get("new") == "value"


def test_memory_atomic_rollback() -> None:
    backend = MemoryBackend()

    backend.set(
        "old",
        "value",
    )

    with pytest.raises(
        RuntimeError,
        match="failure",
    ):
        with backend.atomic():
            backend.delete("old")
            backend.set(
                "new",
                "value",
            )

            raise RuntimeError(
                "failure"
            )

    assert backend.get("old") == "value"
    assert not backend.exists("new")


def test_memory_nested_atomic() -> None:
    backend = MemoryBackend()

    with backend.atomic():
        backend.set(
            "one",
            1,
        )

        with backend.atomic():
            backend.set(
                "two",
                2,
            )

    assert backend.get("one") == 1
    assert backend.get("two") == 2


def test_sqlite_atomic_commit(tmp_path) -> None:
    backend = SQLiteBackend(
        tmp_path / "storage.db"
    )

    backend.set(
        "old",
        "value",
    )

    with backend.atomic():
        backend.delete("old")
        backend.set(
            "new",
            "value",
        )

    assert not backend.exists("old")
    assert backend.get("new") == "value"

    backend.close()


def test_sqlite_atomic_rollback(tmp_path) -> None:
    backend = SQLiteBackend(
        tmp_path / "storage.db"
    )

    backend.set(
        "old",
        "value",
    )

    with pytest.raises(
        RuntimeError,
        match="failure",
    ):
        with backend.atomic():
            backend.delete("old")
            backend.set(
                "new",
                "value",
            )

            raise RuntimeError(
                "failure"
            )

    assert backend.get("old") == "value"
    assert not backend.exists("new")

    backend.close()


def test_sqlite_nested_atomic(tmp_path) -> None:
    backend = SQLiteBackend(
        tmp_path / "storage.db"
    )

    with backend.atomic():
        backend.set(
            "one",
            1,
        )

        with backend.atomic():
            backend.set(
                "two",
                2,
            )

    assert backend.get("one") == 1
    assert backend.get("two") == 2

    backend.close()