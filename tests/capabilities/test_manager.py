import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityExecutionError,
)
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata


class EchoCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="echo",
                name="Echo",
                description="Echo capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


class FailingCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="fail",
                name="Fail",
                description="Always fails",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        raise RuntimeError("boom")


def test_register():
    manager = CapabilityManager()

    capability = EchoCapability()

    manager.register(capability)

    assert manager.exists("echo")


def test_execute():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    result = manager.execute(
        "echo",
        value=100,
    )

    assert result["value"] == 100


def test_execute_failure():
    manager = CapabilityManager()

    manager.register(FailingCapability())

    with pytest.raises(CapabilityExecutionError):
        manager.execute("fail")


def test_unregister():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    manager.unregister("echo")

    assert not manager.exists("echo")


def test_clear():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    manager.clear()

    assert len(manager.list()) == 0