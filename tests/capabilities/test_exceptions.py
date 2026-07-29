import pytest

from sentinel.core.exceptions import SentinelError
from sentinel.capabilities.exceptions import (
    CapabilityAlreadyExistsError,
    CapabilityDisabledError,
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    InvalidCapabilityError,
)


def test_capability_error():
    exc = CapabilityError("error")

    assert isinstance(exc, SentinelError)
    assert str(exc) == "error"


def test_not_found():
    exc = CapabilityNotFoundError("missing")

    assert isinstance(exc, CapabilityError)
    assert str(exc) == "missing"


def test_already_exists():
    exc = CapabilityAlreadyExistsError("exists")

    assert isinstance(exc, CapabilityError)
    assert str(exc) == "exists"


def test_disabled():
    exc = CapabilityDisabledError("disabled")

    assert isinstance(exc, CapabilityError)
    assert str(exc) == "disabled"


def test_invalid():
    exc = InvalidCapabilityError("invalid")

    assert isinstance(exc, CapabilityError)
    assert str(exc) == "invalid"


def test_execution():
    exc = CapabilityExecutionError("failed")

    assert isinstance(exc, CapabilityError)
    assert str(exc) == "failed"


def test_catch_base_exception():
    with pytest.raises(CapabilityError):
        raise CapabilityExecutionError("boom")