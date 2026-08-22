"""
Kernel runtime service for the Execution subsystem.
"""

from __future__ import annotations

from sentinel.execution.service import ExecutionService
from sentinel.kernel.service import Service


class ExecutionRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for ExecutionService.
    """

    def __init__(
        self,
        execution: ExecutionService | None = None,
    ) -> None:
        super().__init__("execution")

        self._execution = (
            execution
            if execution is not None
            else ExecutionService()
        )

        self._initialized = False
        self._shutdown = False

    @property
    def execution(self) -> ExecutionService:
        """Return the underlying execution service."""
        return self._execution

    def initialize(self) -> None:
        """
        Initialize execution resources.

        ExecutionService creates its resources during construction,
        so initialization only updates the runtime lifecycle state.
        """
        if self._shutdown:
            raise RuntimeError(
                "Execution runtime has already been shut down."
            )

        self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down execution resources.
        """
        if self._shutdown:
            return

        self._execution.shutdown()

        self._shutdown = True
        self._initialized = False

    def health(self) -> dict[str, bool]:
        """
        Return execution service health information.
        """
        return {
            "healthy": (
                self._initialized
                and not self._shutdown
            ),
        }