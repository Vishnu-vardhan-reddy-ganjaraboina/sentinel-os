"""
Base implementation of a Sentinel memory entry.
"""

from __future__ import annotations

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

        if not memory_id.strip():
            raise ValueError("memory_id cannot be empty.")

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
        """
        Update the last accessed timestamp.
        """
        self._last_accessed = datetime.now(UTC)

    def archive(self) -> None:
        self._status = MemoryStatus.ARCHIVED

    def delete(self) -> None:
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