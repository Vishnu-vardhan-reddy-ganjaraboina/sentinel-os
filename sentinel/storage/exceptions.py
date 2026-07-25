"""
Storage exceptions for Sentinel OS.
"""

from __future__ import annotations


class StorageError(Exception):
    """Base class for all storage errors."""


class StorageConnectionError(StorageError):
    """Raised when a storage backend cannot be reached."""


class StorageNotFoundError(StorageError):
    """Raised when requested data does not exist."""


class StorageWriteError(StorageError):
    """Raised when data cannot be written."""


class StorageReadError(StorageError):
    """Raised when data cannot be read."""