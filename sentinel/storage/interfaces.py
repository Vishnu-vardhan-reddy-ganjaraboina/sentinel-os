"""
Storage interfaces for Sentinel OS.

Defines abstract contracts for all storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """
    Base interface for all storage implementations.
    """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Return True if the key exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Any:
        """
        Retrieve a value.

        Raises:
            StorageKeyNotFoundError
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Store a value.
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
        Remove all stored data.
        """
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> list[str]:
        """
        Return all keys.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Shutdown the backend.
        """
        raise NotImplementedError