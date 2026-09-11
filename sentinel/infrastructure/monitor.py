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

from sentinel.infrastructure.exceptions import MonitorError
from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


@dataclass(slots=True)
class ServiceHealth:
    """
    Represents the runtime health of a service.
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
        self._initialized = False
        self._shutdown = False

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def initialize(self) -> None:
        """Initialize the monitor service."""
        with self._lock:
            if self._shutdown:
                raise MonitorError(
                    "Monitor cannot be initialized after shutdown."
                )

            if self._initialized:
                return

            self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the monitor service and clear registered services."""
        with self._lock:
            if self._shutdown:
                return

            self._services.clear()
            self._initialized = False
            self._shutdown = True

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    def register_service(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Register a service for monitoring.
        """
        self._validate_service_name(service_name)

        if not isinstance(state, ServiceState):
            raise TypeError(
                "state must be a ServiceState"
            )

        now = datetime.now(UTC)

        with self._lock:
            self._ensure_active()

            if service_name in self._services:
                raise ValueError(
                    f"Service already registered: '{service_name}'."
                )

            self._services[service_name] = ServiceHealth(
                service_name=service_name,
                state=state,
                healthy=True,
                started_at=now,
                last_updated=now,
            )

    # ------------------------------------------------------------------ #
    # State
    # ------------------------------------------------------------------ #

    def update_state(
        self,
        service_name: str,
        state: ServiceState,
    ) -> None:
        """
        Update the lifecycle state of a service.
        """
        self._validate_service_name(service_name)

        if not isinstance(state, ServiceState):
            raise TypeError(
                "state must be a ServiceState"
            )

        with self._lock:
            self._ensure_active()
            health = self._get_service(service_name)

            health.state = state
            health.last_updated = datetime.now(UTC)

    def mark_unhealthy(
        self,
        service_name: str,
    ) -> None:
        """
        Mark a service as unhealthy.
        """
        self._validate_service_name(service_name)

        with self._lock:
            self._ensure_active()
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
        """
        self._validate_service_name(service_name)

        with self._lock:
            self._ensure_active()
            health = self._get_service(service_name)

            health.healthy = True
            health.last_updated = datetime.now(UTC)

    # ------------------------------------------------------------------ #
    # Kernel synchronization
    # ------------------------------------------------------------------ #

    def sync_kernel(self, kernel: Kernel) -> None:
        """
        Synchronize monitored services with the Kernel health snapshot.

        The Kernel remains responsible for determining health.
        The Monitor stores the resulting health and lifecycle state.
        """
        if not isinstance(kernel, Kernel):
            raise TypeError(
                "kernel must be an instance of Kernel."
            )

        services = kernel.services()
        kernel_health = kernel.health()

        for service in services:
            service_health = kernel_health["services"].get(
                service.name,
                {},
            )

            is_running = kernel.running(service.name)

            state = (
                ServiceState.RUNNING
                if is_running
                else ServiceState.STOPPED
            )

            healthy = (
                is_running
                and service_health.get("healthy") is True
            )

            with self._lock:
                self._ensure_active()

                now = datetime.now(UTC)

                existing = self._services.get(service.name)

                if existing is None:
                    self._services[service.name] = ServiceHealth(
                        service_name=service.name,
                        state=state,
                        healthy=healthy,
                        started_at=now,
                        last_updated=now,
                    )
                else:
                    existing.state = state
                    existing.healthy = healthy
                    existing.last_updated = now

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def get_health(
        self,
        service_name: str,
    ) -> ServiceHealth:
        """
        Return the health information for a service.

        Read-only access remains available after shutdown so callers can
        safely inspect the final cleared state.
        """
        self._validate_service_name(service_name)

        with self._lock:
            if self._shutdown:
                raise ServiceNotFoundError(
                    f"Unknown service: '{service_name}'."
                )

            return deepcopy(
                self._get_service(service_name)
            )

    def get_all_health(self) -> dict[str, ServiceHealth]:
        """
        Return a snapshot of all monitored services.

        Read-only snapshots remain available after shutdown.
        """
        with self._lock:
            return deepcopy(self._services)

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _get_service(
        self,
        service_name: str,
    ) -> ServiceHealth:
        """
        Return a registered service.

        This method must be called while holding ``self._lock``.
        """
        try:
            return self._services[service_name]
        except KeyError as exc:
            raise ServiceNotFoundError(
                f"Unknown service: '{service_name}'."
            ) from exc

    def _ensure_active(self) -> None:
        """Ensure the monitor can accept mutating operations."""
        if self._shutdown:
            raise MonitorError(
                "Monitor has been shut down."
            )

    @staticmethod
    def _validate_service_name(
        service_name: str,
    ) -> None:
        """Validate a service name."""
        if not isinstance(service_name, str):
            raise TypeError(
                "service_name must be a string"
            )

        if not service_name.strip():
            raise ValueError(
                "service_name cannot be empty"
            )