"""
Adapter between the Sentinel Kernel and Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service_state import ServiceState


class KernelAdapter:
    """
    Adapt the Sentinel Kernel to the Kernel Control Plane target contract.

    The control plane depends on this adapter instead of directly depending
    on Kernel implementation details.
    """

    __slots__ = ("_kernel",)

    def __init__(self, kernel: Kernel) -> None:
        self._kernel = kernel

    @property
    def kernel(self) -> Kernel:
        """Return the underlying Kernel."""
        return self._kernel

    def service_names(self) -> tuple[str, ...]:
        """Return the names of all registered services."""
        return tuple(service.name for service in self._kernel.services())

    def service_state(self, name: str) -> ServiceState:
        """Return the lifecycle state of a registered service."""
        return self._kernel.state(name)

    def start_service(self, name: str) -> None:
        """Start a service and any dependencies it requires."""
        self._kernel.start(name)

    def stop_service(self, name: str) -> None:
        """Stop a service."""
        self._kernel.stop(name)

    def restart_service(self, name: str) -> None:
        """Restart a service and ensure its dependencies."""
        self._kernel.restart(name)

    def health(self) -> Mapping[str, Any]:
        """Return Kernel health information."""
        return self._kernel.health()