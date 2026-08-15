from datetime import timedelta

from sentinel.memory.constants import MemoryType
from sentinel.memory.manager import MemoryManager
from sentinel.memory.service import MemoryService


def test_manager_property() -> None:
    manager = MemoryManager()
    service = MemoryService(manager)

    assert service.manager is manager


def test_create() -> None:
    service = MemoryService()

    entry = service.create(
        "memory.1",
        "hello",
    )

    assert entry.id == "memory.1"
    assert entry.content == "hello"
    assert service.exists("memory.1")


def test_create_with_options() -> None:
    service = MemoryService()

    entry = service.create(
        "memory.1",
        {"value": 42},
        importance=5,
        memory_type=MemoryType.LONG_TERM,
        ttl=timedelta(hours=1),
    )

    assert entry.importance == 5
    assert entry.memory_type == MemoryType.LONG_TERM
    assert entry.expired is False


def test_get() -> None:
    service = MemoryService()

    created = service.create(
        "memory.1",
        "hello",
    )

    assert service.get("memory.1") is created


def test_remove() -> None:
    service = MemoryService()

    service.create(
        "memory.1",
        "hello",
    )

    service.remove("memory.1")

    assert not service.exists("memory.1")


def test_search() -> None:
    service = MemoryService()

    service.create(
        "memory.1",
        "Sentinel operating system",
    )
    service.create(
        "memory.2",
        "Python programming",
    )

    results = service.search("sentinel")

    assert len(results) == 1
    assert results[0].id == "memory.1"


def test_archive() -> None:
    service = MemoryService()

    service.create(
        "memory.1",
        "hello",
    )

    entry = service.archive("memory.1")

    assert entry.status.value == "archived"


def test_delete() -> None:
    service = MemoryService()

    service.create(
        "memory.1",
        "hello",
    )

    entry = service.delete("memory.1")

    assert entry.status.value == "deleted"


def test_clear() -> None:
    service = MemoryService()

    service.create("memory.1", "one")
    service.create("memory.2", "two")

    service.clear()

    assert len(service) == 0


def test_list() -> None:
    service = MemoryService()

    first = service.create("memory.1", "one")
    second = service.create("memory.2", "two")

    assert service.list() == [first, second]


def test_len() -> None:
    service = MemoryService()

    assert len(service) == 0

    service.create("memory.1", "hello")

    assert len(service) == 1
