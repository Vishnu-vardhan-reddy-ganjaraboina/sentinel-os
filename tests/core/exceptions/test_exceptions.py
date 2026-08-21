from sentinel.core.exceptions import (
    AlreadyExistsError,
    ConfigurationError,
    DeserializationError,
    NotFoundError,
    OperationError,
    PermissionDeniedError,
    SentinelError,
    SerializationError,
    TimeoutError,
    ValidationError,
)


def test_base_exception() -> None:
    error = SentinelError("failure")

    assert str(error) == "failure"
    assert error.details == {}


def test_exception_details() -> None:
    error = SentinelError(
        "failure",
        details={"service": "kernel"},
    )

    assert error.details == {"service": "kernel"}


def test_exception_repr() -> None:
    error = SentinelError(
        "failure",
        details={"service": "kernel"},
    )

    assert repr(error) == (
        "SentinelError("
        "message='failure', "
        "details={'service': 'kernel'})"
    )


def test_configuration_error() -> None:
    error = ConfigurationError("invalid configuration")

    assert isinstance(error, SentinelError)


def test_validation_error() -> None:
    error = ValidationError("invalid value")

    assert isinstance(error, SentinelError)


def test_serialization_errors() -> None:
    assert isinstance(
        SerializationError("serialization failed"),
        SentinelError,
    )

    assert isinstance(
        DeserializationError("deserialization failed"),
        SentinelError,
    )


def test_resource_errors() -> None:
    assert isinstance(
        NotFoundError("not found"),
        SentinelError,
    )

    assert isinstance(
        AlreadyExistsError("already exists"),
        SentinelError,
    )


def test_operation_errors() -> None:
    assert isinstance(
        PermissionDeniedError("access denied"),
        SentinelError,
    )

    assert isinstance(
        OperationError("operation failed"),
        SentinelError,
    )

    assert isinstance(
        TimeoutError("operation timed out"),
        SentinelError,
    )