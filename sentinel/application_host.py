"""
Application host orchestration for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.application import Application
from sentinel.application_manager import ApplicationManager
from sentinel.application_state import ApplicationState


class ApplicationHost:
    """
    Coordinate lifecycle of multiple Sentinel applications.

    ApplicationHost owns orchestration across applications.
    ApplicationManager remains responsible for individual application
    lifecycle transitions.
    """

    def __init__(
        self,
        manager: ApplicationManager | None = None,
    ) -> None:
        if manager is not None and not isinstance(
            manager,
            ApplicationManager,
        ):
            raise TypeError(
                "manager must be an ApplicationManager instance."
            )

        self._manager = (
            manager
            if manager is not None
            else ApplicationManager()
        )
        self._running = False
        self._starting = False
        self._stopping = False
        self._lock = RLock()

    @property
    def manager(self) -> ApplicationManager:
        """Return the application manager."""
        return self._manager

    @property
    def running(self) -> bool:
        """Return whether the host is running."""
        with self._lock:
            return self._running

    def register(
        self,
        name: str,
        application: Application,
    ) -> None:
        """Register an application with the host."""
        with self._lock:
            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            self._manager.register(name, application)

    def unregister(
        self,
        name: str,
    ) -> Application:
        """Unregister an inactive application."""
        with self._lock:
            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            return self._manager.unregister(name)

    def get(
        self,
        name: str,
    ) -> Application:
        """Return a registered application."""
        with self._lock:
            return self._manager.get(name)

    def start(
        self,
        name: str,
    ) -> Application:
        """Start one registered application."""
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Application host is not running."
                )

            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            return self._manager.start(name)

    def stop(
        self,
        name: str,
    ) -> None:
        """Stop one registered application."""
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Application host is not running."
                )

            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            self._manager.stop(name)

    def start_all(self) -> tuple[Application, ...]:
        """
        Start all registered applications.

        Applications are started in registration order. If startup of one
        application fails, already-started applications are stopped in
        reverse order before the original exception is raised.
        """
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Application host is already running."
                )

            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            self._starting = True

        started: list[Application] = []

        try:
            for name in self._manager.names():
                application = self._manager.start(name)
                started.append(application)
        except Exception:
            for application in reversed(started):
                for name in self._manager.names():
                    if self._manager.get(name) is application:
                        try:
                            self._manager.stop(name)
                        except Exception:
                            pass
                        break

            with self._lock:
                self._starting = False
                self._running = False

            raise

        with self._lock:
            self._starting = False
            self._running = True

        return tuple(started)

    def stop_all(self) -> None:
        """
        Stop all running applications.

        Applications are stopped in reverse registration order.
        Shutdown continues if one application fails; the first failure
        is re-raised after all applications have been attempted.
        """
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Application host is not running."
                )

            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            self._stopping = True

        first_error: Exception | None = None

        try:
            for name in reversed(self._manager.names()):
                try:
                    if self._manager.running(name):
                        self._manager.stop(name)
                except Exception as exc:
                    if first_error is None:
                        first_error = exc
        finally:
            with self._lock:
                self._stopping = False
                self._running = False

        if first_error is not None:
            raise first_error

    def state(
        self,
        name: str,
    ) -> ApplicationState:
        """Return an application's state."""
        return self._manager.state(name)

    def states(self) -> Mapping[str, ApplicationState]:
        """Return a snapshot of application states."""
        return self._manager.states()

    def health(
        self,
        name: str,
    ) -> Mapping[str, Any]:
        """Return health information for one application."""
        return self._manager.health(name)

    def health_all(self) -> Mapping[str, Mapping[str, Any]]:
        """Return health information for all registered applications."""
        result: dict[str, Mapping[str, Any]] = {}

        for name in self._manager.names():
            result[name] = self._manager.health(name)

        return result

    def __len__(self) -> int:
        """Return the number of registered applications."""
        return len(self._manager)

    def __repr__(self) -> str:
        """Return a useful host representation."""
        return (
            "ApplicationHost("
            f"applications={len(self._manager)}, "
            f"running={self.running})"
        )