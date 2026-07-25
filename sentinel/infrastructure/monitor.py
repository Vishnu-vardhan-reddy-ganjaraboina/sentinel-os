"""
Health monitoring service for Sentinel OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


@dataclass(slots=True)
class ServiceHealth:
    """
    Represents the health information of a service.
    """

    service_name: str
    state: ServiceState
    healthy: bool
    started_at: datetime | None = None
    last_updated: datetime | None = None
    error_count: int = 0


class Monitor(Service):
    """
    Tracks the health of all registered services.
    """

    def __init__(self) -> None:
        super().__init__("monitor")
        self._services: Dict[str, ServiceHealth] = {}

    def initialize(self) -> None:
        """Initialize the monitor."""

    def shutdown(self) -> None:
        """Shutdown the monitor."""
        self._services.clear()

    def register_service(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Register a service for monitoring.
        """
        self._services[service_name] = ServiceHealth(
            service_name=service_name,
            state=state,
            healthy=True,
            started_at=datetime.now(),
            last_updated=datetime.now(),
        )

    def update_state(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Update a service state.
        """
        health = self._services[service_name]

        health.state = state
        health.last_updated = datetime.now()

    def mark_unhealthy(
        self,
        service_name: str,
    ) -> None:
        """
        Mark a service as unhealthy.
        """
        health = self._services[service_name]

        health.healthy = False
        health.error_count += 1
        health.last_updated = datetime.now()

    def mark_healthy(
        self,
        service_name: str,
    ) -> None:
        """
        Mark a service as healthy.
        """
        health = self._services[service_name]

        health.healthy = True
        health.last_updated = datetime.now()

    def get_health(
        self,
        service_name: str,
    ) -> ServiceHealth:
        """
        Return health information for a service.
        """
        return self._services[service_name]

    def get_all_health(self) -> dict[str, ServiceHealth]:
        """
        Return all monitored services.
        """
        return self._services.copy()