"""
Boot lifecycle manager for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.boot.configuration import BootConfiguration
from sentinel.boot.exceptions import (
    BootShutdownError,
    BootStartupError,
    BootStateError,
)
from sentinel.boot.profile import BootProfile
from sentinel.boot.result import BootResult
from sentinel.boot.system_factory import SystemFactory
from sentinel.system import System


class BootManager:
    """
    Coordinate the top-level Sentinel OS boot lifecycle.

    Lifecycle:

        STOPPED -> STARTING -> RUNNING -> STOPPING -> STOPPED

    A failed startup returns to STOPPED because System performs its own
    rollback.

    A failed shutdown enters FAILED because recovery may be required.
    """

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"

    def __init__(
        self,
        system: System,
        profile: BootProfile | None = None,
        *,
        factory: SystemFactory | None = None,
    ) -> None:
        if not isinstance(system, System):
            raise TypeError("system must be a System instance.")

        if profile is not None and not isinstance(
            profile,
            BootProfile,
        ):
            raise TypeError("profile must be a BootProfile instance.")

        if factory is not None and not isinstance(
            factory,
            SystemFactory,
        ):
            raise TypeError("factory must be a SystemFactory instance.")

        self._system = system
        self._profile = (
            profile
            if profile is not None
            else BootProfile()
        )
        self._factory = factory

        self._state = self.STOPPED
        self._last_result: BootResult | None = None
        self._lock = RLock()

    @classmethod
    def from_configuration(
        cls,
        configuration: BootConfiguration,
        profile: BootProfile | None = None,
    ) -> BootManager:
        """
        Compose a System from boot configuration and return a BootManager.

        The system is composed but not started.
        """
        if not isinstance(
            configuration,
            BootConfiguration,
        ):
            raise TypeError(
                "configuration must be a BootConfiguration instance."
            )

        if profile is not None and not isinstance(
            profile,
            BootProfile,
        ):
            raise TypeError("profile must be a BootProfile instance.")

        factory = SystemFactory(configuration)
        system = factory.create()

        return cls(
            system,
            profile,
            factory=factory,
        )

    @property
    def system(self) -> System:
        """Return the managed Sentinel system."""
        return self._system

    @property
    def profile(self) -> BootProfile:
        """Return the active boot profile."""
        return self._profile

    @property
    def factory(self) -> SystemFactory | None:
        """Return the SystemFactory used for composition, if any."""
        return self._factory

    @property
    def state(self) -> str:
        """Return the current boot lifecycle state."""
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        """Return whether Sentinel is fully running."""
        with self._lock:
            return self._state == self.RUNNING

    @property
    def last_result(self) -> BootResult | None:
        """Return the most recent boot operation result."""
        with self._lock:
            return self._last_result

    def start(self) -> BootResult:
        """Boot Sentinel OS."""
        with self._lock:
            if self._state == self.RUNNING:
                raise BootStateError(
                    "Sentinel is already booted."
                )

            if self._state in {
                self.STARTING,
                self.STOPPING,
            }:
                raise BootStateError(
                    "Sentinel is currently transitioning."
                )

            if self._state == self.FAILED:
                raise BootStateError(
                    "Sentinel is in a failed state. "
                    "Recovery is required before starting."
                )

            self._state = self.STARTING

        try:
            self._system.start()

        except Exception as exc:
            result = BootResult(
                success=False,
                profile=self._profile.name,
                message="Sentinel OS boot failed.",
                details={
                    "state": self.STOPPED,
                    "error": str(exc),
                    "exception": type(exc).__name__,
                },
            )

            with self._lock:
                self._state = self.STOPPED
                self._last_result = result

            raise BootStartupError(
                "Sentinel OS failed to boot."
            ) from exc

        system_health = self._system.health()

        if not isinstance(system_health, Mapping):
            system_health = {
                "healthy": False,
                "error": "System health result is invalid.",
            }

        result = BootResult(
            success=True,
            profile=self._profile.name,
            message="Sentinel OS booted successfully.",
            details={
                "state": self.RUNNING,
                "profile": self._profile.to_dict(),
                "health": dict(system_health),
            },
        )

        with self._lock:
            self._state = self.RUNNING
            self._last_result = result

        return result

    def stop(self) -> BootResult:
        """Shut down Sentinel OS."""
        with self._lock:
            if self._state != self.RUNNING:
                raise BootStateError(
                    "Sentinel is not booted."
                )

            self._state = self.STOPPING

        try:
            self._system.shutdown()

        except Exception as exc:
            result = BootResult(
                success=False,
                profile=self._profile.name,
                message="Sentinel OS shutdown failed.",
                details={
                    "state": self.FAILED,
                    "error": str(exc),
                    "exception": type(exc).__name__,
                },
            )

            with self._lock:
                self._state = self.FAILED
                self._last_result = result

            raise BootShutdownError(
                "Sentinel OS failed during shutdown."
            ) from exc

        system_health = self._system.health()

        if not isinstance(system_health, Mapping):
            system_health = {
                "healthy": False,
                "error": "System health result is invalid.",
            }

        result = BootResult(
            success=True,
            profile=self._profile.name,
            message="Sentinel OS shut down successfully.",
            details={
                "state": self.STOPPED,
                "health": dict(system_health),
            },
        )

        with self._lock:
            self._state = self.STOPPED
            self._last_result = result

        return result

    def health(self) -> dict[str, Any]:
        """Return combined boot-manager and system health."""
        with self._lock:
            state = self._state
            last_result = self._last_result

        system_health = self._system.health()

        if not isinstance(system_health, Mapping):
            system_health = {
                "healthy": False,
                "error": "System health result is invalid.",
            }

        return {
            "state": state,
            "running": state == self.RUNNING,
            "healthy": (
                state == self.RUNNING
                and system_health.get("healthy") is True
            ),
            "profile": self._profile.to_dict(),
            "system": dict(system_health),
            "last_result": (
                last_result.to_dict()
                if last_result is not None
                else None
            ),
        }

    def __repr__(self) -> str:
        return (
            "BootManager("
            f"profile={self._profile.name!r}, "
            f"state={self.state!r}, "
            f"running={self.running}"
            ")"
        )
