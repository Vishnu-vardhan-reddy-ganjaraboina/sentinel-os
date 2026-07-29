import pytest

from sentinel.devices.interfaces import Device


class DummyDevice(Device):

    def __init__(self):
        self._connected = False

    @property
    def id(self):
        return "dummy"

    @property
    def name(self):
        return "Dummy Device"

    @property
    def description(self):
        return "Testing device"

    @property
    def version(self):
        return "1.0.0"

    @property
    def connected(self):
        return self._connected

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    def health_check(self):
        return True

    def execute(self, **kwargs):
        return kwargs


def test_device_properties():
    device = DummyDevice()

    assert device.id == "dummy"
    assert device.name == "Dummy Device"
    assert device.connected is False


def test_connect_disconnect():
    device = DummyDevice()

    device.connect()
    assert device.connected is True

    device.disconnect()
    assert device.connected is False


def test_health_check():
    device = DummyDevice()

    assert device.health_check() is True


def test_execute():
    device = DummyDevice()

    result = device.execute(value=42)

    assert result["value"] == 42


def test_interface_is_abstract():
    with pytest.raises(TypeError):
        Device()