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

    The entry protects its mutable lifecycle state and access timestamps
    so that concurrent readers and lifecycle operations remain consistent.
    Mutable content is isolated from callers through defensive deep copies.
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
        self._status_changed_at = now

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
    def status_changed_at(self) -> datetime:
        with self._lock:
            return self._status_changed_at

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
            self._status_changed_at = datetime.now(UTC)

    def delete(self) -> None:
        """Mark this memory entry as deleted."""
        with self._lock:
            self._status = MemoryStatus.DELETED
            self._status_changed_at = datetime.now(UTC)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseMemoryEntry:
        """Restore a memory entry while preserving lifecycle timestamps and TTL."""
        if not isinstance(data, dict):
            raise TypeError("memory data must be a dictionary.")

        required = {
            "id", "content", "memory_type", "importance", "status",
            "created_at", "last_accessed",
        }
        if not required.issubset(data):
            raise ValueError("memory data is missing required fields.")

        try:
            if not isinstance(data["created_at"], str):
                raise ValueError("created_at must be a timestamp string.")
            if not isinstance(data["last_accessed"], str):
                raise ValueError("last_accessed must be a timestamp string.")

            memory_type = MemoryType(data["memory_type"])
            status = MemoryStatus(data["status"])
            created_at = datetime.fromisoformat(data["created_at"])
            last_accessed = datetime.fromisoformat(data["last_accessed"])

            status_changed_at_value = data.get(
                "status_changed_at",
                data["created_at"],
            )
            if not isinstance(status_changed_at_value, str):
                raise ValueError("status_changed_at must be a timestamp string.")
            status_changed_at = datetime.fromisoformat(status_changed_at_value)

            ttl_seconds = data.get("ttl_seconds")
            if ttl_seconds is not None and (
                isinstance(ttl_seconds, bool)
                or not isinstance(ttl_seconds, (int, float))
                or ttl_seconds < 0
            ):
                raise ValueError("ttl_seconds must be a non-negative number or None.")

            entry = cls(
                memory_id=data["id"],
                content=data["content"],
                importance=data["importance"],
                memory_type=memory_type,
                ttl=(
                    timedelta(seconds=ttl_seconds)
                    if ttl_seconds is not None else None
                ),
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Stored memory entry is invalid.") from exc

        if (
            created_at.tzinfo is None
            or last_accessed.tzinfo is None
            or status_changed_at.tzinfo is None
        ):
            raise ValueError("Stored memory timestamps must include a timezone.")

        with entry._lock:
            entry._created_at = created_at.astimezone(UTC)
            entry._last_accessed = last_accessed.astimezone(UTC)
            entry._status = status
            entry._status_changed_at = status_changed_at.astimezone(UTC)

        return entry

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
                "status_changed_at": self._status_changed_at.isoformat(),
                "ttl_seconds": (
                    self._ttl.total_seconds() if self._ttl is not None else None
                ),
                "expired": (
                    self._ttl is not None
                    and datetime.now(UTC)
                    >= self._created_at + self._ttl
                ),
            }
