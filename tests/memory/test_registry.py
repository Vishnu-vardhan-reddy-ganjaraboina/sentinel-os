import pytest

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.registry import MemoryRegistry


def test_register():
    registry = MemoryRegistry()
    entry = BaseMemoryEntry("memory.one", "Hello")

    registry.register(entry)

    assert len(registry) == 1
    assert registry.exists(entry.id)


def test_duplicate_register():
    registry = MemoryRegistry()
    entry = BaseMemoryEntry("memory.one", "Hello")

    registry.register(entry)

    with pytest.raises(MemoryAlreadyExistsError):
        registry.register(entry)


def test_get():
    registry = MemoryRegistry()
    entry = BaseMemoryEntry("memory.one", "Hello")

    registry.register(entry)

    assert registry.get(entry.id) is entry


def test_get_not_found():
    registry = MemoryRegistry()

    with pytest.raises(MemoryNotFoundError):
        registry.get("missing")


def test_unregister():
    registry = MemoryRegistry()
    entry = BaseMemoryEntry("memory.one", "Hello")

    registry.register(entry)
    registry.unregister(entry.id)

    assert len(registry) == 0


def test_unregister_not_found():
    registry = MemoryRegistry()

    with pytest.raises(MemoryNotFoundError):
        registry.unregister("missing")


def test_search():
    registry = MemoryRegistry()

    registry.register(BaseMemoryEntry("1", "Sentinel AI"))
    registry.register(BaseMemoryEntry("2", "Python"))

    results = registry.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "1"


def test_list():
    registry = MemoryRegistry()

    registry.register(BaseMemoryEntry("1", "A"))
    registry.register(BaseMemoryEntry("2", "B"))

    assert len(registry.list()) == 2


def test_clear():
    registry = MemoryRegistry()

    registry.register(BaseMemoryEntry("1", "A"))
    registry.clear()

    assert len(registry) == 0


def test_contains():
    registry = MemoryRegistry()

    entry = BaseMemoryEntry("memory.one", "Hello")
    registry.register(entry)

    assert "memory.one" in registry


def test_iteration():
    registry = MemoryRegistry()

    registry.register(BaseMemoryEntry("1", "A"))
    registry.register(BaseMemoryEntry("2", "B"))

    ids = {entry.id for entry in registry}

    assert ids == {"1", "2"}