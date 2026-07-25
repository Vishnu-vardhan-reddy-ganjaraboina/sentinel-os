"""
Storage interface definitions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the backend."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the backend."""

    @abstractmethod
    def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Save data."""

    @abstractmethod
    def load(
        self,
        key: str,
    ) -> Any:
        """Load data."""

    @abstractmethod
    def delete(
        self,
        key: str,
    ) -> None:
        """Delete data."""

    @abstractmethod
    def exists(
        self,
        key: str,
    ) -> bool:
        """Return whether the key exists."""