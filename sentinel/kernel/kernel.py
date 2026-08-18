"""
Sentinel Kernel.

Coordinates service registration, dependency resolution,
startup, and shutdown.
"""

from __future__ import annotations

from typing import TypeVar

from sentinel.kernel.dependency_resolver import DependencyResolver
from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.lifecycle import LifecycleManager
from sentinel.kernel.registry import ServiceRegistry
from sentinel.kernel.service import Service

T = TypeVar("T", bound=Service)


class Kernel:
    """Central coordinator for Sentinel OS."""

    __slots__ = (
        "_registry",
        "_resolver",
        "_event_bus",
        "_lifecycle",
    )

    def __init__(self) -> None:
        self._registry = ServiceRegistry()
        self._resolver = DependencyResolver()
        self._event_bus = EventBus()
        self._lifecycle = LifecycleManager(
            self._event_bus
        )

    @property
    def event_bus(self) -> EventBus:
        """Expose the kernel event bus."""
        return self._event_bus

    def register(
        self,
        service: Service,
    ) -> None:
        """Register a service."""
        self._registry.register(service)

    def boot(self) -> None:
        """
        Start every registered service.

        Services are started according to their
        dependency graph.
        """
        services = self._resolver.resolve(
            self._registry
        )

        for service in services:
            self._lifecycle.start(service)

    def shutdown(self) -> None:
        """
        Stop every registered service.

        Shutdown happens in reverse dependency order.
        """
        services = self._resolver.resolve(
            self._registry
        )

        for service in reversed(services):
            self._lifecycle.stop(service)

    def get(
        self,
        name: str,
    ) -> Service:
        """Return a registered service."""
        return self._registry.get(name)

    def get_typed(
        self,
        name: str,
        service_type: type[T],
    ) -> T:
        """
        Return a registered service validated against the expected type.

        Raises:
            TypeError:
                If the registered service is not an instance of
                the requested service type.
        """
        service = self.get(name)

        if not isinstance(service, service_type):
            raise TypeError(
                f"Service '{name}' is not an instance of "
                f"{service_type.__name__}."
            )

        return service

    def running(
        self,
        name: str,
    ) -> bool:
        """Return True if a service is running."""
        return self._lifecycle.is_running(
            self.get(name)
        )

    def services(self) -> tuple[Service, ...]:
        """Return registered services."""
        return self._registry.services()

    def __len__(self) -> int:
        return len(self._registry)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(services={len(self)})"
        )