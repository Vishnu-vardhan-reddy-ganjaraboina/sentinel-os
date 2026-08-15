"""
High-level manager for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sentinel.memory.constants import MemoryType
from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.store import InMemoryStore


class MemoryManager:
    """
    High-level manager for memory operations.

    The manager coordinates memory entry creation and delegates
    storage operations to the configured memory store.
    """

    def __init__(
        self,
        store: InMemoryStore | None = None,
    ) -> None:
        self._store = store or InMemoryStore()

    @property
    def store(self) -> InMemoryStore:
        """Return the underlying memory store."""
        return self._store

    def create(
        self,
        memory_id: str,
        content: Any,
        *,
        importance: int = 1,
        memory_type: MemoryType = MemoryType.WORKING,
        ttl: timedelta | None = None,
    ) -> MemoryEntry:
        """
        Create and store a new memory entry.
        """
        entry = BaseMemoryEntry(
            memory_id=memory_id,
            content=content,
            importance=importance,
            memory_type=memory_type,
            ttl=ttl,
        )

        self._store.add(entry)

        return entry

    def get(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """
        Retrieve a memory entry.
        """
        entry = self._store.get(memory_id)

        if not entry.expired:
            entry.touch()

        return entry

    def remove(
        self,
        memory_id: str,
    ) -> None:
        """
        Permanently remove a memory entry.
        """
        self._store.remove(memory_id)

    def exists(
        self,
        memory_id: str,
    ) -> bool:
        """Return whether a memory exists."""
        return self._store.exists(memory_id)

    def search(
        self,
        keyword: str,
    ) -> list[MemoryEntry]:
        """
        Search stored memory entries.
        """
        return self._store.search(keyword)

    def archive(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """
        Archive a memory entry and return it.
        """
        entry = self._store.get(memory_id)
        entry.archive()
        return entry

    def delete(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """
        Mark a memory entry as deleted and return it.
        """
        entry = self._store.get(memory_id)
        entry.delete()
        return entry

    def clear(self) -> None:
        """Remove all memory entries."""
        self._store.clear()

    def list(self) -> list[MemoryEntry]:
        """Return all stored memory entries."""
        return self._store.list()

    def __len__(self) -> int:
        """Return the number of stored memory entries."""
        return len(self._store)
