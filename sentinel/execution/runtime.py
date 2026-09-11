"""
Kernel runtime service for the Execution subsystem.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from sentinel.execution.command import CommandResult
from sentinel.execution.context import ExecutionContext
from sentinel.execution.service import ExecutionService
from sentinel.execution.task import Task
from sentinel.kernel.service import Service


class ExecutionRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for ExecutionService.

    The runtime service exposes the Execution subsystem API directly
    while retaining Kernel lifecycle management.
    """

    def __init__(
        self,
        execution: ExecutionService | None = None,
    ) -> None:
        super().__init__(
            "execution",
            dependencies=(),
        )

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

    def execute_task(
        self,
        task: Task,
    ) -> Any:
        """Execute a task."""
        return self._execution.execute_task(task)

    def submit(
        self,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Submit a callable for execution."""
        return self._execution.submit(
            callback,
            *args,
            **kwargs,
        )

    def cancel(
        self,
        task_id: str,
    ) -> bool:
        """Cancel a submitted task."""
        return self._execution.cancel(task_id)

    def get_context(
        self,
        task_id: str,
    ) -> ExecutionContext | None:
        """Return the execution context for a task."""
        return self._execution.get_context(task_id)

    def run_command(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """Execute a command."""
        return self._execution.run_command(command)

    def run_command_checked(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """Execute a command and raise on failure."""
        return self._execution.run_command_checked(command)

    def start_process(
        self,
        command: Sequence[str],
    ) -> int:
        """Start a long-running process."""
        return self._execution.start_process(command)

    def wait_for_process(
        self,
        timeout: float | None = None,
    ) -> int:
        """Wait for the running process."""
        return self._execution.wait_for_process(timeout)

    def terminate_process(self) -> None:
        """Terminate the running process."""
        self._execution.terminate_process()

    def read_process_output(self) -> tuple[str, str]:
        """Read stdout and stderr from the managed process."""
        return self._execution.read_process_output()

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

        if self._initialized:
            return

        self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down execution resources.

        Shutdown is idempotent.
        """
        if self._shutdown:
            return

        self._execution.shutdown()

        self._initialized = False
        self._shutdown = True

    def health(self) -> dict[str, bool]:
        """Return execution service health information."""
        return {
            "healthy": (
                self._initialized
                and not self._shutdown
            ),
        }