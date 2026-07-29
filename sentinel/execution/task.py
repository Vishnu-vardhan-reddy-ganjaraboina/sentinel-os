"""
Task model for the Execution subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from sentinel.execution.constants import (
    DEFAULT_PRIORITY,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_PRIORITY,
    MIN_PRIORITY,
)


@dataclass(slots=True)
class Task:
    """
    Represents a unit of executable work.
    """

    callback: Callable[..., Any]

    args: tuple[Any, ...] = field(default_factory=tuple)

    kwargs: dict[str, Any] = field(default_factory=dict)

    name: str = ""

    priority: int = DEFAULT_PRIORITY

    timeout: int = DEFAULT_TIMEOUT_SECONDS

    metadata: dict[str, Any] = field(default_factory=dict)

    task_id: str = field(default_factory=lambda: str(uuid4()))

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    retries: int = 0

    def __post_init__(self) -> None:
        if not callable(self.callback):
            raise TypeError("callback must be callable.")

        if not (MIN_PRIORITY <= self.priority <= MAX_PRIORITY):
            raise ValueError(
                f"priority must be between "
                f"{MIN_PRIORITY} and {MAX_PRIORITY}."
            )

        if self.timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        if self.retries < 0:
            raise ValueError(
                "retries cannot be negative."
            )

        if not self.name:
            self.name = self.callback.__name__

    def execute(self) -> Any:
        """
        Execute the task.
        """
        return self.callback(*self.args, **self.kwargs)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the task.
        """
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority,
            "timeout": self.timeout,
            "retries": self.retries,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"Task("
            f"id={self.task_id}, "
            f"name={self.name}, "
            f"priority={self.priority})"
        )