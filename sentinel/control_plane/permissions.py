"""
Authorization types for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from enum import StrEnum


class ControlPermission(StrEnum):
    """Permissions required by Kernel Control Plane commands."""

    READ = "read"
    CONTROL = "control"