"""
Constants for the Execution subsystem.

This module defines default values and limits used by the execution
framework.
"""

from __future__ import annotations

from enum import StrEnum

# ---------------------------------------------------------------------------
# Execution Defaults
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS: int = 300
DEFAULT_MAX_WORKERS: int = 4
DEFAULT_PRIORITY: int = 5

# ---------------------------------------------------------------------------
# Task Priorities
# ---------------------------------------------------------------------------

MIN_PRIORITY: int = 1
MAX_PRIORITY: int = 10

# ---------------------------------------------------------------------------
# Execution States
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    """
    Represents the lifecycle of an execution task.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Command Execution
# ---------------------------------------------------------------------------

DEFAULT_SHELL: bool = False
CAPTURE_OUTPUT: bool = True
TEXT_MODE: bool = True

# ---------------------------------------------------------------------------
# Process Limits
# ---------------------------------------------------------------------------

DEFAULT_TERMINATE_TIMEOUT: int = 5
DEFAULT_KILL_TIMEOUT: int = 2