"""
Interfaces for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class MemoryEntry(ABC):
    """
    Abstract interface representing a single memory entry.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique memory identifier.
        """

    @property
    @abstractmethod
    def content(self) -> Any:
        """
        Stored memory content.
        """

    @property
    @abstractmethod
    def importance(self) -> int:
        """
        Importance score.
        """

    @property
    @abstractmethod
    def expired(self) -> bool:
        """
        Whether the memory entry has expired.
        """


class Memory(ABC):
    """
    Abstract interface representing a memory store.
    """

    @abstractmethod
    def add(self, entry: MemoryEntry) -> None:
        """
        Add a memory entry.
        """

    @abstractmethod
    def get(self, memory_id: str) -> MemoryEntry:
        """
        Retrieve a memory entry.
        """

    @abstractmethod
    def remove(self, memory_id: str) -> None:
        """
        Remove a memory entry.
        """

    @abstractmethod
    def exists(self, memory_id: str) -> bool:
        """
        Check whether a memory entry exists.
        """

    @abstractmethod
    def search(self, keyword: str) -> List[MemoryEntry]:
        """
        Search memory entries.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all memory entries.
        """