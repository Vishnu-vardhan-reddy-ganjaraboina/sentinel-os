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
from sentinel.control_plane.transport_server import (
    ControlPlaneTransportServer,
)
from sentinel.kernel.kernel import Kernel
from sentinel.platform import Platform


class System:
    """
    Coordinate the top-level Sentinel OS lifecycle.

    Kernel owns system services.
    Platform owns applications.
    Control Plane owns privileged system control.
    Control Plane transport exposes that control plane to external clients.

    System coordinates their startup and shutdown order.
    """

    def __init__(
        self,
        kernel: Kernel,
        platform: Platform | None = None,
        control_plane: ControlPlane | None = None,
        control_transport: ControlPlaneTransportServer | None = None,
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

        if control_transport is not None and not isinstance(
            control_transport,
            ControlPlaneTransportServer,
        ):
            raise TypeError(
                "control_transport must be a "
                "ControlPlaneTransportServer instance."
            )

        if (
            control_transport is not None
            and control_plane is not None
            and control_transport.control_plane is not control_plane
        ):
            raise ValueError(
                "control_transport must use the same ControlPlane "
                "owned by the System."
            )

        self._kernel = kernel

        self._platform = (
            platform
            if platform is not None
            else Platform()
        )

        self._control_plane = control_plane
        self._control_transport = control_transport

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
    def control_transport(
        self,
    ) -> ControlPlaneTransportServer | None:
        """Return the Control Plane transport server."""
        return self._control_transport

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

        Startup order:

            Kernel
                ↓
            Platform
                ↓
            Control Plane transport

        If any later startup stage fails, earlier stages are rolled back.
        """
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Sentinel system is already running."
                )

        self._kernel.boot()

        try:
            self._platform.start()

            if self._control_transport is not None:
                self._control_transport.start()

        except Exception:
            try:
                if (
                    self._control_transport is not None
                    and self._control_transport.running
                ):
                    self._control_transport.stop()
            except Exception:
                pass

            try:
                self._platform.shutdown()
            except Exception:
                pass

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

        Shutdown order:

            Control Plane transport
                ↓
            Platform
                ↓
            Kernel

        All shutdown stages are attempted even when an earlier stage
        fails. The first failure is raised after cleanup is attempted.
        """
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Sentinel system is not running."
                )

        first_error: Exception | None = None

        try:
            if self._control_transport is not None:
                self._control_transport.stop()
        except Exception as exc:
            first_error = exc

        try:
            self._platform.shutdown()
        except Exception as exc:
            if first_error is None:
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

        control_transport_health: Mapping[str, Any]

        if self._control_transport is None:
            control_transport_health = {
                "configured": False,
                "running": False,
                "healthy": True,
            }
        else:
            control_transport_health = {
                "configured": True,
                "running": self._control_transport.running,
                "host": self._control_transport.host,
                "port": self._control_transport.port,
                "healthy": (
                    self._control_transport.running
                    if self.running
                    else True
                ),
            }

        return {
            "running": self.running,
            "kernel": kernel_health,
            "platform": platform_health,
            "control_transport": control_transport_health,
            "healthy": (
                self.running
                and kernel_health.get("healthy") is True
                and all(
                    health.get("healthy") is True
                    for health in platform_health.values()
                )
                and control_transport_health.get("healthy") is True
            ),
        }

    def __repr__(self) -> str:
        """Return a useful system representation."""
        return (
            "System("
            f"running={self.running}, "
            f"applications={len(self._platform)})"
        )