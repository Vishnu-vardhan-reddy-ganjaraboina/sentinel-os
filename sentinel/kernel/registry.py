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
from threading import RLock

from sentinel.kernel.exceptions import (
    DuplicateServiceError,
    ServiceNotFoundError,
)
from sentinel.kernel.service import Service


class ServiceRegistry:
    """Thread-safe registry of Sentinel services."""

    __slots__ = (
        "_services",
        "_lock",
    )

    def __init__(self) -> None:
        self._services: dict[str, Service] = {}
        self._lock = RLock()

    def register(self, service: Service) -> None:
        """Register a service."""
        if not isinstance(service, Service):
            raise TypeError("service must be an instance of Service.")

        with self._lock:
            if service.name in self._services:
                raise DuplicateServiceError(
                    f"Service '{service.name}' is already registered."
                )

            self._services[service.name] = service

    def unregister(self, name: str) -> None:
        """Remove a registered service."""
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")

        with self._lock:
            try:
                del self._services[name]
            except KeyError as exc:
                raise ServiceNotFoundError(
                    f"Service '{name}' is not registered."
                ) from exc

    def get(self, name: str) -> Service:
        """Return a registered service."""
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")

        with self._lock:
            try:
                return self._services[name]
            except KeyError as exc:
                raise ServiceNotFoundError(
                    f"Service '{name}' is not registered."
                ) from exc

    def exists(self, name: str) -> bool:
        """Return True if the service exists."""
        if not isinstance(name, str) or not name:
            return False

        with self._lock:
            return name in self._services

    def services(self) -> tuple[Service, ...]:
        """Return an immutable snapshot of registered services."""
        with self._lock:
            return tuple(self._services.values())

    def clear(self) -> None:
        """Remove all registered services."""
        with self._lock:
            self._services.clear()

    def __contains__(self, name: object) -> bool:
        """Support ``name in registry``."""
        if not isinstance(name, str):
            return False

        with self._lock:
            return name in self._services

    def __len__(self) -> int:
        """Return the number of registered services."""
        with self._lock:
            return len(self._services)

    def __iter__(self) -> Iterator[Service]:
        """
        Iterate over a snapshot of registered services.

        Returning an iterator over a copied tuple prevents callers
        from observing dictionary mutation during iteration.
        """
        with self._lock:
            snapshot = tuple(self._services.values())

        return iter(snapshot)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"{self.__class__.__name__}"
            f"(services={len(self)})"
        )