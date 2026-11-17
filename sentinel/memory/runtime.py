"""
Kernel runtime service for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from datetime import timedelta
from threading import RLock
from typing import Any

from sentinel.kernel.service import Service
from sentinel.memory.constants import MemoryType
from sentinel.memory.interfaces import MemoryEntry
from sentinel.memory.lifecycle import MemoryLifecycle, RetentionPolicy
from sentinel.memory.persistent_store import PersistentMemoryStore
from sentinel.memory.service import MemoryService


class MemoryRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for MemoryService.

    The runtime service exposes the Memory subsystem API directly
    while retaining Kernel lifecycle management.
    """

    def __init__(
        self,
        memory: MemoryService | None = None,
        *,
        retention_policy: RetentionPolicy | None = None,
    ) -> None:
        super().__init__(
            "memory",
            dependencies=(),
        )

        self._memory = (
            memory
            if memory is not None
            else MemoryService()
        )

        self._initialized = False
        self._lock = RLock()
        self._retention_policy = retention_policy or RetentionPolicy()
        self._last_retention_removed = 0

    @property
    def memory(self) -> MemoryService:
        """Return the underlying Memory service."""
        return self._memory

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
        return self._memory.create(
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
        return self._memory.get(memory_id)

    def remove(
        self,
        memory_id: str,
    ) -> None:
        """Permanently remove a memory entry."""
        self._memory.remove(memory_id)

    def exists(
        self,
        memory_id: str,
    ) -> bool:
        """Return whether a memory exists."""
        return self._memory.exists(memory_id)

    def search(
        self,
        keyword: str,
    ) -> list[MemoryEntry]:
        """Search stored memories."""
        return self._memory.search(keyword)

    def archive(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """Archive a memory entry."""
        return self._memory.archive(memory_id)

    def delete(
        self,
        memory_id: str,
    ) -> MemoryEntry:
        """Mark a memory entry as deleted."""
        return self._memory.delete(memory_id)

    def clear(self) -> None:
        """Remove all stored memories."""
        self._memory.clear()

    def list(self) -> list[MemoryEntry]:
        """Return all stored memory entries."""
        return self._memory.list()

    def __len__(self) -> int:
        """Return the number of stored memories."""
        return len(self._memory)

    def initialize(self) -> None:
        """
        Initialize memory resources.

        MemoryService currently owns no resources that require
        initialization, so initialization only updates lifecycle state.
        """
        with self._lock:
            if self._initialized:
                return

            self._memory.initialize()
            store = self._memory.manager.store
            if isinstance(store, PersistentMemoryStore):
                lifecycle = MemoryLifecycle(store)
                lifecycle.migrate()
                self._last_retention_removed = lifecycle.apply_retention(
                    self._retention_policy
                )

            self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down memory resources.

        Shutdown is idempotent.
        """
        with self._lock:
            if not self._initialized:
                return

            self._memory.close()
            self._initialized = False

    @property
    def retention_removed_on_last_start(self) -> int:
        """Number of records removed by retention during the last startup."""
        with self._lock:
            return self._last_retention_removed

    def health(self) -> dict[str, bool]:
        """Return memory service health information."""
        with self._lock:
            initialized = self._initialized

        return {
            "healthy": initialized,
        }