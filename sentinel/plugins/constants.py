"""
Constants for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from enum import Enum

DEFAULT_PLUGIN_VERSION = "1.0.0"


class PluginState(Enum):
    """
    Plugin lifecycle state.
    """

    REGISTERED = "registered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"


class PluginType(Enum):
    """
    Supported plugin categories.
    """

    CORE = "core"
    SYSTEM = "system"
    EXTENSION = "extension"
    USER = "user"