"""
Storage exception hierarchy for Sentinel OS.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class StorageError(SentinelError):
    """
    Base class for all storage-related exceptions.
    """


class StorageConnectionError(StorageError):
    """
    Raised when a storage backend cannot establish or maintain a connection.
    """


class StorageReadError(StorageError):
    """
    Raised when reading from storage fails.
    """


class StorageWriteError(StorageError):
    """
    Raised when writing to storage fails.
    """


class StorageKeyNotFoundError(StorageError, KeyError):
    """
    Raised when a requested storage key does not exist.
    """


class StorageBackendError(StorageError):
    """
    Raised when a storage backend encounters an unrecoverable error.
    """


class StorageSerializationError(StorageError):
    """
    Raised when serialization or deserialization fails.
    """


class StoragePermissionError(StorageError):
    """
    Raised when access to storage is denied.
    """


class StorageTransactionError(StorageError):
    """
    Raised when a storage transaction fails.
    """