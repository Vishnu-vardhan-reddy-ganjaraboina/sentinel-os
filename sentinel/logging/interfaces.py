"""
Interfaces for the Sentinel logging runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel.logging.models import LogRecord


class LogHandler(ABC):
    """
    Abstract base class for Sentinel log handlers.
    """

    @abstractmethod
    def emit(self, record: LogRecord) -> None:
        """
        Handle a single log record.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Release handler resources.
        """
        raise NotImplementedError


__all__ = (
    "LogHandler",
)