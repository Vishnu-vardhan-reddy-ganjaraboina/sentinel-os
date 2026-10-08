"""
Tests for FilesystemStorage.
"""

from pathlib import Path

import pytest

from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
    StorageSerializationError,
    StorageWriteError,
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
def test_replace_failure_preserves_existing_value_and_cleans_temp(
    tmp_path: Path,
    monkeypatch,
) -> None:
    storage = FilesystemStorage(tmp_path)

    storage.set(
        "config",
        {"version": 1},
    )

    def failing_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(
        "sentinel.storage.backends.filesystem.os.replace",
        failing_replace,
    )

    with pytest.raises(StorageWriteError, match="Unable to write 'config'"):
        storage.set(
            "config",
            {"version": 2},
        )

    assert storage.get("config") == {
        "version": 1,
    }

    assert list(tmp_path.glob("*.tmp")) == []


def test_serialization_failure_cleans_temp_file(
    tmp_path: Path,
) -> None:
    storage = FilesystemStorage(tmp_path)

    class Unserializable:
        pass

    with pytest.raises(StorageSerializationError):
        storage.set(
            "invalid",
            Unserializable(),
        )

    assert not (tmp_path / "invalid.json").exists()
    assert list(tmp_path.glob("*.tmp")) == []
