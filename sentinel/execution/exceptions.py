"""
Exceptions for the Execution subsystem.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class ExecutionError(SentinelError):
    """
    Base exception for all execution-related errors.
    """


class TaskError(ExecutionError):
    """
    Raised when an execution task is invalid or fails.
    """


class CommandError(ExecutionError):
    """
    Raised when executing an external command fails.
    """


class ProcessError(ExecutionError):
    """
    Raised when a managed process encounters an error.
    """


class ExecutionTimeoutError(ExecutionError):
    """
    Raised when execution exceeds the configured timeout.
    """


class TaskCancelledError(ExecutionError):
    """
    Raised when a task has been cancelled before completion.
    """