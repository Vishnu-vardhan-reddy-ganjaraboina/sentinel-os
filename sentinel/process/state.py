"""
Sentinel process lifecycle states.
"""

from enum import StrEnum


class ProcessState(StrEnum):
    """Lifecycle states for the Sentinel process host."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
