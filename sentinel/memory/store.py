"""
In-memory storage implementation for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from threading import RLock

from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.interfaces import Memory, MemoryEntry


class InMemoryStore(Memory):
    """
    Thread-safe in-memory memory store.

    The store owns persistence of memory entries only. It does not
    perform authorization, expiration policy, or orchestration.
    """

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._lock = RLock()

    def add(self, entry: MemoryEntry) -> None:
        """
        Add a memory entry.

        Raises:
            MemoryAlreadyExistsError:
                If an entry with the same ID already exists.
        """
        with self._lock:
            if entry.id in self._entries:
                raise MemoryAlreadyExistsError(f"Memory '{entry.id}' already exists.")
            self._entries[entry.id] = entry

    def upsert(self, entry: MemoryEntry) -> None:
        """Insert or atomically replace an entry by ID."""
        with self._lock:
            self._entries[entry.id] = entry

    def get(self, memory_id: str) -> MemoryEntry:
        """
        Retrieve a memory entry.

        Raises:
            MemoryNotFoundError:
                If the memory does not exist.
        """
        with self._lock:
            try:
                return self._entries[memory_id]
            except KeyError as exc:
                raise MemoryNotFoundError(
                    f"Memory '{memory_id}' was not found."
                ) from exc

    def remove(self, memory_id: str) -> None:
        """
        Remove a memory entry.

        Raises:
            MemoryNotFoundError:
                If the memory does not exist.
        """
        with self._lock:
            if memory_id not in self._entries:
                raise MemoryNotFoundError(f"Memory '{memory_id}' was not found.")
            del self._entries[memory_id]

    def exists(self, memory_id: str) -> bool:
        """Return whether a memory entry exists."""
        with self._lock:
            return memory_id in self._entries

    def search(self, keyword: str) -> list[MemoryEntry]:
        """
        Search memory entries by content.

        String content is matched case-insensitively.
        Other content types are converted to strings.
        """
        normalized = keyword.strip().lower()
        if not normalized:
            return []

        with self._lock:
            return [
                entry
                for entry in self._entries.values()
                if normalized in str(entry.content).lower()
            ]

    def clear(self) -> None:
        """Remove all stored memory entries."""
        with self._lock:
            self._entries.clear()

    def list(self) -> list[MemoryEntry]:
        """Return all stored memory entries."""
        with self._lock:
            return list(self._entries.values())

    def __contains__(self, memory_id: object) -> bool:
        """Support ``memory_id in store``."""
        return isinstance(memory_id, str) and self.exists(memory_id)

    def __len__(self) -> int:
        """Return the number of stored entries."""
        with self._lock:
            return len(self._entries)
