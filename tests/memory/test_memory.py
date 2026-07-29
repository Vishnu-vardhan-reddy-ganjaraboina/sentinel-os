import pytest

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.memory import MemoryStore


def test_add():
    store = MemoryStore()
    entry = BaseMemoryEntry("memory.one", "Hello")

    store.add(entry)

    assert len(store) == 1
    assert store.exists(entry.id)


def test_duplicate_add():
    store = MemoryStore()
    entry = BaseMemoryEntry("memory.one", "Hello")

    store.add(entry)

    with pytest.raises(MemoryAlreadyExistsError):
        store.add(entry)


def test_get():
    store = MemoryStore()
    entry = BaseMemoryEntry("memory.one", "Hello")

    store.add(entry)

    assert store.get(entry.id) is entry


def test_get_not_found():
    store = MemoryStore()

    with pytest.raises(MemoryNotFoundError):
        store.get("missing")


def test_remove():
    store = MemoryStore()
    entry = BaseMemoryEntry("memory.one", "Hello")

    store.add(entry)
    store.remove(entry.id)

    assert len(store) == 0


def test_remove_not_found():
    store = MemoryStore()

    with pytest.raises(MemoryNotFoundError):
        store.remove("missing")


def test_search():
    store = MemoryStore()

    store.add(BaseMemoryEntry("1", "Sentinel AI"))
    store.add(BaseMemoryEntry("2", "Python"))

    results = store.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "1"


def test_clear():
    store = MemoryStore()

    store.add(BaseMemoryEntry("1", "A"))
    store.add(BaseMemoryEntry("2", "B"))

    store.clear()

    assert len(store) == 0


def test_iteration():
    store = MemoryStore()

    store.add(BaseMemoryEntry("1", "A"))
    store.add(BaseMemoryEntry("2", "B"))

    ids = {entry.id for entry in store}

    assert ids == {"1", "2"}


def test_contains():
    store = MemoryStore()

    entry = BaseMemoryEntry("memory.one", "Hello")

    store.add(entry)

    assert "memory.one" in store