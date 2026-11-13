"""
Manager for the Sentinel logging runtime.
"""

from __future__ import annotations

from threading import RLock

from sentinel.logging.interfaces import LogHandler
from sentinel.logging.models import LogRecord


class LogManager:
    """
    Coordinate log records across registered handlers.
    """

    def __init__(
        self,
        handlers: list[LogHandler] | None = None,
    ) -> None:
        self._lock = RLock()
        self._handlers: list[LogHandler] = []

        for handler in handlers or []:
            self.add_handler(handler)

    @property
    def handlers(self) -> tuple[LogHandler, ...]:
        """
        Return the currently registered handlers.
        """
        with self._lock:
            return tuple(self._handlers)

    def add_handler(self, handler: LogHandler) -> None:
        """
        Register a handler.
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def remove_handler(self, handler: LogHandler) -> None:
        """
        Remove a registered handler.
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def emit(self, record: LogRecord) -> None:
        """
        Send a log record to every registered handler.

        Handler failures are isolated so one failing handler does not prevent
        other handlers from receiving the record. A single handler failure is
        re-raised directly. Multiple failures are raised as an ExceptionGroup.
        """
        with self._lock:
            handlers = tuple(self._handlers)

        failures: list[BaseException] = []

        for handler in handlers:
            try:
                handler.emit(record)
            except BaseException as exc:
                failures.append(exc)

        if len(failures) == 1:
            raise failures[0]

        if failures:
            raise BaseExceptionGroup(
                "One or more logging handlers failed",
                failures,
            )

    def close(self) -> None:
        """
        Close all registered handlers.
        """
        with self._lock:
            handlers = tuple(self._handlers)

        for handler in handlers:
            handler.close()


__all__ = (
    "LogManager",
)
