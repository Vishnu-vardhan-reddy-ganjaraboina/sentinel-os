"""
Infrastructure exception hierarchy for Sentinel OS.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class InfrastructureError(SentinelError):
    """
    Base class for all infrastructure exceptions.
    """


class ConfigurationError(InfrastructureError):
    """
    Raised when configuration is invalid.
    """


class LoggingError(InfrastructureError):
    """
    Raised when logging initialization fails.
    """


class SchedulerError(InfrastructureError):
    """
    Raised for scheduler-related failures.
    """


class MonitorError(InfrastructureError):
    """
    Raised for monitor-related failures.
    """