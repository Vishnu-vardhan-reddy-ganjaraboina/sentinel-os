from __future__ import annotations

from sentinel.kernel.event import Event
from sentinel.kernel.service import Service


class Monitor(Service):
    """
    Monitors Sentinel events and service health.

    This service subscribes to kernel lifecycle events and
    reports them. In future versions it will expose metrics,
    diagnostics, and health monitoring.
    """

    def __init__(self) -> None:
        super().__init__("Monitor")

    def start(self) -> None:
        if self.event_bus is None:
            raise RuntimeError("EventBus has not been injected.")

        self.event_bus.subscribe(
            "ServiceStarted",
            self._on_service_started,
        )

        self.event_bus.subscribe(
            "ServiceStopped",
            self._on_service_stopped,
        )

        print("Monitor initialized.")

    def stop(self) -> None:
        if self.event_bus is not None:
            self.event_bus.unsubscribe(
                "ServiceStarted",
                self._on_service_started,
            )

            self.event_bus.unsubscribe(
                "ServiceStopped",
                self._on_service_stopped,
            )

        print("Monitor stopped.")

    def _on_service_started(self, event: Event) -> None:
        service = event.payload["service"]
        print(f"[Monitor] Service started: {service}")

    def _on_service_stopped(self, event: Event) -> None:
        service = event.payload["service"]
        print(f"[Monitor] Service stopped: {service}")