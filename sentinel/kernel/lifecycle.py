"""
Lifecycle management for Sentinel OS.
"""

from __future__ import annotations

from threading import RLock

from sentinel.kernel.event import Event
from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.exceptions import (
    ServiceAlreadyRunningError,
    ServiceNotRunningError,
)
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


class LifecycleManager:
    """Thread-safe manager for service lifecycle state."""

    __slots__ = (
        "_states",
        "_event_bus",
        "_lock",
    )

    def __init__(self, event_bus: EventBus) -> None:
        if not isinstance(event_bus, EventBus):
            raise TypeError("event_bus must be an EventBus.")

        self._event_bus = event_bus
        self._states: dict[str, ServiceState] = {}
        self._lock = RLock()

    def state(
        self,
        service: Service,
    ) -> ServiceState:
        """Return the current service state."""
        if not isinstance(service, Service):
            raise TypeError("service must be an instance of Service.")

        with self._lock:
            return self._states.get(
                service.name,
                ServiceState.CREATED,
            )

    def is_running(
        self,
        service: Service,
    ) -> bool:
        """Return True if the service is running."""
        return self.state(service) is ServiceState.RUNNING

    def start(
        self,
        service: Service,
    ) -> None:
        """
        Start a service.

        State transitions are protected by a lock, while the
        service's own initialization runs outside the lock.
        """
        if not isinstance(service, Service):
            raise TypeError("service must be an instance of Service.")

        with self._lock:
            current_state = self._states.get(
                service.name,
                ServiceState.CREATED,
            )

            if current_state is ServiceState.RUNNING:
                raise ServiceAlreadyRunningError(
                    f"{service.name} is already running."
                )

            if current_state is ServiceState.STARTING:
                raise ServiceAlreadyRunningError(
                    f"{service.name} is already starting."
                )

            self._states[service.name] = ServiceState.STARTING

        try:
            service.initialize()

        except Exception:
            with self._lock:
                self._states[service.name] = ServiceState.FAILED
            raise

        with self._lock:
            self._states[service.name] = ServiceState.RUNNING

        self._event_bus.publish(
            Event(
                name="ServiceStarted",
                source=service.name,
            )
        )

    def stop(
        self,
        service: Service,
    ) -> None:
        """
        Stop a service.

        State transitions are protected by a lock, while the
        service's own shutdown runs outside the lock.
        """
        if not isinstance(service, Service):
            raise TypeError("service must be an instance of Service.")

        with self._lock:
            current_state = self._states.get(
                service.name,
                ServiceState.CREATED,
            )

            if current_state is not ServiceState.RUNNING:
                raise ServiceNotRunningError(
                    f"{service.name} is not running."
                )

            self._states[service.name] = ServiceState.STOPPING

        try:
            service.shutdown()

        except Exception:
            with self._lock:
                self._states[service.name] = ServiceState.FAILED
            raise

        with self._lock:
            self._states[service.name] = ServiceState.STOPPED

        self._event_bus.publish(
            Event(
                name="ServiceStopped",
                source=service.name,
            )
        )