"""
Unit tests for infrastructure exceptions.
"""

from sentinel.core.exceptions import SentinelError
from sentinel.infrastructure.exceptions import (
    ConfigurationError,
    InfrastructureError,
    LoggingError,
    MonitorError,
    SchedulerError,
)


def test_configuration_error():
    error = ConfigurationError("Invalid configuration")

    assert isinstance(error, ConfigurationError)
    assert isinstance(error, InfrastructureError)
    assert isinstance(error, SentinelError)
    assert str(error) == "Invalid configuration"


def test_logging_error():
    error = LoggingError("Logging failed")

    assert isinstance(error, LoggingError)
    assert isinstance(error, InfrastructureError)
    assert isinstance(error, SentinelError)


def test_scheduler_error():
    error = SchedulerError("Scheduler failure")

    assert isinstance(error, SchedulerError)
    assert isinstance(error, InfrastructureError)
    assert isinstance(error, SentinelError)


def test_monitor_error():
    error = MonitorError("Monitor failure")

    assert isinstance(error, MonitorError)
    assert isinstance(error, InfrastructureError)
    assert isinstance(error, SentinelError)


def test_catch_infrastructure_error():
    try:
        raise SchedulerError("Failure")
    except InfrastructureError:
        caught = True
    else:
        caught = False

    assert caught


def test_catch_sentinel_error():
    try:
        raise LoggingError("Failure")
    except SentinelError:
        caught = True
    else:
        caught = False

    assert caught