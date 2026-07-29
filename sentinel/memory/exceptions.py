"""
Exceptions for the Sentinel Memory subsystem.
"""

from sentinel.core.exceptions import SentinelError


class MemoryError(SentinelError):
    """
    Base exception for all memory-related errors.
    """


class MemoryNotFoundError(MemoryError):
    """
    Raised when a memory entry cannot be found.
    """


class MemoryAlreadyExistsError(MemoryError):
    """
    Raised when attempting to register an existing memory entry.
    """


class InvalidMemoryError(MemoryError):
    """
    Raised when a memory entry is invalid.
    """


class MemoryExpiredError(MemoryError):
    """
    Raised when accessing an expired memory entry.
    """


class MemoryStorageError(MemoryError):
    """
    Raised when a memory storage operation fails.
    """