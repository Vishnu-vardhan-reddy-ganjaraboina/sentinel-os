import pytest

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)
from sentinel.devices.metadata import DeviceMetadata
from sentinel.devices.registry import DeviceRegistry


class DummyDevice(BaseDevice):

    def __init__(self, device_id: str = "dummy.device"):
        super().__init__(
            DeviceMetadata(
                device_id=device_id,
                name="Dummy Device",
                description="Testing device",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    registry = DeviceRegistry()

    device = DummyDevice()

    registry.register(device)

    assert registry.exists(device.id)


def test_duplicate_registration():
    registry = DeviceRegistry()

    device = DummyDevice()

    registry.register(device)

    with pytest.raises(DeviceAlreadyExistsError):
        registry.register(device)


def test_get():
    registry = DeviceRegistry()

    device = DummyDevice()

    registry.register(device)

    assert registry.get(device.id) is device


def test_unregister():
    registry = DeviceRegistry()

    device = DummyDevice()

    registry.register(device)

    registry.unregister(device.id)

    assert not registry.exists(device.id)


def test_unregister_unknown():
    registry = DeviceRegistry()

    with pytest.raises(DeviceNotFoundError):
        registry.unregister("missing")


def test_list():
    registry = DeviceRegistry()

    registry.register(DummyDevice("device1"))
    registry.register(DummyDevice("device2"))

    assert len(registry.list()) == 2


def test_category_filter():
    registry = DeviceRegistry()

    registry.register(DummyDevice())

    devices = registry.list_by_category(
        DeviceCategory.CUSTOM
    )

    assert len(devices) == 1


def test_clear():
    registry = DeviceRegistry()

    registry.register(DummyDevice())

    registry.clear()

    assert len(registry) == 0