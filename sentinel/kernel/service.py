"""
Base Service abstraction for Sentinel OS.

Every executable capability inside Sentinel OS derives from Service.

Responsibilities:
    - Identity
    - Dependency declaration
    - Initialization
    - Shutdown
    - Health reporting

Non-responsibilities:
    - Lifecycle management
    - State transitions
    - Dependency resolution
    - Event publishing
    - Logging
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class Service(ABC):
    """Abstract base class for all Sentinel services."""

    __slots__ = ("_name", "_dependencies")

    def __init__(
        self,
        name: str,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        """
        Initialize a service.

        Args:
            name:
                Unique service name.

            dependencies:
                Names of services that must be initialized first.

        Raises:
            ValueError:
                If the service name is empty.
        """
        name = name.strip()

        if not name:
            raise ValueError("Service name cannot be empty.")

        self._name = name
        self._dependencies = tuple(dependencies)

    @property
    def name(self) -> str:
        """Return the unique service name."""
        return self._name

    @property
    def dependencies(self) -> tuple[str, ...]:
        """Return immutable dependency names."""
        return self._dependencies

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the service.

        Called exactly once by the LifecycleManager.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        """
        Shut down the service gracefully.
        """
        raise NotImplementedError

    def health(self) -> Mapping[str, Any]:
        """
        Return health information.

        Subclasses may override this to provide richer diagnostics.
        """
        return {
            "healthy": True,
        }

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"{self.__class__.__name__}"
            f"(name={self._name!r})"
        )