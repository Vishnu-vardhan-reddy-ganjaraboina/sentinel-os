"""
Exceptions raised by the Sentinel control subsystem.
"""


class ControlError(Exception):
    """Base exception for control-plane failures."""


class ControlProtocolError(ControlError):
    """Raised when a control message is invalid."""


class ControlConnectionError(ControlError):
    """Raised when the control endpoint cannot be reached."""


class ControlRequestError(ControlError):
    """Raised when a control request cannot be processed."""
