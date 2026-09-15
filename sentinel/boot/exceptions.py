"""
Exceptions raised by the Sentinel boot subsystem.
"""


class BootError(Exception):
    """Base exception for boot-related failures."""


class BootConfigurationError(BootError):
    """Raised when the boot configuration is invalid."""


class BootStateError(BootError):
    """Raised when a boot operation is invalid for the current state."""


class BootStartupError(BootError):
    """Raised when Sentinel fails during startup."""


class BootShutdownError(BootError):
    """Raised when Sentinel fails during shutdown."""
