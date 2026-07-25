"""
Service registry for Sentinel OS.

Stores and manages registered services.

Responsibilities:
    - Register services
    - Remove services
    - Retrieve services

Non-responsibilities:
    - Lifecycle management
    - Dependency resolution
    - Event publishing
"""

from __future__ import annotations

from collections.abc import Iterator

from sentinel.kernel.exceptions import (
    DuplicateServiceError,
    ServiceNotFoundError,
)
from sentinel.kernel.service import Service


class ServiceRegistry:
    """Stores registered services."""

    __slots__ = ("_services",)

    def __init__(self) -> None:
        self._services: dict[str, Service] = {}

    def register(self, service: Service) -> None:
        """
        Register a service.

        Raises:
            DuplicateServiceError:
                If a service with the same name already exists.
        """
        if service.name in self._services:
            raise DuplicateServiceError(
                f"Service '{service.name}' is already registered."
            )

        self._services[service.name] = service

    def unregister(self, name: str) -> None:
        """
        Remove a service.

        Raises:
            ServiceNotFoundError:
                If the service is not registered.
        """
        try:
            del self._services[name]
        except KeyError as exc:
            raise ServiceNotFoundError(
                f"Service '{name}' is not registered."
            ) from exc

    def get(self, name: str) -> Service:
        """
        Return a registered service.

        Raises:
            ServiceNotFoundError:
                If the service does not exist.
        """
        try:
            return self._services[name]
        except KeyError as exc:
            raise ServiceNotFoundError(
                f"Service '{name}' is not registered."
            ) from exc

    def exists(self, name: str) -> bool:
        """Return True if the service exists."""
        return name in self._services

    def services(self) -> tuple[Service, ...]:
        """Return all registered services."""
        return tuple(self._services.values())

    def clear(self) -> None:
        """Remove all registered services."""
        self._services.clear()

    def __contains__(self, name: object) -> bool:
        """Support 'name in registry'."""
        return isinstance(name, str) and name in self._services

    def __len__(self) -> int:
        """Return the number of registered services."""
        return len(self._services)

    def __iter__(self) -> Iterator[Service]:
        """Iterate over registered services."""
        return iter(self._services.values())

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"{self.__class__.__name__}"
            f"(services={len(self)})"
        )