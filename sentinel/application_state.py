"""
Application lifecycle states for Sentinel OS.
"""

from enum import Enum


class ApplicationState(str, Enum):
    """Lifecycle states for Sentinel applications."""

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"