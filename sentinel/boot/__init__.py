"""
Public API for the Sentinel boot subsystem.
"""

from sentinel.boot.configuration import BootConfiguration
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
from sentinel.boot.system_factory import SystemFactory

__all__ = [
    "BootConfiguration",
    "BootConfigurationError",
    "BootError",
    "BootManager",
    "BootShutdownError",
    "BootProfile",
    "BootResult",
    "BootStartupError",
    "BootStateError",
    "SystemFactory",
]
