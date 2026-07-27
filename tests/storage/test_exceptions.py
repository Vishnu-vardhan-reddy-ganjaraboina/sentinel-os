from sentinel.core.exceptions import SentinelError
from sentinel.storage.exceptions import (
    StorageError,
    StorageKeyNotFoundError,
    StorageBackendError,
    StorageSerializationError,
    StoragePermissionError,
    StorageTransactionError,
)


def test_storage_error():
    error = StorageError("error")

    assert isinstance(error, SentinelError)
    assert str(error) == "error"


def test_key_not_found():
    error = StorageKeyNotFoundError("missing")

    assert isinstance(error, StorageError)
    assert isinstance(error, KeyError)


def test_backend_error():
    assert isinstance(StorageBackendError(), StorageError)


def test_serialization_error():
    assert isinstance(StorageSerializationError(), StorageError)


def test_permission_error():
    assert isinstance(StoragePermissionError(), StorageError)


def test_transaction_error():
    assert isinstance(StorageTransactionError(), StorageError)