from sentinel.devices.constants import (
    DEFAULT_DEVICE_VERSION,
    DeviceCategory,
    DeviceStatus,
)


def test_default_version():
    assert DEFAULT_DEVICE_VERSION == "1.0.0"


def test_categories():
    assert DeviceCategory.FILESYSTEM.value == "filesystem"
    assert DeviceCategory.NETWORK.value == "network"
    assert DeviceCategory.CUSTOM.value == "custom"


def test_status():
    assert DeviceStatus.ONLINE.value == "online"
    assert DeviceStatus.OFFLINE.value == "offline"
    assert DeviceStatus.BUSY.value == "busy"
    assert DeviceStatus.DISCONNECTED.value == "disconnected"