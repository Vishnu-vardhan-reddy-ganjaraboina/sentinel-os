"""
Task scheduler for Sentinel OS.
"""

from __future__ import annotations

import threading
import time

from dataclasses import dataclass, field
from typing import Callable

from sentinel.kernel.service import Service


@dataclass(slots=True)
class ScheduledTask:
    """Represents a scheduled task."""

    name: str
    interval: float
    callback: Callable[[], None]
    last_run: float = field(default_factory=time.monotonic)


class Scheduler(Service):
    """
    Executes scheduled background tasks.
    """

    def __init__(self) -> None:
        super().__init__("scheduler")

        self._tasks: dict[str, ScheduledTask] = {}

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def initialize(self) -> None:
        """Start the scheduler."""

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="Scheduler",
        )

        self._thread.start()

    def shutdown(self) -> None:
        """Stop the scheduler."""

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join()

    def add_task(
        self,
        name: str,
        interval: float,
        callback: Callable[[], None],
    ) -> None:
        """Register a scheduled task."""

        self._tasks[name] = ScheduledTask(
            name=name,
            interval=interval,
            callback=callback,
        )

    def remove_task(self, name: str) -> None:
        """Remove a scheduled task."""

        self._tasks.pop(name, None)

    def _run(self) -> None:
        """Scheduler execution loop."""

        while not self._stop_event.is_set():

            now = time.monotonic()

            for task in self._tasks.values():

                if now - task.last_run >= task.interval:

                    task.callback()

                    task.last_run = now

            self._stop_event.wait(0.5)