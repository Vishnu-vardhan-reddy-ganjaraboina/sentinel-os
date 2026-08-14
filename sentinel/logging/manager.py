"""
Manager for the Sentinel logging runtime.
"""

from __future__ import annotations

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
        self._handlers: list[LogHandler] = list(handlers or [])

    @property
    def handlers(self) -> tuple[LogHandler, ...]:
        """
        Return the currently registered handlers.
        """
        return tuple(self._handlers)

    def add_handler(self, handler: LogHandler) -> None:
        """
        Register a handler.
        """
        if handler not in self._handlers:
            self._handlers.append(handler)

    def remove_handler(self, handler: LogHandler) -> None:
        """
        Remove a registered handler.
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit(self, record: LogRecord) -> None:
        """
        Send a log record to every registered handler.
        """
        for handler in self._handlers:
            handler.emit(record)

    def close(self) -> None:
        """
        Close all registered handlers.
        """
        for handler in self._handlers:
            handler.close()


__all__ = (
    "LogManager",
)