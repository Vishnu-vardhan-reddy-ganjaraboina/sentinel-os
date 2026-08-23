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

def test_metadata_rejects_non_string_version() -> None:
    with pytest.raises(TypeError):
        DeviceMetadata(
            device_id="x",
            name="X",
            description="X",
            category=DeviceCategory.CUSTOM,
            version=123,  # type: ignore[arg-type]
        )


def test_metadata_rejects_empty_version() -> None:
    with pytest.raises(ValueError):
        DeviceMetadata(
            device_id="x",
            name="X",
            description="X",
            category=DeviceCategory.CUSTOM,
            version="",
        )


def test_metadata_rejects_invalid_category() -> None:
    with pytest.raises((TypeError, ValueError)):
        DeviceMetadata(
            device_id="x",
            name="X",
            description="X",
            category="invalid",  # type: ignore[arg-type]
        )


def test_to_dict_returns_isolated_metadata() -> None:
    metadata = create_metadata()

    data = metadata.to_dict()

    data["capabilities"].append("changed")
    data["properties"]["changed"] = True

    assert "changed" not in metadata.capabilities
    assert "changed" not in metadata.properties


def test_metadata_round_trip_preserves_fields() -> None:
    metadata = DeviceMetadata(
        device_id="filesystem.local",
        name="Local Filesystem",
        description="Local storage device",
        category=DeviceCategory.FILESYSTEM,
        version="2.1.0",
        manufacturer="Sentinel",
        model="LocalFS",
        serial_number="SN-001",
        capabilities=["read", "write"],
        properties={
            "root": "/tmp",
            "readonly": False,
        },
    )

    restored = DeviceMetadata.from_dict(
        metadata.to_dict()
    )

    assert restored.version == "2.1.0"
    assert restored.manufacturer == "Sentinel"
    assert restored.model == "LocalFS"
    assert restored.serial_number == "SN-001"
    assert restored.capabilities == ["read", "write"]
    assert restored.properties == {
        "root": "/tmp",
        "readonly": False,
    }