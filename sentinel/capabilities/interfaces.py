"""
Interfaces for the Capabilities subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Capability(ABC):
    """
    Abstract base class for all Sentinel capabilities.

    A capability represents a unit of functionality that can be
    registered, discovered, and executed by the Capabilities subsystem.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique identifier of the capability.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description.
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Capability version.
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Whether the capability is enabled.
        """

    @abstractmethod
    def enable(self) -> None:
        """
        Enable the capability.
        """

    @abstractmethod
    def disable(self) -> None:
        """
        Disable the capability.
        """

    @abstractmethod
    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the capability.
        """