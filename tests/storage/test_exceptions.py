from sentinel.core.exceptions import SentinelError
from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageError,
    StorageKeyNotFoundError,
    StoragePermissionError,
    StorageSerializationError,
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
    assert isinstance(
        StorageBackendError("Backend failure"),
        StorageError,
    )


def test_serialization_error():
    assert isinstance(
        StorageSerializationError("Serialization failure"),
        StorageError,
    )


def test_permission_error():
    assert isinstance(
        StoragePermissionError("Permission denied"),
        StorageError,
    )


def test_transaction_error():
    assert isinstance(
        StorageTransactionError("Transaction failed"),
        StorageError,
    )