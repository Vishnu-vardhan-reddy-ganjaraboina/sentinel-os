"""
Storage manager for Sentinel OS.
"""

from __future__ import annotations

from typing import Any

from sentinel.storage.interfaces import StorageBackend


class StorageManager:
    """
    High-level interface for Sentinel storage.

    The manager delegates all operations to the configured
    storage backend.
    """

    def __init__(self, backend: StorageBackend) -> None:
        self._backend = backend

    def connect(self) -> None:
        """Connect to the storage backend."""
        self._backend.connect()

    def disconnect(self) -> None:
        """Disconnect from the storage backend."""
        self._backend.disconnect()

    def save(self, key: str, value: Any) -> None:
        """Save a value."""
        self._backend.save(key, value)

    def load(self, key: str) -> Any:
        """Load a value."""
        return self._backend.load(key)

    def delete(self, key: str) -> None:
        """Delete a value."""
        self._backend.delete(key)

    def exists(self, key: str) -> bool:
        """Return whether a key exists."""
        return self._backend.exists(key)