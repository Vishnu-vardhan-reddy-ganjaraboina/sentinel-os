"""
Constants for the Sentinel Automation subsystem.
"""

from enum import Enum

DEFAULT_WORKFLOW_VERSION = "1.0.0"

DEFAULT_RETRY_COUNT = 3

DEFAULT_RETRY_DELAY = 5


class WorkflowStatus(str, Enum):
    """
    Workflow execution status.
    """

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class TriggerType(str, Enum):
    """
    Supported trigger types.
    """

    MANUAL = "manual"

    EVENT = "event"

    SCHEDULE = "schedule"

    WEBHOOK = "webhook"

    CONDITION = "condition"