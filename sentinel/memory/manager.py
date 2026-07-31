"""
Manager for the Sentinel Memory subsystem.
"""

from __future__ import annotations

import builtins

from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.registry import MemoryRegistry


class MemoryManager:
    """
    High-level manager for memory entries.
    """

    def __init__(self) -> None:
        self._registry = MemoryRegistry()

    @property
    def registry(self) -> MemoryRegistry:
        return self._registry

    def register(self, entry: MemoryEntry) -> None:
        self._registry.register(entry)

    def unregister(self, memory_id: str) -> None:
        self._registry.unregister(memory_id)

    def get(self, memory_id: str) -> MemoryEntry:
        return self._registry.get(memory_id)

    def exists(self, memory_id: str) -> bool:
        return self._registry.exists(memory_id)

    def search(self, keyword: str) -> builtins.list[MemoryEntry]:
        return self._registry.search(keyword)

    def list(self) -> builtins.list[MemoryEntry]:
        return self._registry.list()

    def clear(self) -> None:
        self._registry.clear()