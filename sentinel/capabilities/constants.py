"""
Constants for the Capabilities subsystem.
"""

from __future__ import annotations

from enum import Enum

DEFAULT_CAPABILITY_VERSION = "1.0.0"


class CapabilityCategory(str, Enum):
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


class CapabilityStatus(str, Enum):
    """
    Lifecycle status of a capability.
    """

    ENABLED = "enabled"
    DISABLED = "disabled"