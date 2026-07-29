"""
Execution context for the Execution subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sentinel.execution.constants import TaskStatus


@dataclass(slots=True)
class ExecutionContext:
    """
    Stores the runtime state and outcome of a task execution.
    """

    task_id: str

    status: TaskStatus = TaskStatus.PENDING

    started_at: datetime | None = None

    finished_at: datetime | None = None

    result: Any = None

    error: Exception | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        """
        Return execution duration in seconds.
        """
        if self.started_at is None or self.finished_at is None:
            return None

        return (self.finished_at - self.started_at).total_seconds()

    def mark_running(self) -> None:
        """
        Mark the task as running.
        """
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def mark_completed(self, result: Any = None) -> None:
        """
        Mark the task as completed successfully.
        """
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, error: Exception) -> None:
        """
        Mark the task as failed.
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(UTC)

    def mark_cancelled(self) -> None:
        """
        Mark the task as cancelled.
        """
        self.status = TaskStatus.CANCELLED
        self.finished_at = datetime.now(UTC)

    @property
    def is_finished(self) -> bool:
        """
        Return True if the task has reached a terminal state.
        """
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )