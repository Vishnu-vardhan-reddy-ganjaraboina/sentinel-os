"""
Target interface for Sentinel Kernel Control Plane operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from sentinel.kernel.service_state import ServiceState


class KernelControlTarget(Protocol):
    """
    Interface required by the Kernel Control Plane.

    The control layer depends on this abstraction rather than
    directly depending on Kernel implementation details.
    """

    def service_names(self) -> tuple[str, ...]:
        """Return registered service names."""
        ...

    def service_state(self, name: str) -> ServiceState:
        """Return the lifecycle state of a service."""
        ...

    def start_service(self, name: str) -> None:
        """Start a service and its required dependencies."""
        ...

    def stop_service(self, name: str) -> None:
        """Stop a service."""
        ...

    def restart_service(self, name: str) -> None:
        """Restart a service and ensure its dependencies."""
        ...

    def health(self) -> Mapping[str, Any]:
        """Return Kernel health information."""
        ...