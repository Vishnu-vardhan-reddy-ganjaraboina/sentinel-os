"""
Constants for the Capabilities subsystem.
"""

from __future__ import annotations

from enum import StrEnum

DEFAULT_CAPABILITY_VERSION = "1.0.0"


class CapabilityCategory(StrEnum):
    """
    Categories of capabilities supported by Sentinel.
    """

    FILESYSTEM = "filesystem"
    DATABASE = "database"
    WEB = "web"
    AI = "ai"
    SYSTEM = "system"
    NETWORK = "network"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    CUSTOM = "custom"


class CapabilityStatus(StrEnum):
    """
    Lifecycle status of a capability.
    """

    ENABLED = "enabled"
    DISABLED = "disabled"