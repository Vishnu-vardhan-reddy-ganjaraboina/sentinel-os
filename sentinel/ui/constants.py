"""
Constants for the Sentinel UI subsystem.
"""

from __future__ import annotations

from enum import Enum

DEFAULT_UI_VERSION = "1.0.0"


class Theme(Enum):
    """
    Supported UI themes.
    """

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class WindowState(Enum):
    """
    Window lifecycle state.
    """

    CREATED = "created"
    OPEN = "open"
    MINIMIZED = "minimized"
    CLOSED = "closed"


class ViewState(Enum):
    """
    View lifecycle state.
    """

    CREATED = "created"
    ACTIVE = "active"
    HIDDEN = "hidden"