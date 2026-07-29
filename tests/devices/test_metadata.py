import pytest

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.metadata import DeviceMetadata


def create_metadata() -> DeviceMetadata:
    return DeviceMetadata(
        device_id="filesystem.local",
        name="Local Filesystem",
        description="Local storage device",
        category=DeviceCategory.FILESYSTEM,
    )


def test_create_metadata():
    metadata = create_metadata()

    assert metadata.device_id == "filesystem.local"
    assert metadata.name == "Local Filesystem"
    assert metadata.connected is False


def test_to_dict():
    metadata = create_metadata()

    data = metadata.to_dict()

    assert data["device_id"] == "filesystem.local"
    assert data["category"] == "filesystem"


def test_from_dict():
    metadata = create_metadata()

    restored = DeviceMetadata.from_dict(
        metadata.to_dict()
    )

    assert restored.device_id == metadata.device_id
    assert restored.category == metadata.category


def test_empty_id():
    with pytest.raises(ValueError):
        DeviceMetadata(
            device_id="",
            name="x",
            description="x",
            category=DeviceCategory.CUSTOM,
        )


def test_empty_name():
    with pytest.raises(ValueError):
        DeviceMetadata(
            device_id="x",
            name="",
            description="x",
            category=DeviceCategory.CUSTOM,
        )


def test_empty_description():
    with pytest.raises(ValueError):
        DeviceMetadata(
            device_id="x",
            name="x",
            description="",
            category=DeviceCategory.CUSTOM,
        )