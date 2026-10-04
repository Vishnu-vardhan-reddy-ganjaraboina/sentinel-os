"""
Thread-safe in-memory storage backend for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
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
        - Atomic transaction support.
    """

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._lock = RLock()
        self._closed = False

    def connect(self) -> None:
        """
        Open the backend.

        Reconnecting after close starts with an empty store because
        close/disconnect intentionally clears in-memory data.
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
        """Return whether a key exists."""
        self._validate_key(key)
        self._ensure_open()

        with self._lock:
            return key in self._storage

    def get(self, key: str) -> Any:
        """
        Retrieve a value.

        Returns a defensive copy.
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

        Values are deep-copied before storage.
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
        """Remove all stored values."""
        self._ensure_open()

        with self._lock:
            self._storage.clear()

    def keys(self) -> list[str]:
        """Return all stored keys."""
        self._ensure_open()

        with self._lock:
            return list(self._storage.keys())

    @contextmanager
    def atomic(self) -> Iterator[None]:
        """
        Execute operations atomically.

        The entire transaction holds the backend lock, preventing another
        thread from observing an intermediate state.

        A deep snapshot is retained for rollback.
        """
        with self._lock:
            self._ensure_open()

            snapshot = deepcopy(self._storage)

            try:
                yield
            except BaseException:
                self._storage = snapshot
                raise

    def close(self) -> None:
        """Close the backend."""
        self.disconnect()

    def save(self, key: str, value: Any) -> None:
        """Backward-compatible alias for set()."""
        self.set(key, value)

    def load(self, key: str) -> Any:
        """Backward-compatible alias for get()."""
        return self.get(key)

    def __len__(self) -> int:
        """Return the number of stored values."""
        with self._lock:
            return len(self._storage)

    def _ensure_open(self) -> None:
        if self._closed:
            raise StorageBackendError(
                "MemoryBackend has been closed."
            )

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise ValueError(
                "Storage key must be a string."
            )

        if not key:
            raise ValueError(
                "Storage key cannot be empty."
            )