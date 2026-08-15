"""
Interfaces for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sentinel.memory.constants import MemoryStatus, MemoryType


class MemoryEntry(ABC):
    """
    Abstract interface representing a single memory entry.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Return the unique memory identifier."""

    @property
    @abstractmethod
    def content(self) -> Any:
        """Return the stored memory content."""

    @property
    @abstractmethod
    def importance(self) -> int:
        """Return the memory importance."""

    @property
    @abstractmethod
    def memory_type(self) -> MemoryType:
        """Return the memory type."""

    @property
    @abstractmethod
    def status(self) -> MemoryStatus:
        """Return the memory status."""

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Return the creation timestamp."""

    @property
    @abstractmethod
    def last_accessed(self) -> datetime:
        """Return the last-access timestamp."""

    @property
    @abstractmethod
    def expired(self) -> bool:
        """Return whether the memory has expired."""

    @abstractmethod
    def touch(self) -> None:
        """Update the last-access timestamp."""

    @abstractmethod
    def archive(self) -> None:
        """Archive the memory."""

    @abstractmethod
    def delete(self) -> None:
        """Delete the memory."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the memory entry."""


class Memory(ABC):
    """
    Abstract interface for memory storage.
    """

    @abstractmethod
    def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry."""

    @abstractmethod
    def get(self, memory_id: str) -> MemoryEntry:
        """Retrieve a memory entry."""

    @abstractmethod
    def remove(self, memory_id: str) -> None:
        """Remove a memory entry."""

    @abstractmethod
    def exists(self, memory_id: str) -> bool:
        """Return whether a memory exists."""

    @abstractmethod
    def search(self, keyword: str) -> list[MemoryEntry]:
        """Search memory entries."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all memory entries."""

    @abstractmethod
    def list(self) -> list[MemoryEntry]:
        """Return all memory entries."""
