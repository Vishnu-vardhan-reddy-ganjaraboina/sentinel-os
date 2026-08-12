"""
Tests for logging exceptions.
"""

from __future__ import annotations

import pytest

from sentinel.core.exceptions import SentinelError
from sentinel.logging.exceptions import (
    LogConfigurationError,
    LogFormatterError,
    LoggerStateError,
    LoggingError,
    LogHandlerError,
    LogWriteError,
)


@pytest.mark.parametrize(
    "exception_type",
    [
        LogConfigurationError,
        LogFormatterError,
        LogHandlerError,
        LogWriteError,
    ],
)
def test_logging_errors_inherit_from_logging_error(
    exception_type: type[LoggingError],
) -> None:
    assert issubclass(exception_type, LoggingError)
    assert issubclass(exception_type, SentinelError)


def test_logging_error_inheritance() -> None:
    assert issubclass(LoggingError, SentinelError)


def test_logger_state_error_inheritance() -> None:
    assert issubclass(LoggerStateError, SentinelError)


def test_exceptions_can_be_raised() -> None:
    with pytest.raises(LoggingError):
        raise LogConfigurationError("Invalid logging configuration")

    with pytest.raises(LoggingError):
        raise LogFormatterError("Formatting failed")

    with pytest.raises(LoggingError):
        raise LogHandlerError("Handler failed")

    with pytest.raises(LoggingError):
        raise LogWriteError("Write failed")

    with pytest.raises(LoggerStateError):
        raise LoggerStateError("Invalid logger state")