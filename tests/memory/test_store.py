from concurrent.futures import ThreadPoolExecutor

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


def test_concurrent_adds_preserve_all_unique_entries() -> None:
    store = InMemoryStore()

    def add_entry(index: int) -> None:
        store.add(create_entry(f"memory.{index}", f"value-{index}"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(add_entry, range(200)))

    assert len(store) == 200
    assert len(store.list()) == 200
    assert all(store.exists(f"memory.{index}") for index in range(200))


def test_upsert_inserts_new_entry() -> None:
    store = InMemoryStore()
    entry = create_entry("memory.upsert", "first value")

    store.upsert(entry)

    assert store.get("memory.upsert") is entry
    assert len(store) == 1


def test_upsert_replaces_existing_entry() -> None:
    store = InMemoryStore()
    original = create_entry("memory.upsert", "first value")
    replacement = create_entry("memory.upsert", "updated value")

    store.add(original)
    store.upsert(replacement)

    assert store.get("memory.upsert") is replacement
    assert store.get("memory.upsert").content == "updated value"
    assert len(store) == 1


def test_concurrent_upserts_keep_one_entry_per_id() -> None:
    store = InMemoryStore()

    def upsert_entry(index: int) -> None:
        store.upsert(create_entry("memory.shared", f"value-{index}"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(upsert_entry, range(100)))

    assert len(store) == 1
    assert store.exists("memory.shared")
    assert store.get("memory.shared").id == "memory.shared"
