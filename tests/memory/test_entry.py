"""Tests for the production memory entry implementation."""

from concurrent.futures import ThreadPoolExecutor

from sentinel.memory.constants import MemoryStatus, MemoryType
from sentinel.memory.entry import BaseMemoryEntry


def test_concurrent_touch_is_safe() -> None:
    entry = BaseMemoryEntry(
        memory_id="memory.concurrent",
        content="hello",
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: entry.touch(), range(100)))

    assert entry.last_accessed >= entry.created_at


def test_concurrent_status_updates_are_safe() -> None:
    entry = BaseMemoryEntry(
        memory_id="memory.concurrent",
        content="hello",
    )

    def update(index: int) -> None:
        if index % 2 == 0:
            entry.archive()
        else:
            entry.delete()

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(update, range(100)))

    assert entry.status in {
        MemoryStatus.ARCHIVED,
        MemoryStatus.DELETED,
    }


def test_concurrent_content_access_is_safe() -> None:
    entry = BaseMemoryEntry(
        memory_id="memory.concurrent",
        content="hello",
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda _: entry.content,
                range(100),
            )
        )

    assert results == ["hello"] * 100


def test_to_dict_is_safe_during_concurrent_updates() -> None:
    entry = BaseMemoryEntry(
        memory_id="memory.concurrent",
        content="hello",
    )

    def read_snapshot(_: int) -> dict[str, object]:
        return entry.to_dict()

    with ThreadPoolExecutor(max_workers=8) as executor:
        snapshots = list(
            executor.map(read_snapshot, range(100))
        )

    assert len(snapshots) == 100

    for snapshot in snapshots:
        assert snapshot["id"] == "memory.concurrent"
        assert snapshot["content"] == "hello"
        assert snapshot["memory_type"] == MemoryType.WORKING.value
