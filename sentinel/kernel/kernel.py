"""
Sentinel Kernel.

Coordinates service registration, dependency resolution,
startup, and shutdown.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any, TypeVar

from sentinel.kernel.dependency_resolver import DependencyResolver
from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.exceptions import ServiceNotRunningError
from sentinel.kernel.lifecycle import LifecycleManager
from sentinel.kernel.registry import ServiceRegistry
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState

T = TypeVar("T", bound=Service)


class Kernel:
    """Central coordinator for Sentinel OS."""

    __slots__ = (
        "_registry",
        "_resolver",
        "_event_bus",
        "_lifecycle",
        "_lock",
    )

    def __init__(self) -> None:
        self._registry = ServiceRegistry()
        self._resolver = DependencyResolver()
        self._event_bus = EventBus()
        self._lifecycle = LifecycleManager(self._event_bus)
        self._lock = RLock()

    @property
    def event_bus(self) -> EventBus:
        """Expose the kernel event bus."""
        return self._event_bus

    def register(self, service: Service) -> None:
        """Register a service."""
        with self._lock:
            self._registry.register(service)

    def boot(self) -> None:
        """
        Start every registered service.

        Services are started according to their dependency graph.

        If startup fails, all services that were successfully started
        during this boot attempt are stopped in reverse order before
        the original exception is re-raised.
        """
        with self._lock:
            services = self._resolver.resolve(self._registry)
            started: list[Service] = []

            try:
                for service in services:
                    self._lifecycle.start(service)
                    started.append(service)

            except Exception:
                for service in reversed(started):
                    try:
                        self._lifecycle.stop(service)
                    except Exception:
                        pass
                raise

    def shutdown(self) -> None:
        """
        Stop every registered service.

        Shutdown happens in reverse dependency order.
        """
        with self._lock:
            services = self._resolver.resolve(self._registry)
            first_error: Exception | None = None

            for service in reversed(services):
                try:
                    self._lifecycle.stop(service)
                except ServiceNotRunningError:
                    continue
                except Exception as exc:
                    if first_error is None:
                        first_error = exc

            if first_error is not None:
                raise first_error

    def start(self, name: str) -> None:
        """
        Start a single service and any dependencies it requires.

        Dependencies are started first and already-running dependencies
        are left untouched.

        Services unrelated to the requested service are not started.

        If startup fails, services started during this operation are
        rolled back in reverse order.
        """
        with self._lock:
            target = self._registry.get(name)

            dependency_names = self._dependency_closure(target)

            ordered_services = self._resolver.resolve(self._registry)
            services_to_start = [
                service
                for service in ordered_services
                if service.name in dependency_names
            ]

            started: list[Service] = []

            try:
                for service in services_to_start:
                    if self._lifecycle.is_running(service):
                        continue

                    self._lifecycle.start(service)
                    started.append(service)

            except Exception:
                for service in reversed(started):
                    try:
                        self._lifecycle.stop(service)
                    except Exception:
                        pass
                raise

    def stop(self, name: str) -> None:
        """
        Stop a single service.

        Dependents are not stopped automatically.
        """
        with self._lock:
            service = self._registry.get(name)
            self._lifecycle.stop(service)

    def restart(self, name: str) -> None:
        """
        Restart a single service.

        The service is stopped first and then started again.
        Required dependencies are ensured before startup.
        """
        with self._lock:
            service = self._registry.get(name)

            self._lifecycle.stop(service)

            dependency_names = self._dependency_closure(service)
            ordered_services = self._resolver.resolve(self._registry)

            services_to_start = [
                item
                for item in ordered_services
                if item.name in dependency_names
            ]

            for item in services_to_start:
                if self._lifecycle.is_running(item):
                    continue

                self._lifecycle.start(item)

    def state(self, name: str) -> ServiceState:
        """Return the current lifecycle state of a service."""
        with self._lock:
            service = self._registry.get(name)
            return self._lifecycle.state(service)

    def get(self, name: str) -> Service:
        """Return a registered service."""
        with self._lock:
            return self._registry.get(name)

    def get_typed(self, name: str, service_type: type[T]) -> T:
        service = self.get(name)

        if not isinstance(service, service_type):
            raise TypeError(
                f"Service '{name}' is not an instance of "
                f"{service_type.__name__}."
            )

        return service

    def running(self, name: str) -> bool:
        """Return True if a service is running."""
        with self._lock:
            return self._lifecycle.is_running(
                self._registry.get(name)
            )

    def services(self) -> tuple[Service, ...]:
        """Return registered services."""
        with self._lock:
            return self._registry.services()

    def health(self) -> Mapping[str, Any]:
        """
        Return system-wide health information.

        A service contributes to overall system health only when:
            1. The service is running.
            2. Its own health report is healthy.

        Individual service health reports are preserved even when the
        service is not currently running.
        """
        services = self.services()
        service_health: dict[str, Mapping[str, Any]] = {}
        overall_healthy = bool(services)

        for service in services:
            try:
                health = service.health()

                if not isinstance(health, Mapping):
                    health = {
                        "healthy": False,
                        "error": "Service health result is invalid.",
                    }

                service_health[service.name] = dict(health)

                is_running = self._lifecycle.is_running(service)
                reports_healthy = health.get("healthy") is True

                if not is_running or not reports_healthy:
                    overall_healthy = False

            except Exception as exc:
                service_health[service.name] = {
                    "healthy": False,
                    "error": str(exc),
                }
                overall_healthy = False

        return {
            "healthy": overall_healthy,
            "services": service_health,
        }

    def __len__(self) -> int:
        with self._lock:
            return len(self._registry)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(services={len(self)})"
        )

    def _dependency_closure(self, service: Service) -> set[str]:
        """
        Return the requested service and all of its dependencies.

        Dependencies are resolved recursively through the registered
        service graph.
        """
        required: set[str] = set()
        pending = [service]

        while pending:
            current = pending.pop()

            if current.name in required:
                continue

            required.add(current.name)

            for dependency_name in current.dependencies:
                dependency = self._registry.get(dependency_name)
                pending.append(dependency)

        return required