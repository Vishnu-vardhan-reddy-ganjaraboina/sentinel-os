"""
Bootstrap module for Sentinel OS.

Responsible for creating, starting and shutting down the Sentinel
Kernel.

Bootstrap intentionally contains no application-specific logic.
Infrastructure services are registered by the application layer.
"""

from __future__ import annotations

from .kernel import Kernel


class Bootstrap:
    """
    Bootstrap the Sentinel Kernel.

    A Bootstrap instance owns a single Kernel instance and provides
    a clean entry point for starting and stopping Sentinel.
    """

    def __init__(self) -> None:
        self._kernel: Kernel | None = None

    @property
    def kernel(self) -> Kernel:
        """
        Return the running kernel.

        Raises:
            RuntimeError:
                If the kernel has not been started.
        """
        if self._kernel is None:
            raise RuntimeError("Kernel has not been started.")

        return self._kernel

    def start(self) -> Kernel:
        """
        Create and start the Sentinel Kernel.

        Returns:
            Kernel:
                The running kernel instance.

        Raises:
            RuntimeError:
                If the kernel is already running.
        """
        if self._kernel is not None:
            raise RuntimeError("Kernel is already running.")

        kernel = Kernel()
        kernel.start()

        self._kernel = kernel
        return kernel

    def shutdown(self) -> None:
        """
        Gracefully stop the Sentinel Kernel.

        Raises:
            RuntimeError:
                If the kernel is not running.
        """
        if self._kernel is None:
            raise RuntimeError("Kernel is not running.")

        self._kernel.shutdown()
        self._kernel = None