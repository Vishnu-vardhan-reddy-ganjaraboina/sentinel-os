"""
Base implementation of a Sentinel memory entry.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

from sentinel.memory.constants import (
    DEFAULT_IMPORTANCE,
    DEFAULT_TTL,
    MemoryStatus,
    MemoryType,
)
from sentinel.memory.interfaces import MemoryEntry


class BaseMemoryEntry(MemoryEntry):
    """
    Base implementation of a memory entry.
    """

    def __init__(
        self,
        memory_id: str,
        content: Any,
        memory_type: MemoryType = MemoryType.WORKING,
        importance: int = DEFAULT_IMPORTANCE,
        ttl: timedelta | None = DEFAULT_TTL,
    ) -> None:
        if not isinstance(memory_id, str):
            raise TypeError("memory_id must be a string.")

        if not memory_id.strip():
            raise ValueError("memory_id cannot be empty.")

        if not isinstance(importance, int):
            raise TypeError("importance must be an integer.")

        if importance < 0:
            raise ValueError("importance cannot be negative.")

        if ttl is not None:
            if not isinstance(ttl, timedelta):
                raise TypeError("ttl must be a timedelta or None.")

            if ttl.total_seconds() < 0:
                raise ValueError("ttl cannot be negative.")

        if not isinstance(memory_type, MemoryType):
            raise TypeError(
                "memory_type must be a MemoryType."
            )

        self._id = memory_id
        self._content = content
        self._type = memory_type
        self._importance = importance
        self._ttl = ttl

        self._status = MemoryStatus.ACTIVE

        self._created_at = datetime.now(UTC)
        self._last_accessed = self._created_at

    @property
    def id(self) -> str:
        return self._id

    @property
    def content(self) -> Any:
        self.touch()
        return self._content

    @property
    def importance(self) -> int:
        return self._importance

    @property
    def memory_type(self) -> MemoryType:
        return self._type

    @property
    def status(self) -> MemoryStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def last_accessed(self) -> datetime:
        return self._last_accessed

    @property
    def expired(self) -> bool:
        if self._ttl is None:
            return False

        return datetime.now(UTC) >= self._created_at + self._ttl

    def touch(self) -> None:
        """Update the last accessed timestamp."""
        self._last_accessed = datetime.now(UTC)

    def archive(self) -> None:
        """Archive this memory entry."""
        self._status = MemoryStatus.ARCHIVED

    def delete(self) -> None:
        """Mark this memory entry as deleted."""
        self._status = MemoryStatus.DELETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self._content,
            "memory_type": self.memory_type.value,
            "importance": self.importance,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expired": self.expired,
        }



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