"""
Base implementation of a Sentinel memory entry.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import RLock
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

    Mutable lifecycle state and access timestamps are protected against
    concurrent access. Content is isolated through defensive deep copies.
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
            raise TypeError("memory_type must be a MemoryType.")

        self._id = memory_id
        self._content = deepcopy(content)
        self._type = memory_type
        self._importance = importance
        self._ttl = ttl

        self._status = MemoryStatus.ACTIVE

        now = datetime.now(UTC)
        self._created_at = now
        self._last_accessed = now
        self._lock = RLock()

    @property
    def id(self) -> str:
        return self._id

    @property
    def content(self) -> Any:
        with self._lock:
            self._last_accessed = datetime.now(UTC)
            return deepcopy(self._content)

    @property
    def importance(self) -> int:
        return self._importance

    @property
    def memory_type(self) -> MemoryType:
        return self._type

    @property
    def status(self) -> MemoryStatus:
        with self._lock:
            return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def last_accessed(self) -> datetime:
        with self._lock:
            return self._last_accessed

    @property
    def expired(self) -> bool:
        with self._lock:
            if self._ttl is None:
                return False
            return datetime.now(UTC) >= self._created_at + self._ttl

    def touch(self) -> None:
        """Update the last accessed timestamp."""
        with self._lock:
            self._last_accessed = datetime.now(UTC)

    def archive(self) -> None:
        """Archive this memory entry."""
        with self._lock:
            self._status = MemoryStatus.ARCHIVED

    def delete(self) -> None:
        """Mark this memory entry as deleted."""
        with self._lock:
            self._status = MemoryStatus.DELETED

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "id": self._id,
                "content": deepcopy(self._content),
                "memory_type": self._type.value,
                "importance": self._importance,
                "status": self._status.value,
                "created_at": self._created_at.isoformat(),
                "last_accessed": self._last_accessed.isoformat(),
                "expired": (
                    self._ttl is not None
                    and datetime.now(UTC)
                    >= self._created_at + self._ttl
                ),
            }
