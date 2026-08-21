"""
Thread-safe in-memory storage backend for Sentinel OS.

This module provides the low-level in-memory implementation of the
StorageBackend contract.
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


class MemoryBackend(StorageBackend):
    """
    Thread-safe in-memory storage backend.

    Characteristics:
        - Thread-safe operations.
        - Deep-copy protection on reads and writes.
        - Explicit lifecycle management.
        - Deterministic error handling after close.
        - No external resources.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._lock = RLock()
        self._closed = False

    def connect(self) -> None:
        """
        Open the backend.

        A MemoryBackend can be reconnected after being closed.
        Reconnecting starts with an empty store because close()
        intentionally clears all in-memory data.
        """
        with self._lock:
            self._closed = False

    def disconnect(self) -> None:
        """
        Close the backend and clear all stored data.
        """
        with self._lock:
            self._storage.clear()
            self._closed = True

    def exists(self, key: str) -> bool:
        """
        Return whether a key exists.
        """
        self._validate_key(key)
        self._ensure_open()

        with self._lock:
            return key in self._storage

    def get(self, key: str) -> Any:
        """
        Retrieve a value.

        Raises:
            ValueError:
                If the key is invalid.
            StorageBackendError:
                If the backend is closed.
            StorageKeyNotFoundError:
                If the key does not exist.
        """
        self._validate_key(key)
        self._ensure_open()

        with self._lock:
            try:
                value = self._storage[key]
            except KeyError as exc:
                raise StorageKeyNotFoundError(
                    f"Key '{key}' does not exist."
                ) from exc

            return deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        """
        Store or replace a value.

        Values are deep-copied before storage to prevent callers
        from mutating internal state.
        """
        self._validate_key(key)
        self._ensure_open()

        copied_value = deepcopy(value)

        with self._lock:
            self._storage[key] = copied_value

    def delete(self, key: str) -> None:
        """
        Delete a key.

        Raises:
            ValueError:
                If the key is invalid.
            StorageBackendError:
                If the backend is closed.
            StorageKeyNotFoundError:
                If the key does not exist.
        """
        self._validate_key(key)
        self._ensure_open()

        with self._lock:
            if key not in self._storage:
                raise StorageKeyNotFoundError(
                    f"Key '{key}' does not exist."
                )

            del self._storage[key]

    def clear(self) -> None:
        """
        Remove all stored values.
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
        Close the backend.

        Closing clears all in-memory data. Any subsequent
        operation fails with StorageBackendError.
        """
        self.disconnect()

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

    def __len__(self) -> int:
        """
        Return the number of stored values.
        """
        with self._lock:
            return len(self._storage)

    def _ensure_open(self) -> None:
        """
        Ensure the backend is available.
        """
        if self._closed:
            raise StorageBackendError(
                "MemoryBackend has been closed."
            )

    @staticmethod
    def _validate_key(key: str) -> None:
        """
        Validate a storage key.
        """
        if not isinstance(key, str):
            raise ValueError(
                "Storage key must be a string."
            )

        if not key:
            raise ValueError(
                "Storage key cannot be empty."
            )