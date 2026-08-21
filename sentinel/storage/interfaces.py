"""
Storage interfaces for Sentinel OS.

Defines the contract implemented by all storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """
    Abstract storage backend.

    Backends provide persistent or ephemeral key-value storage.

    Lifecycle methods (`connect` and `disconnect`) have safe default
    implementations so lightweight backends do not need to implement
    meaningless lifecycle methods. Resource-backed implementations such
    as SQLite may override them.
    """

    def connect(self) -> None:
        """
        Initialize the backend and make it ready for operations.

        Backends that do not require an explicit connection may use
        this default no-op implementation.
        """
        return None

    def disconnect(self) -> None:
        """
        Release backend resources.

        Backends that do not own external resources may use this
        default no-op implementation.
        """
        return None

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Return whether a key exists.
        """
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
        """
        Store or replace a value.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a key.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all stored values.
        """
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> list[str]:
        """
        Return all stored keys.
        """
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