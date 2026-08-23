import pytest

from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.metadata import CapabilityMetadata


def create_metadata() -> CapabilityMetadata:
    return CapabilityMetadata(
        capability_id="file.read",
        name="Read File",
        description="Reads a file",
        category=CapabilityCategory.FILESYSTEM,
    )


def test_create_metadata():
    metadata = create_metadata()

    assert metadata.capability_id == "file.read"
    assert metadata.name == "Read File"
    assert metadata.enabled is True


def test_to_dict():
    metadata = create_metadata()

    data = metadata.to_dict()

    assert data["capability_id"] == "file.read"
    assert data["category"] == "filesystem"


def test_from_dict():
    metadata = create_metadata()

    restored = CapabilityMetadata.from_dict(
        metadata.to_dict()
    )

    assert restored.capability_id == metadata.capability_id
    assert restored.category == metadata.category


def test_empty_id():
    with pytest.raises(ValueError):
        CapabilityMetadata(
            capability_id="",
            name="x",
            description="x",
            category=CapabilityCategory.CUSTOM,
        )


def test_empty_name():
    with pytest.raises(ValueError):
        CapabilityMetadata(
            capability_id="x",
            name="",
            description="x",
            category=CapabilityCategory.CUSTOM,
        )


def test_empty_description():
    with pytest.raises(ValueError):
        CapabilityMetadata(
            capability_id="x",
            name="x",
            description="",
            category=CapabilityCategory.CUSTOM,
        )

def test_metadata_rejects_non_string_version() -> None:
    with pytest.raises(TypeError):
        CapabilityMetadata(
            capability_id="x",
            name="X",
            description="X",
            category=CapabilityCategory.CUSTOM,
            version=123,  # type: ignore[arg-type]
        )


def test_metadata_rejects_empty_version() -> None:
    with pytest.raises(ValueError):
        CapabilityMetadata(
            capability_id="x",
            name="X",
            description="X",
            category=CapabilityCategory.CUSTOM,
            version="",
        )


def test_metadata_rejects_invalid_category() -> None:
    with pytest.raises((TypeError, ValueError)):
        CapabilityMetadata(
            capability_id="x",
            name="X",
            description="X",
            category="invalid",  # type: ignore[arg-type]
        )


def test_to_dict_returns_isolated_metadata() -> None:
    metadata = create_metadata()

    data = metadata.to_dict()

    data["tags"].append("changed")
    data["permissions"].append("changed")

    assert "changed" not in metadata.tags
    assert "changed" not in metadata.permissions


def test_metadata_round_trip_preserves_fields() -> None:
    metadata = CapabilityMetadata(
        capability_id="file.read",
        name="Read File",
        description="Reads a file",
        category=CapabilityCategory.FILESYSTEM,
        version="2.1.0",
        author="Sentinel",
        tags=["file", "read"],
        permissions=["filesystem.read"],
        input_schema={"type": "object"},
        output_schema={"type": "string"},
    )

    restored = CapabilityMetadata.from_dict(
        metadata.to_dict()
    )

    assert restored.version == "2.1.0"
    assert restored.author == "Sentinel"
    assert restored.tags == ["file", "read"]
    assert restored.permissions == ["filesystem.read"]
    assert restored.input_schema == {"type": "object"}
    assert restored.output_schema == {"type": "string"}