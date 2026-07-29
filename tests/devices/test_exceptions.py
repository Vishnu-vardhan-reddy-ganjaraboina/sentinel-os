import pytest

from sentinel.core.exceptions import SentinelError
from sentinel.devices.exceptions import (
    DeviceAlreadyExistsError,
    DeviceBusyError,
    DeviceDisconnectedError,
    DeviceError,
    DeviceNotFoundError,
    DeviceOperationError,
    InvalidDeviceError,
)


def test_device_error():
    exc = DeviceError("error")
    assert str(exc) == "error"


def test_not_found():
    exc = DeviceNotFoundError("missing")
    assert isinstance(exc, DeviceError)


def test_already_exists():
    exc = DeviceAlreadyExistsError("exists")
    assert isinstance(exc, DeviceError)


def test_disconnected():
    exc = DeviceDisconnectedError("offline")
    assert isinstance(exc, DeviceError)


def test_busy():
    exc = DeviceBusyError("busy")
    assert isinstance(exc, DeviceError)


def test_invalid():
    exc = InvalidDeviceError("invalid")
    assert isinstance(exc, DeviceError)


def test_operation():
    exc = DeviceOperationError("failed")
    assert isinstance(exc, DeviceError)


def test_catch_base_exception():
    with pytest.raises(DeviceError):
        raise DeviceBusyError("busy")


def test_catch_sentinel_exception():
    with pytest.raises(SentinelError):
        raise DeviceBusyError("busy")