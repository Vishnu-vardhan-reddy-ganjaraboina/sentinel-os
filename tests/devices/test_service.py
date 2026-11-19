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

    assert service.get("echo").connected is False


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
def test_injected_empty_manager_is_preserved() -> None:
    from sentinel.devices.manager import DeviceManager

    manager = DeviceManager()
    service = DeviceService(manager)

    device = EchoDevice()
    service.register(device)

    assert manager.get("echo") is device


def test_service_does_not_expose_internal_accessors() -> None:
    service = DeviceService()

    assert not hasattr(service, "manager")
    assert not hasattr(service, "registry")
