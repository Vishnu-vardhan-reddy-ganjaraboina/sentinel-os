"""
Service layer for the Sentinel Memory subsystem.
"""

from __future__ import annotations

import builtins

from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.manager import MemoryManager
from sentinel.memory.registry import MemoryRegistry


class MemoryService:
    """
    Public service interface for memory management.
    """

    def __init__(self) -> None:
        self._manager = MemoryManager()

    @property
    def manager(self) -> MemoryManager:
        return self._manager

    @property
    def registry(self) -> MemoryRegistry:
        return self._manager.registry

    def register(self, entry: MemoryEntry) -> None:
        self._manager.register(entry)

    def unregister(self, memory_id: str) -> None:
        self._manager.unregister(memory_id)

    def get(self, memory_id: str) -> MemoryEntry:
        return self._manager.get(memory_id)

    def exists(self, memory_id: str) -> bool:
        return self._manager.exists(memory_id)

    def search(self, keyword: str) -> builtins.list[MemoryEntry]:
        return self._manager.search(keyword)

    def list(self) -> builtins.list[MemoryEntry]:
        return self._manager.list()

    def clear(self) -> None:
        self._manager.clear()