"""
In-memory storage backend for Sentinel OS.
"""

from __future__ import annotations

from typing import Any

from sentinel.storage.exceptions import StorageConnectionError
from sentinel.storage.interfaces import StorageBackend


class MemoryBackend(StorageBackend):
    """
    In-memory implementation of StorageBackend.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._storage.clear()
        self._connected = False

    def _require_connection(self) -> None:
        if not self._connected:
            raise StorageConnectionError(
                "Memory backend is not connected."
            )

    def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        self._require_connection()
        self._storage[key] = value

    def load(
        self,
        key: str,
    ) -> Any:
        self._require_connection()
        return self._storage.get(key)

    def delete(
        self,
        key: str,
    ) -> None:
        self._require_connection()
        self._storage.pop(key, None)

    def exists(
        self,
        key: str,
    ) -> bool:
        self._require_connection()
        return key in self._storage