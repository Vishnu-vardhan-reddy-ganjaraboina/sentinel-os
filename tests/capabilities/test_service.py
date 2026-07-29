from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.capabilities.service import CapabilityService


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


def test_register():
    service = CapabilityService()

    service.register(EchoCapability())

    assert service.exists("echo")


def test_execute():
    service = CapabilityService()

    service.register(EchoCapability())

    result = service.execute(
        "echo",
        message="hello",
    )

    assert result["message"] == "hello"


def test_unregister():
    service = CapabilityService()

    service.register(EchoCapability())

    service.unregister("echo")

    assert service.exists("echo") is False


def test_list():
    service = CapabilityService()

    service.register(EchoCapability())

    assert len(service.list()) == 1


def test_clear():
    service = CapabilityService()

    service.register(EchoCapability())

    service.clear()

    assert len(service.list()) == 0