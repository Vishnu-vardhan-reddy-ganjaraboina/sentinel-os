"""
Storage interfaces for Sentinel OS.

Defines the contract implemented by all storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class StorageBackend(ABC):
    """
    Abstract key-value storage backend.

    Implementations provide thread-safe key-value storage and may optionally
    support atomic multi-operation transactions.

    ``atomic()`` is intentionally a capability rather than an abstract
    requirement so existing third-party/custom backends remain compatible.
    """

    def connect(self) -> None:
        """
        Initialize the backend.

        Backends that do not require explicit connection may use this
        default no-op implementation.
        """
        return None

    def disconnect(self) -> None:
        """
        Release backend resources.

        Backends without external resources may use this default
        no-op implementation.
        """
        return None

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether a key exists."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Any:
        """
        Retrieve a value.

        Raises:
            StorageKeyNotFoundError:
                If the key does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store or replace a value."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored values."""
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> list[str]:
        """Return all stored keys."""
        raise NotImplementedError

    def close(self) -> None:
        """
        Backward-compatible alias for disconnect().
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

    @contextmanager
    def atomic(self) -> Iterator[None]:
        """
        Execute a group of storage operations atomically.

        Backends that support transactional multi-operation updates override
        this method.

        A backend without transaction support must not silently pretend that
        operations are atomic.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support atomic transactions."
        )
        yield