"""
Constants for the Sentinel Brain subsystem.
"""

from enum import Enum

DEFAULT_BRAIN_VERSION = "1.0.0"

DEFAULT_MAX_PLANNING_DEPTH = 5

DEFAULT_MAX_CONTEXT_ITEMS = 100


class BrainState(str, Enum):
    """
    Brain execution states.
    """

    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanStatus(str, Enum):
    """
    Planning lifecycle.
    """

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"