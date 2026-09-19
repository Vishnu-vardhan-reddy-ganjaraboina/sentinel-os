"""
Top-level Sentinel OS system lifecycle coordinator.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.application import Application
from sentinel.application_host import ApplicationHost
from sentinel.control_plane.service import ControlPlane
from sentinel.kernel.kernel import Kernel
from sentinel.platform import Platform


class System:
    """
    Coordinate the top-level Sentinel OS lifecycle.

    Kernel owns system services.
    Platform owns applications.
    System coordinates their startup and shutdown order.
    """

    def __init__(
        self,
        kernel: Kernel,
        platform: Platform | None = None,
        control_plane: ControlPlane | None = None,
    ) -> None:
        if not isinstance(kernel, Kernel):
            raise TypeError(
                "kernel must be a Kernel instance."
            )

        if platform is not None and not isinstance(
            platform,
            Platform,
        ):
            raise TypeError(
                "platform must be a Platform instance."
            )

        if control_plane is not None and not isinstance(
            control_plane,
            ControlPlane,
        ):
            raise TypeError(
                "control_plane must be a ControlPlane instance."
            )

        self._kernel = kernel
        self._platform = (
            platform
            if platform is not None
            else Platform()
        )
        self._control_plane = control_plane

        self._running = False
        self._lock = RLock()

    @property
    def kernel(self) -> Kernel:
        """Return the system kernel."""
        return self._kernel

    @property
    def platform(self) -> Platform:
        """Return the application platform."""
        return self._platform

    @property
    def control_plane(self) -> ControlPlane | None:
        """Return the system control plane."""
        return self._control_plane

    @property
    def host(self) -> ApplicationHost:
        """Return the application host."""
        return self._platform.host

    @property
    def running(self) -> bool:
        """Return whether the complete system is running."""
        with self._lock:
            return self._running

    def register_application(
        self,
        name: str,
        application: Application,
        manifest: Any | None = None,
    ) -> None:
        """Register an application before system startup."""
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Cannot register applications while system is running."
                )

        self._platform.register_application(
            name,
            application,
            manifest,
        )

    def start(self) -> None:
        """
        Start the complete Sentinel OS system.

        Kernel starts first. Applications start only after the kernel
        has successfully booted. If application startup fails, the
        platform is rolled back and the kernel is shut down.
        """
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Sentinel system is already running."
                )

        self._kernel.boot()

        try:
            self._platform.start()
        except Exception:
            try:
                self._kernel.shutdown()
            except Exception:
                pass
            raise

        with self._lock:
            self._running = True

    def shutdown(self) -> None:
        """
        Shut down the complete Sentinel OS system.

        Applications are stopped before kernel services.
        Kernel shutdown is attempted even when application shutdown
        fails.
        """
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Sentinel system is not running."
                )

        first_error: Exception | None = None

        try:
            self._platform.shutdown()
        except Exception as exc:
            first_error = exc

        try:
            self._kernel.shutdown()
        except Exception as exc:
            if first_error is None:
                first_error = exc

        with self._lock:
            self._running = False

        if first_error is not None:
            raise first_error

    def health(self) -> Mapping[str, Any]:
        """Return system-wide health information."""
        kernel_health = self._kernel.health()
        platform_health = self._platform.health()

        return {
            "running": self.running,
            "kernel": kernel_health,
            "platform": platform_health,
            "healthy": (
                self.running
                and kernel_health.get("healthy") is True
                and all(
                    health.get("healthy") is True
                    for health in platform_health.values()
                )
            ),
        }

    def __repr__(self) -> str:
        """Return a useful system representation."""
        return (
            "System("
            f"running={self.running}, "
            f"applications={len(self._platform)})"
        )