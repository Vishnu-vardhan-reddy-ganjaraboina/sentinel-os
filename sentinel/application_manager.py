"""
Application lifecycle management for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.application import Application
from sentinel.application_registry import ApplicationRegistry
from sentinel.application_state import ApplicationState


class ApplicationManager:
    """
    Manage registration and lifecycle of Sentinel applications.

    ApplicationManager owns application-level lifecycle orchestration.
    Individual Application objects remain responsible for their own
    startup and shutdown behavior.
    """

    _ACTIVE_STATES = frozenset(
        {
            ApplicationState.STARTING,
            ApplicationState.RUNNING,
            ApplicationState.STOPPING,
        }
    )

    def __init__(
        self,
        registry: ApplicationRegistry | None = None,
    ) -> None:
        if registry is not None and not isinstance(
            registry,
            ApplicationRegistry,
        ):
            raise TypeError(
                "registry must be an ApplicationRegistry instance."
            )

        self._registry = (
            registry
            if registry is not None
            else ApplicationRegistry()
        )
        self._states: dict[str, ApplicationState] = {}
        self._errors: dict[str, str | None] = {}
        self._lock = RLock()

    @property
    def registry(self) -> ApplicationRegistry:
        """Return the application registry."""
        return self._registry

    def register(
        self,
        name: str,
        application: Application,
    ) -> None:
        """
        Register an application.

        Registry and lifecycle state are updated under the same manager
        lock. If lifecycle bookkeeping unexpectedly fails after registry
        insertion, the registry insertion is rolled back.
        """
        normalized_name = self._validate_name(name)

        if not isinstance(application, Application):
            raise TypeError(
                "application must be an Application instance."
            )

        with self._lock:
            self._registry.register(
                normalized_name,
                application,
            )

            try:
                self._states[normalized_name] = (
                    ApplicationState.REGISTERED
                )
                self._errors[normalized_name] = None
            except Exception:
                try:
                    self._registry.unregister(normalized_name)
                except Exception:
                    pass
                raise

    def unregister(
        self,
        name: str,
    ) -> Application:
        """Unregister and return an inactive application."""
        normalized_name = self._validate_name(name)

        with self._lock:
            state = self._states.get(normalized_name)

            if state in self._ACTIVE_STATES:
                raise RuntimeError(
                    f"Application '{normalized_name}' is active."
                )

            application = self._registry.unregister(
                normalized_name,
            )

            self._states.pop(normalized_name, None)
            self._errors.pop(normalized_name, None)

            return application

    def get(
        self,
        name: str,
    ) -> Application:
        """Return a registered application."""
        normalized_name = self._validate_name(name)

        with self._lock:
            return self._registry.get(normalized_name)

    def all(self) -> tuple[Application, ...]:
        """Return a snapshot of all registered applications."""
        with self._lock:
            return self._registry.all()

    def names(self) -> tuple[str, ...]:
        """Return a snapshot of all registered application names."""
        with self._lock:
            return self._registry.names()

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether an application is registered."""
        normalized_name = self._validate_name(name)

        with self._lock:
            return self._registry.contains(normalized_name)

    def start(
        self,
        name: str,
    ) -> Application:
        """
        Start a registered application.

        State is changed to STARTING before invoking Application.start().
        Application startup executes outside the manager lock.
        """
        normalized_name = self._validate_name(name)

        with self._lock:
            application = self._registry.get(normalized_name)
            state = self._states.get(normalized_name)

            if state == ApplicationState.RUNNING:
                raise RuntimeError(
                    f"Application '{normalized_name}' is already running."
                )

            if state == ApplicationState.STARTING:
                raise RuntimeError(
                    f"Application '{normalized_name}' is starting."
                )

            if state == ApplicationState.STOPPING:
                raise RuntimeError(
                    f"Application '{normalized_name}' is stopping."
                )

            self._states[normalized_name] = (
                ApplicationState.STARTING
            )
            self._errors[normalized_name] = None

        try:
            application.start()
        except Exception as exc:
            with self._lock:
                self._states[normalized_name] = (
                    ApplicationState.FAILED
                )
                self._errors[normalized_name] = str(exc)

            raise

        with self._lock:
            self._states[normalized_name] = (
                ApplicationState.RUNNING
            )
            self._errors[normalized_name] = None

        return application

    def stop(
        self,
        name: str,
    ) -> None:
        """
        Stop a running application.

        State is changed to STOPPING before invoking Application.shutdown().
        Application shutdown executes outside the manager lock.
        """
        normalized_name = self._validate_name(name)

        with self._lock:
            application = self._registry.get(normalized_name)
            state = self._states.get(normalized_name)

            if state != ApplicationState.RUNNING:
                raise RuntimeError(
                    f"Application '{normalized_name}' is not running."
                )

            self._states[normalized_name] = (
                ApplicationState.STOPPING
            )

        try:
            application.shutdown()
        except Exception as exc:
            with self._lock:
                self._states[normalized_name] = (
                    ApplicationState.FAILED
                )
                self._errors[normalized_name] = str(exc)

            raise

        with self._lock:
            self._states[normalized_name] = (
                ApplicationState.STOPPED
            )
            self._errors[normalized_name] = None

    def restart(
        self,
        name: str,
    ) -> Application:
        """Restart a currently running application."""
        normalized_name = self._validate_name(name)

        self.stop(normalized_name)
        return self.start(normalized_name)

    def running(
        self,
        name: str,
    ) -> bool:
        """Return whether a registered application is running."""
        normalized_name = self._validate_name(name)

        with self._lock:
            self._registry.get(normalized_name)

            return (
                self._states.get(normalized_name)
                == ApplicationState.RUNNING
            )

    def state(
        self,
        name: str,
    ) -> ApplicationState:
        """Return an application's lifecycle state."""
        normalized_name = self._validate_name(name)

        with self._lock:
            self._registry.get(normalized_name)

            return self._states[normalized_name]

    def states(self) -> Mapping[str, ApplicationState]:
        """Return a snapshot of all application states."""
        with self._lock:
            return dict(self._states)

    def errors(self) -> Mapping[str, str | None]:
        """Return a snapshot of application lifecycle errors."""
        with self._lock:
            return dict(self._errors)

    def health(
        self,
        name: str,
    ) -> Mapping[str, Any]:
        """Return health information for an application."""
        normalized_name = self._validate_name(name)

        with self._lock:
            application = self._registry.get(normalized_name)
            state = self._states.get(normalized_name)
            error = self._errors.get(normalized_name)

        if state != ApplicationState.RUNNING:
            return {
                "healthy": False,
                "state": (
                    state.value
                    if state is not None
                    else None
                ),
                "error": error,
            }

        try:
            health = application.health
        except Exception as exc:
            return {
                "healthy": False,
                "state": state.value,
                "error": str(exc),
            }

        if not isinstance(health, Mapping):
            return {
                "healthy": False,
                "state": state.value,
                "error": "Application health result is invalid.",
            }

        result = dict(health)
        result.setdefault("healthy", False)
        result["state"] = state.value

        return result

    def clear(self) -> None:
        """
        Remove all inactive applications.

        Active applications are never silently removed.
        """
        with self._lock:
            active = tuple(
                name
                for name, state in self._states.items()
                if state in self._ACTIVE_STATES
            )

            if active:
                names = ", ".join(active)
                raise RuntimeError(
                    f"Cannot clear active applications: {names}."
                )

            self._registry.clear()
            self._states.clear()
            self._errors.clear()

    def __len__(self) -> int:
        """Return the number of registered applications."""
        with self._lock:
            return len(self._registry)

    def __repr__(self) -> str:
        """Return a useful manager representation."""
        with self._lock:
            return (
                "ApplicationManager("
                f"applications={len(self._states)})"
            )

    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate and normalize an application name."""
        if not isinstance(name, str):
            raise TypeError("name must be a string.")

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("name must not be empty.")

        return normalized_name