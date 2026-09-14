"""
Application registry for Sentinel OS.
"""

from __future__ import annotations

from threading import RLock
from typing import Any

from sentinel.application import Application
from sentinel.application_manifest import ApplicationManifest


class ApplicationRegistry:
    """
    Thread-safe registry for Sentinel applications.

    The registry manages application identity, metadata, and lookup.
    Application lifecycle remains owned by ApplicationManager.
    """

    def __init__(self) -> None:
        self._applications: dict[str, Application] = {}
        self._manifests: dict[str, ApplicationManifest] = {}
        self._lock = RLock()

    def register(
        self,
        name: str,
        application: Application,
        manifest: ApplicationManifest | None = None,
    ) -> None:
        """
        Register an application and its manifest.

        When no manifest is supplied, a minimal manifest is created
        automatically from the registration name.
        """
        normalized_name = self._validate_name(name)

        if not isinstance(application, Application):
            raise TypeError(
                "application must be an Application instance."
            )

        if manifest is None:
            manifest = ApplicationManifest(
                name=normalized_name,
            )
        elif not isinstance(manifest, ApplicationManifest):
            raise TypeError(
                "manifest must be an ApplicationManifest instance."
            )
        elif manifest.name != normalized_name:
            raise ValueError(
                f"Manifest name '{manifest.name}' does not match "
                f"registration name '{normalized_name}'."
            )

        with self._lock:
            if normalized_name in self._applications:
                raise ValueError(
                    f"Application '{normalized_name}' is already registered."
                )

            self._applications[normalized_name] = application
            self._manifests[normalized_name] = manifest

    def unregister(
        self,
        name: str,
    ) -> Application:
        """
        Remove and return a registered application.

        The application's manifest is removed with it.
        """
        normalized_name = self._validate_name(name)

        with self._lock:
            try:
                application = self._applications.pop(
                    normalized_name,
                )
            except KeyError:
                raise KeyError(
                    f"Application '{normalized_name}' is not registered."
                ) from None

            self._manifests.pop(normalized_name, None)

            return application

    def get(
        self,
        name: str,
    ) -> Application:
        """Return a registered application."""
        normalized_name = self._validate_name(name)

        with self._lock:
            try:
                return self._applications[normalized_name]
            except KeyError:
                raise KeyError(
                    f"Application '{normalized_name}' is not registered."
                ) from None

    def manifest(
        self,
        name: str,
    ) -> ApplicationManifest:
        """Return the manifest for a registered application."""
        normalized_name = self._validate_name(name)

        with self._lock:
            try:
                return self._manifests[normalized_name]
            except KeyError:
                raise KeyError(
                    f"Application '{normalized_name}' is not registered."
                ) from None

    def application_info(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Return application and manifest information."""
        normalized_name = self._validate_name(name)

        with self._lock:
            try:
                application = self._applications[normalized_name]
                manifest = self._manifests[normalized_name]
            except KeyError:
                raise KeyError(
                    f"Application '{normalized_name}' is not registered."
                ) from None

            return {
                "name": normalized_name,
                "application": application,
                "manifest": manifest,
            }

    def all(self) -> tuple[Application, ...]:
        """Return a snapshot of all registered applications."""
        with self._lock:
            return tuple(self._applications.values())

    def names(self) -> tuple[str, ...]:
        """Return a snapshot of all registered application names."""
        with self._lock:
            return tuple(self._applications.keys())

    def manifests(
        self,
    ) -> tuple[tuple[str, ApplicationManifest], ...]:
        """Return a snapshot of all application manifests."""
        with self._lock:
            return tuple(self._manifests.items())

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether an application is registered."""
        normalized_name = self._validate_name(name)

        with self._lock:
            return normalized_name in self._applications

    def clear(self) -> None:
        """Remove all registered applications and manifests."""
        with self._lock:
            self._applications.clear()
            self._manifests.clear()

    def __len__(self) -> int:
        """Return the number of registered applications."""
        with self._lock:
            return len(self._applications)

    def __contains__(
        self,
        name: object,
    ) -> bool:
        """Return whether a valid string name is registered."""
        if not isinstance(name, str):
            return False

        normalized_name = name.strip()

        if not normalized_name:
            return False

        with self._lock:
            return normalized_name in self._applications

    def __repr__(self) -> str:
        """Return a useful registry representation."""
        with self._lock:
            return (
                "ApplicationRegistry("
                f"applications={len(self._applications)})"
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