
import pytest

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.store import InMemoryStore


def create_entry(
    memory_id: str = "memory.1",
    content: object = "hello",
) -> BaseMemoryEntry:
    return BaseMemoryEntry(
        memory_id=memory_id,
        content=content,
    )


def test_add_and_get() -> None:
    store = InMemoryStore()
    entry = create_entry()

    store.add(entry)

    assert store.get("memory.1") is entry


def test_duplicate_add_raises() -> None:
    store = InMemoryStore()
    entry = create_entry()

    store.add(entry)

    with pytest.raises(MemoryAlreadyExistsError):
        store.add(entry)


def test_missing_get_raises() -> None:
    store = InMemoryStore()

    with pytest.raises(MemoryNotFoundError):
        store.get("missing")


def test_remove() -> None:
    store = InMemoryStore()
    entry = create_entry()

    store.add(entry)
    store.remove("memory.1")

    assert not store.exists("memory.1")


def test_remove_missing_raises() -> None:
    store = InMemoryStore()

    with pytest.raises(MemoryNotFoundError):
        store.remove("missing")


def test_exists() -> None:
    store = InMemoryStore()
    entry = create_entry()

    assert not store.exists("memory.1")

    store.add(entry)

    assert store.exists("memory.1")


def test_search() -> None:
    store = InMemoryStore()

    store.add(
        create_entry(
            "memory.1",
            "Sentinel operating system",
        )
    )
    store.add(
        create_entry(
            "memory.2",
            "Python programming",
        )
    )

    results = store.search("SENTINEL")

    assert len(results) == 1
    assert results[0].id == "memory.1"


def test_search_empty_keyword() -> None:
    store = InMemoryStore()
    store.add(create_entry())

    assert store.search("") == []


def test_list() -> None:
    store = InMemoryStore()

    first = create_entry("memory.1")
    second = create_entry("memory.2")

    store.add(first)
    store.add(second)

    assert store.list() == [first, second]


def test_clear() -> None:
    store = InMemoryStore()

    store.add(create_entry())

    store.clear()

    assert len(store) == 0
    assert store.list() == []


def test_contains() -> None:
    store = InMemoryStore()
    entry = create_entry()

    store.add(entry)

    assert "memory.1" in store
    assert "missing" not in store


def test_len() -> None:
    store = InMemoryStore()

    assert len(store) == 0

    store.add(create_entry())

    assert len(store) == 1

