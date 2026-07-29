import pytest

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import MemoryNotFoundError
from sentinel.memory.manager import MemoryManager


def test_register():
    manager = MemoryManager()

    entry = BaseMemoryEntry("memory.one", "Hello")

    manager.register(entry)

    assert manager.exists(entry.id)


def test_get():
    manager = MemoryManager()

    entry = BaseMemoryEntry("memory.one", "Hello")

    manager.register(entry)

    assert manager.get(entry.id) is entry


def test_unregister():
    manager = MemoryManager()

    entry = BaseMemoryEntry("memory.one", "Hello")

    manager.register(entry)

    manager.unregister(entry.id)

    assert not manager.exists(entry.id)


def test_search():
    manager = MemoryManager()

    manager.register(BaseMemoryEntry("1", "Sentinel AI"))
    manager.register(BaseMemoryEntry("2", "Python"))

    results = manager.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "1"


def test_list():
    manager = MemoryManager()

    manager.register(BaseMemoryEntry("1", "A"))
    manager.register(BaseMemoryEntry("2", "B"))

    assert len(manager.list()) == 2


def test_clear():
    manager = MemoryManager()

    manager.register(BaseMemoryEntry("1", "A"))
    manager.register(BaseMemoryEntry("2", "B"))

    manager.clear()

    assert len(manager.list()) == 0


def test_get_missing():
    manager = MemoryManager()

    with pytest.raises(MemoryNotFoundError):
        manager.get("missing")