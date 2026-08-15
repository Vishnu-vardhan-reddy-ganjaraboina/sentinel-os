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
