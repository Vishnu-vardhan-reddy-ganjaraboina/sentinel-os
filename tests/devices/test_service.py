from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.metadata import DeviceMetadata
from sentinel.devices.service import DeviceService


class EchoDevice(BaseDevice):

    def __init__(self):
        super().__init__(
            DeviceMetadata(
                device_id="echo",
                name="Echo Device",
                description="Echo testing device",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    service = DeviceService()

    service.register(EchoDevice())

    assert service.exists("echo")


def test_connect_execute():
    service = DeviceService()

    service.register(EchoDevice())

    service.connect("echo")

    result = service.execute(
        "echo",
        message="hello",
    )

    assert result["message"] == "hello"


def test_disconnect():
    service = DeviceService()

    service.register(EchoDevice())

    service.connect("echo")
    service.disconnect("echo")

    assert service.registry.get("echo").connected is False


def test_unregister():
    service = DeviceService()

    service.register(EchoDevice())

    service.unregister("echo")

    assert service.exists("echo") is False


def test_list():
    service = DeviceService()

    service.register(EchoDevice())

    assert len(service.list()) == 1


def test_clear():
    service = DeviceService()

    service.register(EchoDevice())

    service.clear()

    assert len(service.list()) == 0