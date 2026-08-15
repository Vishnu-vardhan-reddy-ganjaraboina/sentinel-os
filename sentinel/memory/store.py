"""
In-memory storage implementation for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.interfaces import Memory, MemoryEntry


class InMemoryStore(Memory):
    """
    Thread-unsafe in-memory memory store.

    The store owns persistence of memory entries only. It does not
    perform authorization, expiration policy, or orchestration.
    """

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}

    def add(self, entry: MemoryEntry) -> None:
        """
        Add a memory entry.

        Raises:
            MemoryAlreadyExistsError:
                If an entry with the same ID already exists.
        """
        if entry.id in self._entries:
            raise MemoryAlreadyExistsError(
                f"Memory '{entry.id}' already exists."
            )

        self._entries[entry.id] = entry

    def get(self, memory_id: str) -> MemoryEntry:
        """
        Retrieve a memory entry.

        Raises:
            MemoryNotFoundError:
                If the memory does not exist.
        """
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
        if memory_id not in self._entries:
            raise MemoryNotFoundError(
                f"Memory '{memory_id}' was not found."
            )

        del self._entries[memory_id]

    def exists(self, memory_id: str) -> bool:
        """Return whether a memory entry exists."""
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

        return [
            entry
            for entry in self._entries.values()
            if normalized in str(entry.content).lower()
        ]

    def clear(self) -> None:
        """Remove all stored memory entries."""
        self._entries.clear()

    def list(self) -> list[MemoryEntry]:
        """Return all stored memory entries."""
        return list(self._entries.values())

    def __contains__(self, memory_id: object) -> bool:
        """Support ``memory_id in store``."""
        return (
            isinstance(memory_id, str)
            and memory_id in self._entries
        )

    def __len__(self) -> int:
        """Return the number of stored entries."""
        return len(self._entries)
