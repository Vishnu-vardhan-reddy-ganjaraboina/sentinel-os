"""
Top-level Sentinel OS system lifecycle coordinator.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.application import Application
from sentinel.application_host import ApplicationHost
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpoint,
    ControlPlaneEndpointRegistry,
)
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
    Endpoint registry publishes the runtime Control Plane endpoint.

    System coordinates their startup and shutdown order.
    """

    def __init__(
        self,
        kernel: Kernel,
        platform: Platform | None = None,
        control_plane: ControlPlane | None = None,
        control_transport: ControlPlaneTransportServer | None = None,
        endpoint_registry: ControlPlaneEndpointRegistry | None = None,
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

        if endpoint_registry is not None and not isinstance(
            endpoint_registry,
            ControlPlaneEndpointRegistry,
        ):
            raise TypeError(
                "endpoint_registry must be a "
                "ControlPlaneEndpointRegistry instance."
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
        self._endpoint_registry = endpoint_registry

        self._running = False
        self._lock = RLock()

    @property
    def kernel(self) -> Kernel:
        return self._kernel

    @property
    def platform(self) -> Platform:
        return self._platform

    @property
    def control_plane(self) -> ControlPlane | None:
        return self._control_plane

    @property
    def control_transport(
        self,
    ) -> ControlPlaneTransportServer | None:
        return self._control_transport

    @property
    def endpoint_registry(
        self,
    ) -> ControlPlaneEndpointRegistry | None:
        return self._endpoint_registry

    @property
    def host(self) -> ApplicationHost:
        return self._platform.host

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def register_application(
        self,
        name: str,
        application: Application,
        manifest: Any | None = None,
    ) -> None:
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
                ↓
            Endpoint registry

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

            if self._endpoint_registry is not None:
                if self._control_transport is None:
                    raise RuntimeError(
                        "Endpoint registry requires a "
                        "Control Plane transport."
                    )

                endpoint = ControlPlaneEndpoint(
                    version=1,
                    host=self._control_transport.host,
                    port=self._control_transport.port,
                )

                self._endpoint_registry.publish(endpoint)

        except Exception:
            try:
                if self._endpoint_registry is not None:
                    self._endpoint_registry.clear()
            except Exception:
                pass

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

            Endpoint registry
                ↓
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
            if self._endpoint_registry is not None:
                self._endpoint_registry.clear()
        except Exception as exc:
            first_error = exc

        try:
            if self._control_transport is not None:
                self._control_transport.stop()
        except Exception as exc:
            if first_error is None:
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

        endpoint_registry_health: Mapping[str, Any]

        if self._endpoint_registry is None:
            endpoint_registry_health = {
                "configured": False,
                "registered": False,
                "healthy": True,
            }
        else:
            endpoint_registry_health = {
                "configured": True,
                "registered": self._endpoint_registry.registered,
                "path": str(self._endpoint_registry.path),
                "healthy": (
                    self._endpoint_registry.registered
                    if self.running
                    else True
                ),
            }

        return {
            "running": self.running,
            "kernel": kernel_health,
            "platform": platform_health,
            "control_transport": control_transport_health,
            "endpoint_registry": endpoint_registry_health,
            "healthy": (
                self.running
                and kernel_health.get("healthy") is True
                and all(
                    health.get("healthy") is True
                    for health in platform_health.values()
                )
                and control_transport_health.get("healthy") is True
                and endpoint_registry_health.get("healthy") is True
            ),
        }

    def __repr__(self) -> str:
        return (
            "System("
            f"running={self.running}, "
            f"applications={len(self._platform)})"
        )