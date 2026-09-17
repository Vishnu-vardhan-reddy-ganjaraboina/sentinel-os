"""
Sentinel process lifecycle states.
"""

from enum import Enum


class ProcessState(str, Enum):
    """Lifecycle states for the Sentinel process host."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
