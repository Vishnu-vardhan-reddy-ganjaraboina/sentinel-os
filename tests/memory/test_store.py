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


def test_iteration_returns_entries() -> None:
    store = InMemoryStore()

    first = create_entry("memory.1")
    second = create_entry("memory.2")

    store.add(first)
    store.add(second)

    assert list(store) == [first, second]


def test_concurrent_adds_are_atomic() -> None:
    store = InMemoryStore()
    entry = create_entry("memory.concurrent")

    def add_entry(_: int) -> str:
        try:
            store.add(entry)
            return "added"
        except MemoryAlreadyExistsError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(add_entry, range(32)))

    assert results.count("added") == 1
    assert results.count("duplicate") == 31
    assert len(store) == 1
    assert store.get("memory.concurrent") is entry


def test_concurrent_unique_adds_are_safe() -> None:
    store = InMemoryStore()

    entries = [
        create_entry(
            memory_id=f"memory.{index}",
            content=f"content {index}",
        )
        for index in range(100)
    ]

    def add_entry(entry: BaseMemoryEntry) -> None:
        store.add(entry)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(add_entry, entries))

    assert len(store) == 100

    for entry in entries:
        assert store.get(entry.id) is entry


def test_concurrent_reads_are_safe() -> None:
    store = InMemoryStore()

    entries = [
        create_entry(
            memory_id=f"memory.{index}",
            content=f"content {index}",
        )
        for index in range(100)
    ]

    for entry in entries:
        store.add(entry)

    def read_entry(index: int) -> BaseMemoryEntry:
        return store.get(f"memory.{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(read_entry, range(100)))

    assert results == entries


def test_concurrent_contains_and_len_are_safe() -> None:
    store = InMemoryStore()

    for index in range(100):
        store.add(create_entry(f"memory.{index}"))

    def inspect(_: int) -> tuple[bool, int]:
        return "memory.50" in store, len(store)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(inspect, range(100)))

    assert all(found for found, _ in results)
    assert all(length == 100 for _, length in results)


def test_iteration_uses_stable_snapshot() -> None:
    store = InMemoryStore()

    for index in range(100):
        store.add(create_entry(f"memory.{index}"))

    iterator = iter(store)

    store.clear()

    entries = list(iterator)

    assert len(entries) == 100
    assert len(store) == 0


def test_concurrent_search_is_safe() -> None:
    store = InMemoryStore()

    for index in range(100):
        store.add(
            create_entry(
                memory_id=f"memory.{index}",
                content=f"Sentinel memory {index}",
            )
        )

    def search(_: int) -> list[BaseMemoryEntry]:
        return store.search("sentinel")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(search, range(32)))

    assert all(len(result) == 100 for result in results)


def test_concurrent_clear_and_reads_are_safe() -> None:
    store = InMemoryStore()

    for index in range(100):
        store.add(create_entry(f"memory.{index}"))

    def inspect(_: int) -> tuple[int, bool]:
        return len(store), "memory.50" in store

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(inspect, index)
            for index in range(32)
        ]

        store.clear()

        results = [future.result() for future in futures]

    assert len(store) == 0
    assert all(length in {0, 100} for length, _ in results)
    assert all(found in {True, False} for _, found in results)


def test_concurrent_remove_is_safe() -> None:
    store = InMemoryStore()

    entry = create_entry("memory.concurrent")
    store.add(entry)

    def remove_entry(_: int) -> str:
        try:
            store.remove("memory.concurrent")
            return "removed"
        except MemoryNotFoundError:
            return "missing"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(remove_entry, range(32)))

    assert results.count("removed") == 1
    assert results.count("missing") == 31
    assert not store.exists("memory.concurrent")
