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

    @property
    def memory(self) -> MemoryService:
        """Return the underlying memory service."""
        return self._memory

    def initialize(self) -> None:
        """
        Initialize memory resources.

        MemoryService creates its resources during construction,
        so no additional initialization is required.
        """

    def shutdown(self) -> None:
        """
        Shut down memory resources.

        The current MemoryService uses in-memory storage, so there
        are no external resources requiring explicit shutdown.
        """

    def health(self) -> dict[str, bool]:
        """Return memory service health information."""
        return {
            "healthy": True,
        }
