"""
Exceptions for the Sentinel logging runtime.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class LoggingError(SentinelError):
    """
    Base exception for logging-related errors.
    """

    __slots__ = ()


class LogConfigurationError(LoggingError):
    """
    Raised when logging configuration is invalid.
    """

    __slots__ = ()


class LogFormatterError(LoggingError):
    """
    Raised when log formatting fails.
    """

    __slots__ = ()


class LogHandlerError(LoggingError):
    """
    Raised when a logging handler encounters an error.
    """

    __slots__ = ()


class LogWriteError(LoggingError):
    """
    Raised when writing a log record fails.
    """

    __slots__ = ()


class LoggerStateError(SentinelError):
    """
    Raised when the logger is used in an invalid state.
    """

    __slots__ = ()


__all__ = (
    "LogConfigurationError",
    "LogFormatterError",
    "LogHandlerError",
    "LogWriteError",
    "LoggerStateError",
    "LoggingError",
)