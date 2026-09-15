"""
Bootstrap module for Sentinel OS.

Responsible for creating, starting and shutting down the Sentinel
Kernel.

Bootstrap intentionally contains no application-specific logic.
Infrastructure services are registered by the application layer.
"""

from __future__ import annotations

from collections.abc import Iterable

from .kernel import Kernel
from .service import Service


class Bootstrap:
    """
    Bootstrap the Sentinel Kernel.

    A Bootstrap instance owns a single Kernel instance and provides
    a clean entry point for starting and stopping Sentinel.
    """

    def __init__(
        self,
        services: Iterable[Service] = (),
    ) -> None:
        self._services = tuple(services)
        self._kernel: Kernel | None = None

    @property
    def services(self) -> tuple[Service, ...]:
        """Return the services managed by this bootstrap."""
        return self._services

    @property
    def kernel(self) -> Kernel:
        """Return the active kernel."""
        if self._kernel is None:
            raise RuntimeError("Kernel has not been started.")

        return self._kernel

    def create_kernel(self) -> Kernel:
        """
        Create and configure the Sentinel Kernel without starting it.

        The created Kernel becomes owned by this Bootstrap instance.
        """
        if self._kernel is not None:
            raise RuntimeError("Kernel is already running.")

        kernel = Kernel()

        for service in self._services:
            kernel.register(service)

        self._kernel = kernel
        return kernel

    def start(self) -> Kernel:
        """Create, configure and start the Sentinel Kernel."""
        if self._kernel is not None:
            raise RuntimeError("Kernel is already running.")

        kernel = self.create_kernel()

        try:
            kernel.boot()
        except Exception:
            try:
                kernel.shutdown()
            except Exception:
                pass

            self._kernel = None
            raise

        return kernel
    def shutdown(self) -> None:
        """Gracefully stop the Sentinel Kernel."""
        if self._kernel is None:
            raise RuntimeError("Kernel is not running.")

        self._kernel.shutdown()
        self._kernel = None
