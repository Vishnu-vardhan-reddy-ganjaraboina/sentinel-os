"""
Kernel runtime service for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from sentinel.kernel.service import Service
from sentinel.memory.service import MemoryService


class MemoryRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for MemoryService.
    """

    def __init__(
        self,
        memory: MemoryService | None = None,
    ) -> None:
        super().__init__("memory")

        self._memory = (
            memory
            if memory is not None
            else MemoryService()
        )

        self._initialized = False
        self._shutdown = False

    @property
    def memory(self) -> MemoryService:
        """Return the underlying memory service."""
        return self._memory

    def initialize(self) -> None:
        """
        Initialize memory resources.
        """
        if self._shutdown:
            raise RuntimeError(
                "Memory runtime has already been shut down."
            )

        self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down memory resources.
        """
        if self._shutdown:
            return

        self._shutdown = True
        self._initialized = False

    def health(self) -> dict[str, bool]:
        """Return memory service health information."""
        return {
            "healthy": (
                self._initialized
                and not self._shutdown
            ),
        }