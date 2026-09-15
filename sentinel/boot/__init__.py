"""
Public API for the Sentinel boot subsystem.
"""

from sentinel.boot.exceptions import (
    BootConfigurationError,
    BootError,
    BootShutdownError,
    BootStartupError,
    BootStateError,
)
from sentinel.boot.manager import BootManager
from sentinel.boot.profile import BootProfile
from sentinel.boot.result import BootResult

__all__ = [
    "BootConfigurationError",
    "BootError",
    "BootManager",
    "BootShutdownError",
    "BootProfile",
    "BootResult",
    "BootStartupError",
    "BootStateError",
]
