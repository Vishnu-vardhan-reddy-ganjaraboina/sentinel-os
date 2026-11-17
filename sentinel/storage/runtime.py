"""
Lifecycle-managed storage service for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sentinel.kernel.service import Service
from sentinel.storage.backends.filesystem import FilesystemBackend
from sentinel.storage.backends.in_memory import MemoryBackend
from sentinel.storage.backends.sqlite import SQLiteBackend
from sentinel.storage.interfaces import StorageBackend
from sentinel.storage.manager import StorageManager


class StorageRuntimeService(Service):
    """Own the configured storage backend during the application lifecycle."""

    def __init__(
        self,
        *,
        backend: str = "memory",
        database: str | Path = "data/sentinel.db",
        directory: str | Path = "data/storage",
    ) -> None:
        super().__init__("storage")
        self._backend_name = backend.strip().lower()
        self._database = Path(database)
        self._directory = Path(directory)
        self._manager: StorageManager | None = None

    @property
    def storage(self) -> StorageManager:
        """Return the initialized storage manager."""
        if self._manager is None:
            raise RuntimeError("Storage service is not initialized.")
        return self._manager

    def initialize(self) -> None:
        """Create and connect the configured backend."""
        if self._manager is not None:
            return

        backend: StorageBackend
        if self._backend_name == "sqlite":
            backend = SQLiteBackend(self._database)
        elif self._backend_name == "filesystem":
            backend = FilesystemBackend(self._directory)
        elif self._backend_name == "memory":
            backend = MemoryBackend()
        else:
            raise ValueError(
                f"Unsupported storage backend: '{self._backend_name}'."
            )

        manager = StorageManager(backend)
        try:
            manager.connect()
        except Exception:
            backend.disconnect()
            raise

        self._manager = manager

    def shutdown(self) -> None:
        """Disconnect storage and release the manager."""
        manager = self._manager
        if manager is None:
            return

        manager.disconnect()
        self._manager = None

    def health(self) -> Mapping[str, Any]:
        """Report whether the storage service is initialized."""
        return {
            "healthy": self._manager is not None,
            "backend": self._backend_name,
        }
