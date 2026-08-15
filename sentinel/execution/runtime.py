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

    @property
    def execution(self) -> ExecutionService:
        """Return the underlying execution service."""
        return self._execution

    def initialize(self) -> None:
        """
        Initialize execution resources.

        ExecutionService creates its resources during construction,
        so no additional initialization is required.
        """

    def shutdown(self) -> None:
        """Shut down execution resources."""
        self._execution.shutdown()

    def health(self) -> dict[str, bool]:
        """Return execution service health information."""
        return {
            "healthy": True,
        }