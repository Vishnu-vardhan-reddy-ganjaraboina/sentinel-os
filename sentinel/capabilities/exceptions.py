"""
Exceptions for the Capabilities subsystem.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class CapabilityError(SentinelError):
    """
    Base exception for all capability-related errors.
    """


class CapabilityNotFoundError(CapabilityError):
    """
    Raised when a requested capability does not exist.
    """


class CapabilityAlreadyExistsError(CapabilityError):
    """
    Raised when attempting to register a capability with an ID
    that already exists.
    """


class CapabilityDisabledError(CapabilityError):
    """
    Raised when attempting to execute a disabled capability.
    """


class InvalidCapabilityError(CapabilityError):
    """
    Raised when a capability implementation is invalid.
    """


class CapabilityExecutionError(CapabilityError):
    """
    Raised when a capability fails during execution.
    """