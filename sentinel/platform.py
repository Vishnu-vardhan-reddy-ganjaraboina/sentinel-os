"""
Top-level Sentinel OS platform coordinator.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import TYPE_CHECKING, Any

from sentinel.application_host import ApplicationHost
from sentinel.application_manager import ApplicationManager
from sentinel.application_state import ApplicationState

if TYPE_CHECKING:
    from sentinel.application import Application
    from sentinel.application_manifest import ApplicationManifest


class Platform:
    """
    Coordinate the application platform layer.

    Platform owns ApplicationHost composition and provides the top-level
    application lifecycle API without owning individual Application
    internals.
    """

    def __init__(
        self,
        host: ApplicationHost | None = None,
    ) -> None:
        if host is not None and not isinstance(
            host,
            ApplicationHost,
        ):
            raise TypeError(
                "host must be an ApplicationHost instance."
            )

        self._host = (
            host
            if host is not None
            else ApplicationHost()
        )
        self._running = False
        self._lock = RLock()

    @property
    def host(self) -> ApplicationHost:
        """Return the application host."""
        return self._host

    @property
    def manager(self) -> ApplicationManager:
        """Return the application manager."""
        return self._host.manager

    @property
    def running(self) -> bool:
        """Return whether the platform is running."""
        with self._lock:
            return self._running

    def register_application(
        self,
        name: str,
        application: Application,
        manifest: ApplicationManifest | None = None,
    ) -> None:
        """Register an application with the platform."""
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Cannot register applications while platform is running."
                )

        self._host.register(
            name,
            application,
            manifest,
        )

    def unregister_application(
        self,
        name: str,
    ) -> Application:
        """Unregister an inactive application."""
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Cannot unregister applications while platform is running."
                )

        return self._host.unregister(name)

    def application(
        self,
        name: str,
    ) -> Application:
        """Return a registered application."""
        return self._host.get(name)

    def start(self) -> tuple[Application, ...]:
        """
        Start the application platform.

        All registered applications are started through ApplicationHost.
        """
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Sentinel platform is already running."
                )

        started = self._host.start_all()

        with self._lock:
            self._running = True

        return started

    def shutdown(self) -> None:
        """Shut down all applications managed by the platform."""
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Sentinel platform is not running."
                )

        try:
            self._host.stop_all()
        finally:
            with self._lock:
                self._running = False

    def application_states(
        self,
    ) -> Mapping[str, ApplicationState]:
        """Return a snapshot of application lifecycle states."""
        return self._host.states()

    def health(
        self,
    ) -> Mapping[str, Mapping[str, Any]]:
        """Return health information for all applications."""
        return self._host.health_all()

    def __len__(self) -> int:
        """Return the number of registered applications."""
        return len(self._host)

    def __repr__(self) -> str:
        """Return a useful platform representation."""
        return (
            "Platform("
            f"applications={len(self)}, "
            f"running={self.running})"
        )