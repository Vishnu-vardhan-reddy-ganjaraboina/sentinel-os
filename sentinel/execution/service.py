"""
High-level execution service.

This module provides a unified interface for task execution, command
execution, and process management.
"""

from __future__ import annotations

from typing import Any, Sequence

from sentinel.execution.command import CommandExecutor, CommandResult
from sentinel.execution.context import ExecutionContext
from sentinel.execution.executor import DefaultExecutor
from sentinel.execution.process import ProcessManager
from sentinel.execution.task import Task


class ExecutionService:
    """
    High-level service for the Execution subsystem.
    """

    def __init__(
        self,
        executor: DefaultExecutor | None = None,
        command_executor: CommandExecutor | None = None,
        process_manager: ProcessManager | None = None,
    ) -> None:
        self._executor = executor or DefaultExecutor()
        self._command_executor = command_executor or CommandExecutor()
        self._process_manager = process_manager or ProcessManager()

    @property
    def executor(self) -> DefaultExecutor:
        return self._executor

    @property
    def command_executor(self) -> CommandExecutor:
        return self._command_executor

    @property
    def process_manager(self) -> ProcessManager:
        return self._process_manager

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    def execute_task(self, task: Task) -> Any:
        """
        Execute a Task.
        """
        return self._executor.execute(task)

    def submit(
        self,
        callback,
        *args,
        **kwargs,
    ) -> str:
        """
        Submit a callable for execution.
        """
        return self._executor.submit(
            callback,
            *args,
            **kwargs,
        )

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a submitted task.
        """
        return self._executor.cancel(task_id)

    def get_context(
        self,
        task_id: str,
    ) -> ExecutionContext | None:
        """
        Return the execution context for a task.
        """
        return self._executor.get_context(task_id)

    def shutdown(self) -> None:
        """
        Shut down the executor.
        """
        self._executor.shutdown()

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def run_command(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """
        Execute a command.
        """
        return self._command_executor.run(command)

    def run_command_checked(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """
        Execute a command and raise on failure.
        """
        return self._command_executor.run_checked(command)

    # ------------------------------------------------------------------
    # Process management
    # ------------------------------------------------------------------

    def start_process(
        self,
        command: Sequence[str],
    ) -> int:
        """
        Start a long-running process.
        """
        return self._process_manager.start(command)

    def wait_for_process(
        self,
        timeout: float | None = None,
    ) -> int:
        """
        Wait for the running process.
        """
        return self._process_manager.wait(timeout)

    def terminate_process(self) -> None:
        """
        Terminate the running process.
        """
        self._process_manager.terminate()

    def read_process_output(self) -> tuple[str, str]:
        """
        Read stdout and stderr from the managed process.
        """
        return self._process_manager.read_output()