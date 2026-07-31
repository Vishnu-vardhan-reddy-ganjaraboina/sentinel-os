"""
Constants for the Sentinel Automation subsystem.
"""

from enum import StrEnum

DEFAULT_WORKFLOW_VERSION = "1.0.0"

DEFAULT_RETRY_COUNT = 3

DEFAULT_RETRY_DELAY = 5


class WorkflowStatus(StrEnum):
    """
    Workflow execution status.
    """

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class TriggerType(StrEnum):
    """
    Supported trigger types.
    """

    MANUAL = "manual"

    EVENT = "event"

    SCHEDULE = "schedule"

    WEBHOOK = "webhook"

    CONDITION = "condition"