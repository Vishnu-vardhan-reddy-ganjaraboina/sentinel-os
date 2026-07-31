"""
Service lifecycle states for Sentinel OS.
"""

from __future__ import annotations

from enum import StrEnum


class ServiceState(StrEnum):
    """Represents the lifecycle state of a service."""

    CREATED = "created"
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"