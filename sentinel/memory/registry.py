"""
Registry for the Sentinel Memory subsystem.
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator

from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.memory import MemoryStore


class MemoryRegistry:
    """
    Registry for managing memory entries.
    """

    def __init__(self) -> None:
        self._store = MemoryStore()

    @property
    def store(self) -> MemoryStore:
        return self._store

    def register(self, entry: MemoryEntry) -> None:
        self._store.add(entry)

    def unregister(self, memory_id: str) -> None:
        self._store.remove(memory_id)

    def get(self, memory_id: str) -> MemoryEntry:
        return self._store.get(memory_id)

    def exists(self, memory_id: str) -> bool:
        return self._store.exists(memory_id)

    def search(self, keyword: str) -> builtins.list[MemoryEntry]:
        return self._store.search(keyword)

    def list(self) -> builtins.list[MemoryEntry]:
        return self._store.list()

    def clear(self) -> None:
        self._store.clear()

    def __contains__(self, memory_id: str) -> bool:
        return memory_id in self._store

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self) -> Iterator[MemoryEntry]:
        return iter(self._store)