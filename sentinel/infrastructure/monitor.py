"""
Health monitoring service for Sentinel OS.

This module provides a centralized health monitor responsible for tracking
the runtime state of registered services.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


@dataclass(slots=True)
class ServiceHealth:
    """
    Represents the runtime health of a service.

    Attributes:
        service_name:
            Name of the monitored service.

        state:
            Current lifecycle state.

        healthy:
            Health status.

        started_at:
            Time when monitoring began.

        last_updated:
            Last modification timestamp.

        error_count:
            Number of times the service has been marked unhealthy.
    """

    service_name: str
    state: ServiceState
    healthy: bool
    started_at: datetime
    last_updated: datetime
    error_count: int = 0


class Monitor(Service):
    """
    Monitor the health of registered Sentinel services.

    This class is responsible only for storing and updating service
    health information. It does not perform health checks itself.
    """

    def __init__(self) -> None:
        """Initialize the monitor service."""
        super().__init__("monitor")

        self._services: dict[str, ServiceHealth] = {}
        self._lock = RLock()

    def initialize(self) -> None:
        """Initialize the monitor service."""

    def shutdown(self) -> None:
        """Shutdown the monitor service."""
        with self._lock:
            self._services.clear()

    def register_service(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Register a service for monitoring.

        Args:
            service_name:
                Name of the service.

            state:
                Initial lifecycle state.
        """
        now = datetime.now(UTC)

        with self._lock:
            self._services[service_name] = ServiceHealth(
                service_name=service_name,
                state=state,
                healthy=True,
                started_at=now,
                last_updated=now,
            )

    def update_state(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Update the lifecycle state of a service.

        Args:
            service_name:
                Registered service name.

            state:
                New lifecycle state.

        Raises:
            ServiceNotFoundError:
                If the service has not been registered.
        """
        with self._lock:
            health = self._get_service(service_name)

            health.state = state
            health.last_updated = datetime.now(UTC)

    def mark_unhealthy(
        self,
        service_name: str,
    ) -> None:
        """
        Mark a service as unhealthy.

        Args:
            service_name:
                Registered service name.
        """
        with self._lock:
            health = self._get_service(service_name)

            health.healthy = False
            health.error_count += 1
            health.last_updated = datetime.now(UTC)

    def mark_healthy(
        self,
        service_name: str,
    ) -> None:
        """
        Mark a service as healthy.

        Args:
            service_name:
                Registered service name.
        """
        with self._lock:
            health = self._get_service(service_name)

            health.healthy = True
            health.last_updated = datetime.now(UTC)

    def get_health(
        self,
        service_name: str,
    ) -> ServiceHealth:
        """
        Return the health information for a service.

        Args:
            service_name:
                Registered service name.

        Returns:
            ServiceHealth instance.

        Raises:
            ServiceNotFoundError:
                If the service is unknown.
        """
        with self._lock:
            return deepcopy(self._get_service(service_name))

    def get_all_health(self) -> dict[str, ServiceHealth]:
        """
        Return a snapshot of all monitored services.

        Returns:
            Dictionary mapping service names to health information.
        """
        with self._lock:
            return deepcopy(self._services)

    def _get_service(
        self,
        service_name: str,
    ) -> ServiceHealth:
        """
        Return a registered service.

        Args:
            service_name:
                Registered service name.

        Returns:
            ServiceHealth instance.

        Raises:
            ServiceNotFoundError:
                If the service has not been registered.
        """
        try:
            return self._services[service_name]
        except KeyError as exc:
            raise ServiceNotFoundError(
                f"Unknown service: '{service_name}'."
            ) from exc