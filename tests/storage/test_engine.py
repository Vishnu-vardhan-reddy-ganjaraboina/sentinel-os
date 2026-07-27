"""
Tests for StorageEngine.
"""

import pytest

from sentinel.storage.engine import StorageEngine
from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
)
from sentinel.storage.filesystem import FilesystemStorage
from sentinel.storage.memory import MemoryStorage


def test_register_backend():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    assert engine.registered_backends() == ["memory"]


def test_duplicate_backend():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    with pytest.raises(StorageBackendError):
        engine.register("memory", MemoryStorage())


def test_default_backend():
    engine = StorageEngine()

    backend = MemoryStorage()

    engine.register("memory", backend)

    assert engine.backend() is backend


def test_set_get():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    engine.set("name", "Sentinel")

    assert engine.get("name") == "Sentinel"


def test_delete():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    engine.set("x", 100)

    engine.delete("x")

    with pytest.raises(StorageKeyNotFoundError):
        engine.get("x")


def test_unregister_backend():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    engine.unregister("memory")

    assert engine.registered_backends() == []


def test_unknown_backend():
    engine = StorageEngine()

    with pytest.raises(StorageBackendError):
        engine.backend("missing")


def test_switch_backends(tmp_path):
    engine = StorageEngine()

    memory = MemoryStorage()
    disk = FilesystemStorage(tmp_path)

    engine.register("memory", memory)
    engine.register("disk", disk)

    engine.set("a", 1)

    engine.set_default("disk")

    engine.set("a", 2)

    assert memory.get("a") == 1
    assert disk.get("a") == 2


def test_close():
    engine = StorageEngine()

    engine.register("memory", MemoryStorage())

    engine.close()

    with pytest.raises(StorageBackendError):
        engine.backend()