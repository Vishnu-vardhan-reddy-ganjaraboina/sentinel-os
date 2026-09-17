"""
Long-running process host for Sentinel OS.
"""

from __future__ import annotations

from threading import Event, RLock
from typing import Any

from sentinel.boot.manager import BootManager
from sentinel.boot.result import BootResult
from sentinel.control.endpoint import (
    ControlEndpoint,
    ControlEndpointRegistry,
)
from sentinel.control.server import ControlServer
from sentinel.process.exceptions import (
    ProcessShutdownError,
    ProcessStartupError,
    ProcessStateError,
)
from sentinel.process.state import ProcessState


class ProcessHost:
    """
    Keep a running Sentinel OS instance alive inside a process.

    ProcessHost owns process lifetime.
    BootManager owns Sentinel OS lifecycle.
    ControlServer owns the local control endpoint.
    ControlEndpointRegistry publishes endpoint metadata.

    Lifecycle:

        STOPPED -> STARTING -> RUNNING -> STOPPING -> STOPPED

    A startup failure returns to STOPPED.

    A shutdown failure enters FAILED.
    """

    def __init__(
        self,
        boot_manager: BootManager,
        *,
        control_host: str = "127.0.0.1",
        control_port: int = 0,
        endpoint_registry: ControlEndpointRegistry | None = None,
    ) -> None:
        if not isinstance(
            boot_manager,
            BootManager,
        ):
            raise TypeError(
                "boot_manager must be a BootManager instance."
            )

        if not isinstance(control_host, str):
            raise TypeError(
                "control_host must be a string."
            )

        if not isinstance(control_port, int):
            raise TypeError(
                "control_port must be an integer."
            )

        if endpoint_registry is not None and not isinstance(
            endpoint_registry,
            ControlEndpointRegistry,
        ):
            raise TypeError(
                "endpoint_registry must be a "
                "ControlEndpointRegistry instance."
            )

        self._boot_manager = boot_manager

        self._control_server = ControlServer(
            self,
            host=control_host,
            port=control_port,
        )

        self._endpoint_registry = (
            endpoint_registry
            if endpoint_registry is not None
            else ControlEndpointRegistry()
        )

        self._state = ProcessState.STOPPED
        self._stop_event = Event()
        self._last_result: BootResult | None = None
        self._lock = RLock()

    @property
    def boot_manager(self) -> BootManager:
        """Return the managed BootManager."""
        return self._boot_manager

    @property
    def control_server(self) -> ControlServer:
        """Return the managed ControlServer."""
        return self._control_server

    @property
    def endpoint_registry(self) -> ControlEndpointRegistry:
        """Return the endpoint registry."""
        return self._endpoint_registry

    @property
    def state(self) -> ProcessState:
        """Return the current process state."""
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        """Return whether the process host is running."""
        with self._lock:
            return self._state == ProcessState.RUNNING

    @property
    def last_result(self) -> BootResult | None:
        """Return the most recent boot result."""
        with self._lock:
            return self._last_result

    def start(self) -> BootResult:
        """
        Start Sentinel, its control endpoint, and endpoint publication.
        """
        with self._lock:
            if self._state == ProcessState.RUNNING:
                raise ProcessStateError(
                    "Sentinel process is already running."
                )

            if self._state in {
                ProcessState.STARTING,
                ProcessState.STOPPING,
            }:
                raise ProcessStateError(
                    "Sentinel process is currently transitioning."
                )

            if self._state == ProcessState.FAILED:
                raise ProcessStateError(
                    "Sentinel process is in a failed state."
                )

            self._state = ProcessState.STARTING
            self._stop_event.clear()

        try:
            # Remove an endpoint left behind by a process that is no
            # longer listening.
            self._endpoint_registry.clear_if_stale()

            if self._endpoint_registry.exists():
                raise ProcessStartupError(
                    "Another Sentinel control endpoint is already active."
                )

            result = self._boot_manager.start()

            try:
                self._control_server.start()

                endpoint = ControlEndpoint(
                    host=self._control_server.host,
                    port=self._control_server.port,
                )

                self._endpoint_registry.save(endpoint)

            except Exception:
                try:
                    self._control_server.stop()
                except Exception:
                    pass

                try:
                    self._boot_manager.stop()
                except Exception:
                    pass

                raise

        except ProcessStartupError:
            with self._lock:
                self._state = ProcessState.STOPPED

            raise

        except Exception as exc:
            with self._lock:
                self._state = ProcessState.STOPPED

            raise ProcessStartupError(
                "Sentinel process failed to start."
            ) from exc

        with self._lock:
            self._state = ProcessState.RUNNING
            self._last_result = result

        return result

    def stop(self) -> BootResult:
        """
        Stop the control endpoint, endpoint publication, and Sentinel OS.
        """
        with self._lock:
            if self._state != ProcessState.RUNNING:
                raise ProcessStateError(
                    "Sentinel process is not running."
                )

            self._state = ProcessState.STOPPING

        control_error: Exception | None = None

        try:
            self._control_server.stop()
        except Exception as exc:
            control_error = exc

        if control_error is None:
            try:
                self._endpoint_registry.remove()
            except Exception as exc:
                control_error = exc

        try:
            result = self._boot_manager.stop()
        except Exception as exc:
            with self._lock:
                self._state = ProcessState.FAILED

            raise ProcessShutdownError(
                "Sentinel process failed to stop."
            ) from exc

        if control_error is not None:
            with self._lock:
                self._state = ProcessState.FAILED

            raise ProcessShutdownError(
                "Sentinel process failed to stop cleanly."
            ) from control_error

        with self._lock:
            self._state = ProcessState.STOPPED
            self._last_result = result

        self._stop_event.set()

        return result

    def wait(self, timeout: float | None = None) -> bool:
        """
        Wait until the process receives a shutdown request.

        Returns True when shutdown has been requested, otherwise False
        when the optional timeout expires.
        """
        if timeout is not None:
            if not isinstance(timeout, (int, float)):
                raise TypeError(
                    "timeout must be a number or None."
                )

            if timeout < 0:
                raise ValueError(
                    "timeout cannot be negative."
                )

        return self._stop_event.wait(timeout)

    def request_stop(self) -> None:
        """
        Request process shutdown.

        This only signals the host. It does not perform stop().
        """
        self._stop_event.set()

    def health(self) -> dict[str, Any]:
        """Return process and Sentinel health."""
        with self._lock:
            state = self._state
            result = self._last_result

        boot_health = self._boot_manager.health()
        control_running = self._control_server.running
        endpoint_exists = self._endpoint_registry.exists()

        return {
            "state": state.value,
            "running": state == ProcessState.RUNNING,
            "healthy": (
                state == ProcessState.RUNNING
                and boot_health.get("healthy") is True
                and control_running
                and endpoint_exists
            ),
            "boot": boot_health,
            "control": {
                "running": control_running,
                "host": self._control_server.host,
                "port": self._control_server.port,
            },
            "endpoint": {
                "registered": endpoint_exists,
                "path": str(self._endpoint_registry.path),
            },
            "last_result": (
                result.to_dict()
                if result is not None
                else None
            ),
        }

    def __enter__(self) -> ProcessHost:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        if self.running:
            self.stop()

    def __repr__(self) -> str:
        return (
            "ProcessHost("
            f"state={self.state.value!r}, "
            f"running={self.running}, "
            f"control={self._control_server.running}"
            ")"
        )
