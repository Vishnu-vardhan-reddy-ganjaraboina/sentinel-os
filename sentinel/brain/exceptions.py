"""
Exceptions for the Sentinel Brain subsystem.
"""

from sentinel.core.exceptions import SentinelError


class BrainError(SentinelError):
    """
    Base exception for all brain-related errors.
    """


class ContextError(BrainError):
    """
    Raised when an execution context is invalid.
    """


class PlanningError(BrainError):
    """
    Raised when planning fails.
    """


class ExecutionError(BrainError):
    """
    Raised when brain execution fails.
    """


class EngineError(BrainError):
    """
    Raised when the brain engine encounters an error.
    """


class InvalidPlanError(BrainError):
    """
    Raised when a generated plan is invalid.
    """