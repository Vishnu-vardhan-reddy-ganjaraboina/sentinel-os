"""
Tests for the Sentinel Memory runtime service.
"""

from __future__ import annotations

from datetime import timedelta

from sentinel.kernel.service import Service
from sentinel.memory.constants import MemoryStatus
from sentinel.memory.constants import MemoryType
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService


def test_runtime_name() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.name == "memory"


def test_runtime_default_service() -> None:
    runtime = MemoryRuntimeService()

    assert isinstance(runtime.memory, MemoryService)


def test_runtime_dependencies() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.dependencies == ()


def test_runtime_health_before_initialize() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize() -> None:
    runtime = MemoryRuntimeService()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_initialize_is_idempotent() -> None:
    runtime = MemoryRuntimeService()

    runtime.initialize()
    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_shutdown() -> None:
    runtime = MemoryRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_shutdown_is_idempotent() -> None:
    runtime = MemoryRuntimeService()

    runtime.initialize()
    runtime.shutdown()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_is_service() -> None:
    runtime = MemoryRuntimeService()

    assert isinstance(runtime, Service)


def test_runtime_delegates_create() -> None:
    runtime = MemoryRuntimeService()

    entry = runtime.create(
        "test-id",
        "hello",
    )

    assert entry.content == "hello"
    assert entry.id == "test-id"
    assert runtime.get("test-id") is entry


def test_runtime_delegates_create_with_options() -> None:
    runtime = MemoryRuntimeService()

    entry = runtime.create(
        "test-id",
        "hello",
        importance=5,
        memory_type=MemoryType.LONG_TERM,
        ttl=timedelta(hours=1),
    )

    assert entry.importance == 5
    assert entry.memory_type == MemoryType.LONG_TERM


def test_runtime_delegates_get() -> None:
    runtime = MemoryRuntimeService()

    created = runtime.create(
        "test-id",
        "hello",
    )

    retrieved = runtime.get("test-id")

    assert retrieved is created


def test_runtime_delegates_exists() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.exists("test-id") is False

    runtime.create(
        "test-id",
        "hello",
    )

    assert runtime.exists("test-id") is True


def test_runtime_delegates_search() -> None:
    runtime = MemoryRuntimeService()

    runtime.create("one", "hello world")
    runtime.create("two", "another value")

    results = runtime.search("hello")

    assert len(results) == 1
    assert results[0].id == "one"


def test_runtime_delegates_archive() -> None:
    runtime = MemoryRuntimeService()

    runtime.create(
        "test-id",
        "hello",
    )

    entry = runtime.archive("test-id")

    assert entry.status == MemoryStatus.ARCHIVED


def test_runtime_delegates_delete() -> None:
    runtime = MemoryRuntimeService()

    runtime.create(
        "test-id",
        "hello",
    )

    entry = runtime.delete("test-id")

    assert entry.status == MemoryStatus.DELETED


def test_runtime_delegates_remove() -> None:
    runtime = MemoryRuntimeService()

    runtime.create(
        "test-id",
        "hello",
    )

    runtime.remove("test-id")

    assert runtime.exists("test-id") is False


def test_runtime_delegates_list() -> None:
    runtime = MemoryRuntimeService()

    runtime.create("one", "hello")
    runtime.create("two", "world")

    entries = runtime.list()

    assert len(entries) == 2
    assert {entry.id for entry in entries} == {
        "one",
        "two",
    }


def test_runtime_delegates_clear() -> None:
    runtime = MemoryRuntimeService()

    runtime.create("one", "hello")
    runtime.create("two", "world")

    runtime.clear()

    assert len(runtime) == 0
    assert runtime.list() == []


def test_runtime_len_delegates_to_service() -> None:
    runtime = MemoryRuntimeService()

    assert len(runtime) == 0

    runtime.create(
        "test-id",
        "hello",
    )

    assert len(runtime) == 1


def test_runtime_exposes_underlying_memory_service() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.memory is not None
    assert isinstance(runtime.memory, MemoryService)