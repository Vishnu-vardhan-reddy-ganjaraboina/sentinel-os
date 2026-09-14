"""
Application host orchestration for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import TYPE_CHECKING, Any

from sentinel.application_dependency_resolver import (
    ApplicationDependencyResolver,
)
from sentinel.application_manager import ApplicationManager
from sentinel.application_state import ApplicationState

if TYPE_CHECKING:
    from sentinel.application import Application
    from sentinel.application_manifest import ApplicationManifest


class ApplicationHost:
    """
    Coordinate lifecycle of multiple Sentinel applications.

    ApplicationHost owns multi-application orchestration.
    ApplicationManager owns individual application lifecycle.
    ApplicationDependencyResolver determines dependency-safe startup
    ordering.
    """

    def __init__(
        self,
        manager: ApplicationManager | None = None,
        resolver: ApplicationDependencyResolver | None = None,
    ) -> None:
        if manager is not None and not isinstance(
            manager,
            ApplicationManager,
        ):
            raise TypeError(
                "manager must be an ApplicationManager instance."
            )

        if resolver is not None and not isinstance(
            resolver,
            ApplicationDependencyResolver,
        ):
            raise TypeError(
                "resolver must be an "
                "ApplicationDependencyResolver instance."
            )

        self._manager = (
            manager
            if manager is not None
            else ApplicationManager()
        )
        self._resolver = (
            resolver
            if resolver is not None
            else ApplicationDependencyResolver()
        )

        self._running = False
        self._starting = False
        self._stopping = False
        self._startup_order: tuple[str, ...] = ()
        self._lock = RLock()

    @property
    def manager(self) -> ApplicationManager:
        """Return the application manager."""
        return self._manager

    @property
    def resolver(self) -> ApplicationDependencyResolver:
        """Return the dependency resolver."""
        return self._resolver

    @property
    def running(self) -> bool:
        """Return whether the host is running."""
        with self._lock:
            return self._running

    def register(
        self,
        name: str,
        application: Application,
        manifest: ApplicationManifest | None = None,
    ) -> None:
        """Register an application with its optional manifest."""
        with self._lock:
            if self._starting or self._stopping:
                raise RuntimeError(
                    "Application host is transitioning."
                )

            self._manager.register(
                name,
                application,
                manifest,
            )

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
        Start all applications in dependency-safe order.

        If startup fails, applications that already started are stopped
        in reverse startup order.
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

            manifests = tuple(
                manifest
                for _, manifest in self._manager.manifests()
            )

            startup_order = self._resolver.resolve(manifests)

            self._starting = True
            self._startup_order = startup_order

        started_names: list[str] = []

        try:
            for name in startup_order:
                self._manager.start(name)
                started_names.append(name)
        except Exception:
            for name in reversed(started_names):
                try:
                    if self._manager.running(name):
                        self._manager.stop(name)
                except Exception:
                    pass

            with self._lock:
                self._starting = False
                self._running = False
                self._startup_order = ()

            raise

        with self._lock:
            self._starting = False
            self._running = True

        return tuple(
            self._manager.get(name)
            for name in startup_order
        )

    def stop_all(self) -> None:
        """
        Stop all running applications in reverse startup order.

        Shutdown continues after individual application failures.
        The first failure is re-raised after all applications have been
        attempted.
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
            startup_order = self._startup_order

        first_error: Exception | None = None

        try:
            for name in reversed(startup_order):
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
                self._startup_order = ()

        if first_error is not None:
            raise first_error

    def state(
        self,
        name: str,
    ) -> ApplicationState:
        """Return an application's lifecycle state."""
        return self._manager.state(name)

    def states(
        self,
    ) -> Mapping[str, ApplicationState]:
        """Return a snapshot of application states."""
        return self._manager.states()

    def health(
        self,
        name: str,
    ) -> Mapping[str, Any]:
        """Return health information for one application."""
        return self._manager.health(name)

    def health_all(
        self,
    ) -> Mapping[str, Mapping[str, Any]]:
        """Return health information for all applications."""
        return {
            name: self._manager.health(name)
            for name in self._manager.names()
        }

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