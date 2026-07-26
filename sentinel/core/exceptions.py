"""
sentinel.core.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~

Root exception hierarchy for Sentinel OS.

Every custom exception in Sentinel should ultimately inherit from
SentinelError.
"""

from __future__ import annotations

from typing import Any


class SentinelError(Exception):
    """
    Base exception for the Sentinel platform.

    Parameters
    ----------
    message:
        Human-readable error message.

    details:
        Optional structured metadata describing the error.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details or {}

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(message={self.args[0]!r}, details={self.details!r})"
        )


class ConfigurationError(SentinelError):
    """Raised when configuration is invalid."""


class ValidationError(SentinelError):
    """Raised when validation fails."""


class SerializationError(SentinelError):
    """Raised when serialization fails."""


class DeserializationError(SentinelError):
    """Raised when deserialization fails."""


class NotFoundError(SentinelError):
    """Raised when an object cannot be found."""


class AlreadyExistsError(SentinelError):
    """Raised when an object already exists."""


class PermissionDeniedError(SentinelError):
    """Raised when access is denied."""


class OperationError(SentinelError):
    """Raised when an operation cannot be completed."""


class TimeoutError(SentinelError):
    """Raised when an operation times out."""