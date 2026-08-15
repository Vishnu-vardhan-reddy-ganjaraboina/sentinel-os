"""
High-level service for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sentinel.memory.constants import MemoryType
from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.manager import MemoryManager


class MemoryService:
    """
    High-level service for memory operations.

    The service provides the public subsystem API while delegating
    memory management to MemoryManager.
    """

    def __init__(
        self,
        manager: MemoryManager | None = None,
    ) -> None:
        self._manager = (
            manager
            if manager is not None
            else MemoryManager()
        )

    @property
    def manager(self) -> MemoryManager:
        """Return the underlying memory manager."""
        return self._manager

    def create(
        self,
        memory_id: str,
        content: Any,
        *,
        importance: int = 1,
        memory_type: MemoryType = MemoryType.WORKING,
        ttl: timedelta | None = None,
    ) -> MemoryEntry:
        """Create and store a memory entry."""
        return self._manager.create(
            memory_id=memory_id,
            content=content,
            importance=importance,
            memory_type=memory_type,
            ttl=ttl,
        )

    def get(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """Retrieve a memory entry."""
        return self._manager.get(memory_id)

    def remove(
        self,
        memory_id: str,
    ) -> None:
        """Permanently remove a memory entry."""
        self._manager.remove(memory_id)

    def exists(
        self,
        memory_id: str,
    ) -> bool:
        """Return whether a memory exists."""
        return self._manager.exists(memory_id)

    def search(
        self,
        keyword: str,
    ) -> list[MemoryEntry]:
        """Search stored memories."""
        return self._manager.search(keyword)

    def archive(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """Archive a memory entry."""
        return self._manager.archive(memory_id)

    def delete(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """Mark a memory entry as deleted."""
        return self._manager.delete(memory_id)

    def clear(self) -> None:
        """Remove all stored memories."""
        self._manager.clear()

    def list(self) -> list[MemoryEntry]:
        """Return all stored memory entries."""
        return self._manager.list()

    def __len__(self) -> int:
        """Return the number of stored memories."""
        return len(self._manager)
