"""
Thread-safe in-memory storage backend for Sentinel OS.
"""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any

from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
)
from sentinel.storage.interfaces import StorageBackend


class MemoryStorage(StorageBackend):
    """
    Thread-safe in-memory storage backend.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._lock = RLock()
        self._closed = False

    def exists(self, key: str) -> bool:
        """
        Return True if the key exists.
        """
        self._ensure_open()

        with self._lock:
            return key in self._storage

    def get(self, key: str) -> Any:
        """
        Retrieve a stored value.

        Raises:
            StorageKeyNotFoundError
        """
        self._ensure_open()

        with self._lock:
            try:
                return deepcopy(self._storage[key])
            except KeyError as exc:
                raise StorageKeyNotFoundError(key) from exc

    def set(self, key: str, value: Any) -> None:
        """
        Store a value.
        """
        self._ensure_open()

        with self._lock:
            self._storage[key] = deepcopy(value)

    def delete(self, key: str) -> None:
        """
        Delete a stored key.

        Raises:
            StorageKeyNotFoundError
        """
        self._ensure_open()

        with self._lock:
            try:
                del self._storage[key]
            except KeyError as exc:
                raise StorageKeyNotFoundError(key) from exc
    def clear(self) -> None:
        """
        Remove all stored data.
        """
        self._ensure_open()

        with self._lock:
            self._storage.clear()

    def keys(self) -> list[str]:
        """
        Return all stored keys.
        """
        self._ensure_open()

        with self._lock:
            return list(self._storage.keys())

    def close(self) -> None:
        """
        Shutdown the storage backend.

        After calling this method, all subsequent operations
        will raise StorageBackendError.
        """
        with self._lock:
            self._storage.clear()
            self._closed = True

    def __len__(self) -> int:
        """
        Return the number of stored items.
        """
        with self._lock:
            return len(self._storage)

    def _ensure_open(self) -> None:
        """
        Ensure the backend is still open.

        Raises:
            StorageBackendError:
                If the backend has already been closed.
        """
        if self._closed:
            raise StorageBackendError(
                "MemoryStorage has been closed."
            )