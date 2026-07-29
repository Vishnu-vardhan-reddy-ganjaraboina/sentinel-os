import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityDisabledError,
)
from sentinel.capabilities.metadata import CapabilityMetadata


class DummyCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="dummy.echo",
                name="Dummy",
                description="Echo capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_properties():
    capability = DummyCapability()

    assert capability.id == "dummy.echo"
    assert capability.name == "Dummy"
    assert capability.enabled


def test_execute():
    capability = DummyCapability()

    result = capability.execute(value=10)

    assert result["value"] == 10


def test_disable():
    capability = DummyCapability()

    capability.disable()

    assert capability.enabled is False

    with pytest.raises(CapabilityDisabledError):
        capability.execute()


def test_enable():
    capability = DummyCapability()

    capability.disable()
    capability.enable()

    assert capability.enabled is True


def test_metadata():
    capability = DummyCapability()

    assert capability.metadata.capability_id == "dummy.echo"