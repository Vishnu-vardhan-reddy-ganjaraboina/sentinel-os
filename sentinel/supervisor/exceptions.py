from __future__ import annotations


class SupervisorError(RuntimeError):
    """Base exception for Supervisor failures."""


class SupervisorStateError(SupervisorError):
    """Raised when a Supervisor operation is invalid for its state."""


class SupervisorStartupError(SupervisorError):
    """Raised when the Supervisor cannot start."""


class SupervisorShutdownError(SupervisorError):
    """Raised when the Supervisor cannot shut down."""


class SupervisorRestartError(SupervisorError):
    """Raised when the Supervisor cannot restart its process."""
