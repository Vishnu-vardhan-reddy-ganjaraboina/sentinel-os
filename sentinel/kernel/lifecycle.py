"""
Lifecycle management for Sentinel OS.
"""

from __future__ import annotations

from sentinel.kernel.event import Event
from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.exceptions import (
    ServiceAlreadyRunningError,
    ServiceNotRunningError,
)
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


class LifecycleManager:
    """
    Manages service lifecycle.
    """

    __slots__ = (
        "_states",
        "_event_bus",
    )

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._states: dict[str, ServiceState] = {}

    def state(
        self,
        service: Service,
    ) -> ServiceState:
        """
        Return current service state.
        """
        return self._states.get(
            service.name,
            ServiceState.CREATED,
        )

    def is_running(
        self,
        service: Service,
    ) -> bool:
        return (
            self.state(service)
            is ServiceState.RUNNING
        )

    def start(
        self,
        service: Service,
    ) -> None:
        """
        Start a service.
        """

        if self.is_running(service):
            raise ServiceAlreadyRunningError(
                f"{service.name} is already running."
            )

        self._states[service.name] = (
            ServiceState.STARTING
        )

        try:
            service.initialize()

            self._states[service.name] = (
                ServiceState.RUNNING
            )

            self._event_bus.publish(
                Event(
                    name="ServiceStarted",
                    source=service.name,
                )
            )

        except Exception:
            self._states[service.name] = (
                ServiceState.FAILED
            )
            raise

    def stop(
        self,
        service: Service,
    ) -> None:
        """
        Stop a service.
        """

        if not self.is_running(service):
            raise ServiceNotRunningError(
                f"{service.name} is not running."
            )

        self._states[service.name] = (
            ServiceState.STOPPING
        )

        try:
            service.shutdown()

            self._states[service.name] = (
                ServiceState.STOPPED
            )

            self._event_bus.publish(
                Event(
                    name="ServiceStopped",
                    source=service.name,
                )
            )

        except Exception:
            self._states[service.name] = (
                ServiceState.FAILED
            )
            raise