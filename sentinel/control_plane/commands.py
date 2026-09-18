"""
Commands supported by the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from enum import StrEnum


class KernelCommand(StrEnum):
    """Commands exposed by the Kernel Control Plane."""

    SYSTEM_STATUS = "system.status"
    SYSTEM_HEALTH = "system.health"

    SERVICE_LIST = "service.list"
    SERVICE_STATUS = "service.status"

    SERVICE_START = "service.start"
    SERVICE_STOP = "service.stop"
    SERVICE_RESTART = "service.restart"