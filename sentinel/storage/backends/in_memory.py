"""
In-memory storage backend for Sentinel OS.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sentinel.storage.exceptions import StorageKeyNotFoundError
from sentinel.storage.interfaces import StorageBackend


class MemoryBackend(StorageBackend):
    """
    In-memory implementation of StorageBackend.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._connected = False


    def connect(self) -> None:
         """
         Initialize the backend.
         """
         self._connected = True


    def disconnect(self) -> None:
        """
        Disconnect the backend.
        """
        self.close()

    def exists(self, key: str) -> bool:
        return key in self._storage

    def get(self, key: str) -> Any:
        if key not in self._storage:
            raise StorageKeyNotFoundError(
                f"Key '{key}' does not exist."
            )

        return deepcopy(self._storage[key])

    def set(self, key: str, value: Any) -> None:
        self._storage[key] = deepcopy(value)

    def delete(self, key: str) -> None:
        self._storage.pop(key, None)

    def clear(self) -> None:
        self._storage.clear()

    def keys(self) -> list[str]:
        return list(self._storage.keys())

    def close(self) -> None:
        self.clear()

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError(
                "MemoryBackend is not connected."
           )
        
    def save(self, key: str, value: Any) -> None:
        """
        Backward-compatible alias for set().
        """
        self.set(key, value)


    def load(self, key: str) -> Any:
        """
        Backward-compatible alias for get().
        """
        return self.get(key)