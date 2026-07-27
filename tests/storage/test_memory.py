"""
Tests for the MemoryStorage backend.
"""

from copy import deepcopy

import pytest

from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
)
from sentinel.storage.memory import MemoryStorage


def test_storage_starts_empty():
    storage = MemoryStorage()

    assert len(storage) == 0
    assert storage.keys() == []


def test_set_and_get():
    storage = MemoryStorage()

    storage.set("name", "Sentinel")

    assert storage.get("name") == "Sentinel"


def test_exists():
    storage = MemoryStorage()

    storage.set("a", 1)

    assert storage.exists("a")
    assert not storage.exists("b")


def test_delete():
    storage = MemoryStorage()

    storage.set("x", 100)

    storage.delete("x")

    assert not storage.exists("x")


def test_delete_missing_key():
    storage = MemoryStorage()

    with pytest.raises(StorageKeyNotFoundError):
        storage.delete("missing")


def test_get_missing_key():
    storage = MemoryStorage()

    with pytest.raises(StorageKeyNotFoundError):
        storage.get("missing")


def test_clear():
    storage = MemoryStorage()

    storage.set("a", 1)
    storage.set("b", 2)

    storage.clear()

    assert len(storage) == 0


def test_keys():
    storage = MemoryStorage()

    storage.set("x", 1)
    storage.set("y", 2)

    assert sorted(storage.keys()) == ["x", "y"]


def test_deepcopy_protection():
    storage = MemoryStorage()

    original = {
        "name": "Sentinel",
        "version": 1,
    }

    storage.set("config", original)

    original["version"] = 99

    stored = storage.get("config")

    assert stored["version"] == 1


def test_returned_object_is_copy():
    storage = MemoryStorage()

    storage.set("numbers", [1, 2, 3])

    numbers = storage.get("numbers")

    numbers.append(4)

    assert storage.get("numbers") == [1, 2, 3]


def test_close():
    storage = MemoryStorage()

    storage.close()

    with pytest.raises(StorageBackendError):
        storage.set("x", 1)


def test_close_clears_storage():
    storage = MemoryStorage()

    storage.set("a", 10)

    storage.close()

    with pytest.raises(StorageBackendError):
        storage.get("a")