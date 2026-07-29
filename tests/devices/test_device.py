import pytest

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import DeviceDisconnectedError
from sentinel.devices.metadata import DeviceMetadata


class DummyDevice(BaseDevice):

    def __init__(self):
        super().__init__(
            DeviceMetadata(
                device_id="dummy.device",
                name="Dummy Device",
                description="Testing device",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_properties():
    device = DummyDevice()

    assert device.id == "dummy.device"
    assert device.name == "Dummy Device"
    assert device.connected is False


def test_connect():
    device = DummyDevice()

    device.connect()

    assert device.connected is True


def test_disconnect():
    device = DummyDevice()

    device.connect()
    device.disconnect()

    assert device.connected is False


def test_health_check():
    device = DummyDevice()

    assert device.health_check() is False

    device.connect()

    assert device.health_check() is True


def test_execute():
    device = DummyDevice()

    device.connect()

    result = device.execute(value=123)

    assert result["value"] == 123


def test_execute_disconnected():
    device = DummyDevice()

    with pytest.raises(DeviceDisconnectedError):
        device.execute()


def test_metadata():
    device = DummyDevice()

    assert device.metadata.device_id == "dummy.device"