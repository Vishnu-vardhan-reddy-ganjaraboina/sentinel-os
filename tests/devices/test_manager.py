import pytest

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import DeviceOperationError
from sentinel.devices.manager import DeviceManager
from sentinel.devices.metadata import DeviceMetadata


class EchoDevice(BaseDevice):

    def __init__(self):
        super().__init__(
            DeviceMetadata(
                device_id="echo",
                name="Echo Device",
                description="Echo testing device",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


class FailingDevice(BaseDevice):

    def __init__(self):
        super().__init__(
            DeviceMetadata(
                device_id="fail",
                name="Fail Device",
                description="Always fails",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        raise RuntimeError("boom")


def test_register():
    manager = DeviceManager()

    manager.register(EchoDevice())

    assert manager.exists("echo")


def test_connect():
    manager = DeviceManager()

    manager.register(EchoDevice())

    manager.connect("echo")

    assert manager.registry.get("echo").connected is True


def test_execute():
    manager = DeviceManager()

    manager.register(EchoDevice())
    manager.connect("echo")

    result = manager.execute(
        "echo",
        value=100,
    )

    assert result["value"] == 100


def test_execute_failure():
    manager = DeviceManager()

    manager.register(FailingDevice())
    manager.connect("fail")

    with pytest.raises(DeviceOperationError):
        manager.execute("fail")


def test_disconnect():
    manager = DeviceManager()

    manager.register(EchoDevice())

    manager.connect("echo")
    manager.disconnect("echo")

    assert manager.registry.get("echo").connected is False


def test_unregister():
    manager = DeviceManager()

    manager.register(EchoDevice())

    manager.unregister("echo")

    assert not manager.exists("echo")


def test_clear():
    manager = DeviceManager()

    manager.register(EchoDevice())

    manager.clear()

    assert len(manager.list()) == 0