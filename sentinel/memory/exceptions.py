"""
Exceptions for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class MemoryError(SentinelError):
    """
    Base exception for all memory-related errors.
    """


class MemoryNotFoundError(MemoryError):
    """
    Raised when a requested memory entry does not exist.
    """


class MemoryAlreadyExistsError(MemoryError):
    """
    Raised when attempting to add a memory entry that already exists.
    """


class MemoryExpiredError(MemoryError):
    """
    Raised when attempting to use an expired memory entry.
    """


class MemoryArchivedError(MemoryError):
    """
    Raised when attempting to modify an archived memory entry.
    """


class InvalidMemoryError(MemoryError):
    """
    Raised when a memory entry is invalid.
    """
