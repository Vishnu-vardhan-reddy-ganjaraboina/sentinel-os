from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from sentinel.memory.constants import MemoryStatus, MemoryType
from sentinel.memory.exceptions import MemoryAlreadyExistsError
from sentinel.memory.manager import MemoryManager


def test_create() -> None:
    manager = MemoryManager()

    entry = manager.create(
        "memory.1",
        "hello",
    )

    assert entry.id == "memory.1"
    assert entry.content == "hello"
    assert manager.exists("memory.1")


def test_create_with_options() -> None:
    manager = MemoryManager()

    entry = manager.create(
        "memory.1",
        {"value": 42},
        importance=5,
        memory_type=MemoryType.LONG_TERM,
        ttl=timedelta(hours=1),
    )

    assert entry.importance == 5
    assert entry.memory_type == MemoryType.LONG_TERM
    assert entry.expired is False


def test_duplicate_create_raises() -> None:
    manager = MemoryManager()

    manager.create("memory.1", "first")

    with pytest.raises(MemoryAlreadyExistsError):
        manager.create("memory.1", "second")


def test_get() -> None:
    manager = MemoryManager()

    created = manager.create(
        "memory.1",
        "hello",
    )

    result = manager.get("memory.1")

    assert result is created
    assert result.content == "hello"


def test_remove() -> None:
    manager = MemoryManager()

    manager.create(
        "memory.1",
        "hello",
    )

    manager.remove("memory.1")

    assert not manager.exists("memory.1")


def test_search() -> None:
    manager = MemoryManager()

    manager.create(
        "memory.1",
        "Sentinel operating system",
    )
    manager.create(
        "memory.2",
        "Python programming",
    )

    results = manager.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "memory.1"


def test_archive() -> None:
    manager = MemoryManager()

    manager.create(
        "memory.1",
        "hello",
    )

    entry = manager.archive("memory.1")

    assert entry.status == MemoryStatus.ARCHIVED


def test_delete() -> None:
    manager = MemoryManager()

    manager.create(
        "memory.1",
        "hello",
    )

    entry = manager.delete("memory.1")

    assert entry.status == MemoryStatus.DELETED


def test_clear() -> None:
    manager = MemoryManager()

    manager.create("memory.1", "one")
    manager.create("memory.2", "two")

    manager.clear()

    assert len(manager) == 0
    assert manager.list() == []


def test_list() -> None:
    manager = MemoryManager()

    first = manager.create("memory.1", "one")
    second = manager.create("memory.2", "two")

    assert manager.list() == [first, second]


def test_len() -> None:
    manager = MemoryManager()

    assert len(manager) == 0

    manager.create("memory.1", "hello")

    assert len(manager) == 1


def test_falsey_custom_store_is_preserved() -> None:
    class FalseyStore:
        def __bool__(self) -> bool:
            return False

        def add(self, entry):
            self.entry = entry

        def get(self, memory_id):
            return self.entry

        def remove(self, memory_id):
            del self.entry

        def exists(self, memory_id):
            return hasattr(self, "entry")

        def search(self, keyword):
            return []

        def clear(self):
            if hasattr(self, "entry"):
                del self.entry

        def list(self):
            return [self.entry] if hasattr(self, "entry") else []

        def __len__(self):
            return 1 if hasattr(self, "entry") else 0

    store = FalseyStore()
    manager = MemoryManager(store=store)  # type: ignore[arg-type]

    assert manager.store is store


def test_concurrent_unique_creates_are_safe() -> None:
    manager = MemoryManager()

    def create_entry(index: int):
        return manager.create(
            f"memory.{index}",
            f"content {index}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        entries = list(executor.map(create_entry, range(100)))

    assert len(entries) == 100
    assert len(manager) == 100

    for index, entry in enumerate(entries):
        assert entry.id == f"memory.{index}"
        assert manager.exists(f"memory.{index}")


def test_concurrent_duplicate_creates_are_atomic() -> None:
    manager = MemoryManager()

    def create_duplicate(index: int) -> str:
        try:
            manager.create(
                "memory.concurrent",
                f"content {index}",
            )
            return "created"
        except MemoryAlreadyExistsError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(create_duplicate, range(32))
        )

    assert results.count("created") == 1
    assert results.count("duplicate") == 31
    assert len(manager) == 1


def test_concurrent_gets_are_safe() -> None:
    manager = MemoryManager()

    entries = [
        manager.create(
            f"memory.{index}",
            f"content {index}",
        )
        for index in range(100)
    ]

    def get_entry(index: int):
        return manager.get(f"memory.{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(get_entry, range(100))
        )

    assert results == entries


def test_concurrent_search_is_safe() -> None:
    manager = MemoryManager()

    for index in range(100):
        manager.create(
            f"memory.{index}",
            f"Sentinel memory {index}",
        )

    def search(_: int):
        return manager.search("sentinel")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(search, range(32))
        )

    assert all(len(result) == 100 for result in results)


def test_concurrent_archive_and_delete_are_safe() -> None:
    manager = MemoryManager()

    entry = manager.create(
        "memory.concurrent",
        "hello",
    )

    def update(index: int) -> str:
        if index % 2 == 0:
            manager.archive("memory.concurrent")
            return "archived"

        manager.delete("memory.concurrent")
        return "deleted"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(update, range(32))
        )

    assert len(results) == 32
    assert entry.status in {
        MemoryStatus.ARCHIVED,
        MemoryStatus.DELETED,
    }
