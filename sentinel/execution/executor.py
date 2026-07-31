"""
Production-grade executor for the Execution subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Any

from sentinel.execution.constants import DEFAULT_MAX_WORKERS, TaskStatus
from sentinel.execution.context import ExecutionContext
from sentinel.execution.interfaces import Executor
from sentinel.execution.task import Task


class DefaultExecutor(Executor):
    """
    Thread-pool-backed executor.

    This implementation supports concurrent execution while tracking
    execution state, contexts, and task statistics.
    """

    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

        self._contexts: dict[str, ExecutionContext] = {}
        self._futures: dict[str, Future[Any]] = {}

        self._shutdown = False
        self._lock = Lock()

        self._submitted = 0
        self._completed = 0
        self._failed = 0
        self._cancelled = 0

    def submit(
        self,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        if self._shutdown:
            raise RuntimeError("Executor has been shut down.")

        task = Task(
            callback=callback,
            args=args,
            kwargs=kwargs,
        )

        context = ExecutionContext(task.task_id)

        with self._lock:
            self._contexts[task.task_id] = context
            self._submitted += 1

        future = self._pool.submit(self._run_task, task, context)

        with self._lock:
            self._futures[task.task_id] = future

        return task.task_id

    def execute(self, task: Task) -> Any:
        if self._shutdown:
            raise RuntimeError("Executor has been shut down.")

        context = ExecutionContext(task.task_id)

        with self._lock:
            self._contexts[task.task_id] = context
            self._submitted += 1

        return self._run_task(task, context)

    def _run_task(
        self,
        task: Task,
        context: ExecutionContext,
    ) -> Any:
        context.mark_running()

        try:
            result = task.execute()

            context.mark_completed(result)

            with self._lock:
                self._completed += 1

            return result

        except Exception as exc:
            context.mark_failed(exc)

            with self._lock:
                self._failed += 1

            raise

    def cancel(
        self,
        task_id: str,
    ) -> bool:
        future = self._futures.get(task_id)

        if future is None:
            return False

        cancelled = future.cancel()

        if cancelled:
            context = self._contexts.get(task_id)

            if context is not None:
                context.mark_cancelled()

            with self._lock:
                self._cancelled += 1

        return cancelled

    def is_running(
        self,
        task_id: str,
    ) -> bool:
        context = self._contexts.get(task_id)

        return (
            context is not None
            and context.status == TaskStatus.RUNNING
        )

    def get_context(
        self,
        task_id: str,
    ) -> ExecutionContext | None:
        return self._contexts.get(task_id)

    def stats(self) -> dict[str, int]:
        """
        Return executor statistics.
        """
        with self._lock:
            running = sum(
                1
                for context in self._contexts.values()
                if context.status == TaskStatus.RUNNING
            )

            return {
                "submitted": self._submitted,
                "running": running,
                "completed": self._completed,
                "failed": self._failed,
                "cancelled": self._cancelled,
            }

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True

        self._pool.shutdown(wait=True)