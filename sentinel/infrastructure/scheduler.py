"""
Task scheduler for Sentinel OS.

Provides a lightweight background scheduler responsible for executing
periodic tasks safely and reliably.
"""

from __future__ import annotations

import time

from dataclasses import dataclass, field
from threading import Event, RLock, Thread
from typing import Callable

from sentinel.infrastructure.logger import get_logger
from sentinel.kernel.exceptions import (
    DuplicateTaskError,
    TaskNotFoundError,
)
from sentinel.kernel.service import Service

logger = get_logger(__name__)


@dataclass(slots=True)
class ScheduledTask:
    """
    Represents a scheduled task.

    Attributes:
        name:
            Unique task name.

        interval:
            Execution interval in seconds.

        callback:
            Function to execute.

        enabled:
            Whether the task is enabled.

        last_run:
            Last execution timestamp based on monotonic clock.
    """

    name: str
    interval: float
    callback: Callable[[], None]
    enabled: bool = True
    last_run: float = field(default_factory=time.monotonic)


class Scheduler(Service):
    """
    Executes background tasks at fixed intervals.

    The scheduler runs inside a dedicated daemon thread and guarantees
    that one failing task will not stop the scheduler itself.
    """

    from sentinel.infrastructure.constants import (
    DEFAULT_SCHEDULER_POLL_INTERVAL,
)

    POLL_INTERVAL = DEFAULT_SCHEDULER_POLL_INTERVAL
    

    def __init__(self) -> None:
        """Initialize the scheduler."""
        super().__init__("scheduler")

        self._tasks: dict[str, ScheduledTask] = {}

        self._lock = RLock()

        self._stop_event = Event()

        self._thread: Thread | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def initialize(self) -> None:
        """Start the scheduler."""

        with self._lock:

            if self._thread is not None and self._thread.is_alive():
                return

            logger.info("Starting scheduler.")

            self._stop_event.clear()

            self._thread = Thread(
                target=self._run,
                daemon=True,
                name="Scheduler",
            )

            self._thread.start()

    def shutdown(self) -> None:
        """Stop the scheduler."""

        logger.info("Stopping scheduler.")

        self._stop_event.set()

        if self._thread is not None:

            self._thread.join()

            self._thread = None

    # ------------------------------------------------------------------ #
    # Task Management
    # ------------------------------------------------------------------ #

    def add_task(
        self,
        name: str,
        interval: float,
        callback: Callable[[], None],
    ) -> None:
        """
        Register a new scheduled task.

        Args:
            name:
                Unique task name.

            interval:
                Execution interval in seconds.

            callback:
                Function executed periodically.

        Raises:
            ValueError:
                If interval is invalid.

            DuplicateTaskError:
                If a task already exists.
        """

        if interval <= 0:
            raise ValueError(
                "Task interval must be greater than zero."
            )

        with self._lock:

            if name in self._tasks:
                raise DuplicateTaskError(
                    f"Task '{name}' already exists."
                )

            self._tasks[name] = ScheduledTask(
                name=name,
                interval=interval,
                callback=callback,
            )

        logger.info("Registered task '%s'.", name)

    def remove_task(
        self,
        name: str,
    ) -> None:
        """
        Remove a scheduled task.

        Raises:
            TaskNotFoundError:
                If task does not exist.
        """

        with self._lock:

            if name not in self._tasks:
                raise TaskNotFoundError(
                    f"Task '{name}' does not exist."
                )

            del self._tasks[name]

        logger.info("Removed task '%s'.", name)

    def enable_task(
        self,
        name: str,
    ) -> None:
        """Enable a task."""

        self._get_task(name).enabled = True

    def disable_task(
        self,
        name: str,
    ) -> None:
        """Disable a task."""

        self._get_task(name).enabled = False

    def get_task(
        self,
        name: str,
    ) -> ScheduledTask:
        """
        Return a task snapshot.
        """

        task = self._get_task(name)

        return ScheduledTask(
            name=task.name,
            interval=task.interval,
            callback=task.callback,
            enabled=task.enabled,
            last_run=task.last_run,
        )

    def get_tasks(
        self,
    ) -> dict[str, ScheduledTask]:
        """
        Return all registered tasks.
        """

        with self._lock:

            return {
                name: ScheduledTask(
                    name=task.name,
                    interval=task.interval,
                    callback=task.callback,
                    enabled=task.enabled,
                    last_run=task.last_run,
                )
                for name, task in self._tasks.items()
            }

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _run(self) -> None:
        """Main scheduler loop."""

        logger.info("Scheduler thread started.")

        while not self._stop_event.is_set():

            now = time.monotonic()

            with self._lock:
                tasks = list(self._tasks.values())

            for task in tasks:

                if not task.enabled:
                    continue

                if now - task.last_run < task.interval:
                    continue

                self._execute(task, now)

            self._stop_event.wait(self.POLL_INTERVAL)

        logger.info("Scheduler thread stopped.")

    def _execute(
        self,
        task: ScheduledTask,
        now: float,
    ) -> None:
        """
        Execute a scheduled task safely.
        """

        try:

            task.callback()

            task.last_run = now

        except Exception:

            logger.exception(
                "Scheduled task '%s' failed.",
                task.name,
            )

    def _get_task(
        self,
        name: str,
    ) -> ScheduledTask:
        """
        Return a registered task.

        Raises:
            TaskNotFoundError:
                If task is unknown.
        """

        with self._lock:

            try:
                return self._tasks[name]

            except KeyError as exc:

                raise TaskNotFoundError(
                    f"Unknown task '{name}'."
                ) from exc