import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityAlreadyExistsError,
    CapabilityNotFoundError,
)
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.capabilities.registry import CapabilityRegistry


class DummyCapability(BaseCapability):

    def __init__(self, capability_id: str = "dummy.echo"):
        super().__init__(
            CapabilityMetadata(
                capability_id=capability_id,
                name="Dummy",
                description="Dummy capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    assert registry.exists(capability.id)


def test_duplicate_registration():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    with pytest.raises(CapabilityAlreadyExistsError):
        registry.register(capability)


def test_get():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    assert registry.get(capability.id) is capability


def test_unregister():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    registry.unregister(capability.id)

    assert not registry.exists(capability.id)


def test_unregister_unknown():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotFoundError):
        registry.unregister("missing")


def test_list():
    registry = CapabilityRegistry()

    registry.register(DummyCapability("a"))
    registry.register(DummyCapability("b"))

    assert len(registry.list()) == 2


def test_category_filter():
    registry = CapabilityRegistry()

    registry.register(DummyCapability())

    result = registry.list_by_category(
        CapabilityCategory.CUSTOM
    )

    assert len(result) == 1


def test_clear():
    registry = CapabilityRegistry()

    registry.register(DummyCapability())

    registry.clear()

    assert len(registry) == 0