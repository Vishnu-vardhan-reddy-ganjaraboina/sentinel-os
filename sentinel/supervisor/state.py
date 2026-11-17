from __future__ import annotations

from enum import StrEnum


class SupervisorState(StrEnum):
    """Lifecycle states for the Sentinel Supervisor."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    RESTARTING = "restarting"
    FAILED = "failed"
    STOPPING = "stopping"
