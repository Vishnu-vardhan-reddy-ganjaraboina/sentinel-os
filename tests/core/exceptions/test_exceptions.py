from sentinel.core.exceptions import (
    ConfigurationError,
    SentinelError,
)


def test_base_exception() -> None:
    error = SentinelError("failure")

    assert str(error) == "failure"
    assert error.details == {}


def test_details() -> None:
    error = SentinelError(
        "failure",
        details={"service": "kernel"},
    )

    assert error.details["service"] == "kernel"


def test_inheritance() -> None:
    error = ConfigurationError("invalid")

    assert isinstance(error, SentinelError)