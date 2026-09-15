"""
Boot lifecycle manager for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.boot.exceptions import (
    BootShutdownError,
    BootStartupError,
    BootStateError,
)
from sentinel.boot.profile import BootProfile
from sentinel.boot.result import BootResult
from sentinel.system import System


class BootManager:
    """
    Coordinate the top-level Sentinel OS boot lifecycle.

    Lifecycle:

        STOPPED
           |
           v
        STARTING
           |
           v
        RUNNING
           |
           v
        STOPPING
           |
           v
        STOPPED

    A failed startup returns to STOPPED because System is responsible
    for rolling back a partially completed startup.

    A failed shutdown enters FAILED because the system may be left
    partially active and requires explicit recovery handling.
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
    ) -> None:
        if not isinstance(system, System):
            raise TypeError("system must be a System instance.")

        if profile is not None and not isinstance(
            profile,
            BootProfile,
        ):
            raise TypeError("profile must be a BootProfile instance.")

        self._system = system
        self._profile = (
            profile
            if profile is not None
            else BootProfile()
        )

        self._state = self.STOPPED
        self._last_result: BootResult | None = None
        self._lock = RLock()

    @property
    def system(self) -> System:
        """Return the managed Sentinel system."""
        return self._system

    @property
    def profile(self) -> BootProfile:
        """Return the active boot profile."""
        return self._profile

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
        """
        Boot Sentinel OS.

        Only one startup transition may execute at a time.
        """
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
        """
        Shut down Sentinel OS.

        Only one shutdown transition may execute at a time.
        """
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
        """
        Return combined boot-manager and system health.
        """
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
