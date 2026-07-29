"""
Memory store implementation for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from threading import RLock
from typing import Dict, List

from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.interfaces import Memory, MemoryEntry


class MemoryStore(Memory):
    """
    Thread-safe in-memory storage for memory entries.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, MemoryEntry] = {}
        self._lock = RLock()

    def add(self, entry: MemoryEntry) -> None:
        with self._lock:
            if entry.id in self._entries:
                raise MemoryAlreadyExistsError(
                    f"Memory '{entry.id}' already exists."
                )

            self._entries[entry.id] = entry

    def get(self, memory_id: str) -> MemoryEntry:
        with self._lock:
            if memory_id not in self._entries:
                raise MemoryNotFoundError(
                    f"Memory '{memory_id}' not found."
                )

            return self._entries[memory_id]

    def remove(self, memory_id: str) -> None:
        with self._lock:
            if memory_id not in self._entries:
                raise MemoryNotFoundError(
                    f"Memory '{memory_id}' not found."
                )

            del self._entries[memory_id]

    def exists(self, memory_id: str) -> bool:
        with self._lock:
            return memory_id in self._entries

    def search(self, keyword: str) -> List[MemoryEntry]:
        with self._lock:
            keyword = keyword.lower()

            return [
                entry
                for entry in self._entries.values()
                if keyword in str(entry.content).lower()
            ]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def list(self) -> List[MemoryEntry]:
        with self._lock:
            return list(self._entries.values())

    def __contains__(self, memory_id: str) -> bool:
        return self.exists(memory_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __iter__(self):
        return iter(self.list())