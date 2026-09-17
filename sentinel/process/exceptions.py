"""
Exceptions raised by the Sentinel process subsystem.
"""


class ProcessError(Exception):
    """Base exception for process-host failures."""


class ProcessStateError(ProcessError):
    """Raised when a process operation is invalid for its state."""


class ProcessStartupError(ProcessError):
    """Raised when the Sentinel process cannot start."""


class ProcessShutdownError(ProcessError):
    """Raised when the Sentinel process cannot shut down cleanly."""


class ProcessControlError(ProcessError):
    """Raised when process control cannot be completed."""
