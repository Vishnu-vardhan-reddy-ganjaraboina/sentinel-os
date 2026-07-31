"""
Constants for the Sentinel Brain subsystem.
"""

from enum import StrEnum

DEFAULT_BRAIN_VERSION = "1.0.0"

DEFAULT_MAX_PLANNING_DEPTH = 5

DEFAULT_MAX_CONTEXT_ITEMS = 100


class BrainState(StrEnum):
    """
    Brain execution states.
    """

    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanStatus(StrEnum):
    """
    Planning lifecycle.
    """

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"