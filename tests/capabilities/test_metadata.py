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