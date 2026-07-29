import pytest

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import MemoryNotFoundError
from sentinel.memory.service import MemoryService


def test_register():
    service = MemoryService()

    entry = BaseMemoryEntry("memory.one", "Hello")

    service.register(entry)

    assert service.exists(entry.id)


def test_get():
    service = MemoryService()

    entry = BaseMemoryEntry("memory.one", "Hello")

    service.register(entry)

    assert service.get(entry.id) is entry


def test_unregister():
    service = MemoryService()

    entry = BaseMemoryEntry("memory.one", "Hello")

    service.register(entry)

    service.unregister(entry.id)

    assert not service.exists(entry.id)


def test_search():
    service = MemoryService()

    service.register(BaseMemoryEntry("1", "Sentinel AI"))
    service.register(BaseMemoryEntry("2", "Python"))

    results = service.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "1"


def test_list():
    service = MemoryService()

    service.register(BaseMemoryEntry("1", "A"))
    service.register(BaseMemoryEntry("2", "B"))

    assert len(service.list()) == 2


def test_clear():
    service = MemoryService()

    service.register(BaseMemoryEntry("1", "A"))
    service.register(BaseMemoryEntry("2", "B"))

    service.clear()

    assert len(service.list()) == 0


def test_get_missing():
    service = MemoryService()

    with pytest.raises(MemoryNotFoundError):
        service.get("missing")