"""
Tests for FilesystemStorage.
"""

from pathlib import Path

import pytest

from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
)
from sentinel.storage.filesystem import FilesystemStorage


def test_storage_starts_empty(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    assert storage.keys() == []


def test_set_and_get(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("user", {"name": "Sentinel"})

    assert storage.get("user") == {
        "name": "Sentinel"
    }


def test_exists(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("a", 1)

    assert storage.exists("a")
    assert not storage.exists("b")


def test_delete(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("x", 1)

    storage.delete("x")

    assert not storage.exists("x")


def test_delete_missing_key(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    with pytest.raises(StorageKeyNotFoundError):
        storage.delete("missing")


def test_clear(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("a", 1)
    storage.set("b", 2)

    storage.clear()

    assert storage.keys() == []


def test_keys(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("x", 1)
    storage.set("y", 2)

    assert storage.keys() == ["x", "y"]


def test_invalid_key(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.set("../../secret", 1)


def test_close(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.close()

    with pytest.raises(StorageBackendError):
        storage.set("a", 1)


def test_persistence(tmp_path: Path):
    storage = FilesystemStorage(tmp_path)

    storage.set("config", {"version": 1})

    storage2 = FilesystemStorage(tmp_path)

    assert storage2.get("config") == {
        "version": 1
    }