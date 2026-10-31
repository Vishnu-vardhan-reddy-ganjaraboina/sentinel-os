import pytest

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import DeviceDisconnectedError
from sentinel.devices.metadata import DeviceMetadata


class DummyDevice(BaseDevice):

    def __init__(self):
        super().__init__(
            DeviceMetadata(
                device_id="dummy.device",
                name="Dummy Device",
                description="Testing device",
                category=DeviceCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_properties():
    device = DummyDevice()

    assert device.id == "dummy.device"
    assert device.name == "Dummy Device"
    assert device.connected is False


def test_connect():
    device = DummyDevice()

    device.connect()

    assert device.connected is True


def test_disconnect():
    device = DummyDevice()

    device.connect()
    device.disconnect()

    assert device.connected is False


def test_health_check():
    device = DummyDevice()

    assert device.health_check() is False

    device.connect()

    assert device.health_check() is True


def test_execute():
    device = DummyDevice()

    device.connect()

    result = device.execute(value=123)

    assert result["value"] == 123


def test_execute_disconnected():
    device = DummyDevice()

    with pytest.raises(DeviceDisconnectedError):
        device.execute()


def test_metadata():
    device = DummyDevice()

    assert device.metadata.device_id == "dummy.device"

def test_repeated_connect_is_idempotent() -> None:
    device = DummyDevice()

    device.connect()
    device.connect()

    assert device.connected is True


def test_repeated_disconnect_is_idempotent() -> None:
    device = DummyDevice()

    device.disconnect()
    device.disconnect()

    assert device.connected is False
def test_constructor_copies_input_metadata() -> None:
    metadata = DeviceMetadata(
        device_id="isolated.device",
        name="Original Name",
        description="Original description",
        category=DeviceCategory.CUSTOM,
        capabilities=["read"],
        properties={"settings": {"enabled": True}},
    )

    class MetadataDevice(BaseDevice):
        def run(self, **kwargs):
            return kwargs

    device = MetadataDevice(metadata)
    metadata.name = "Changed Name"
    metadata.capabilities.append("write")
    metadata.properties["settings"]["enabled"] = False

    assert device.name == "Original Name"
    assert device.metadata.capabilities == ["read"]
    assert device.metadata.properties == {
        "settings": {"enabled": True}
    }


def test_metadata_property_returns_isolated_snapshot() -> None:
    device = DummyDevice()

    snapshot = device.metadata
    snapshot.name = "Modified Name"
    snapshot.capabilities.append("write")
    snapshot.properties["nested"] = {"changed": True}
    snapshot.connected = True

    assert device.name == "Dummy Device"
    assert device.metadata.capabilities == []
    assert device.metadata.properties == {}
    assert device.connected is False


def test_metadata_snapshot_reflects_live_connection_state() -> None:
    device = DummyDevice()

    assert device.metadata.connected is False

    device.connect()
    assert device.metadata.connected is True

    device.disconnect()
    assert device.metadata.connected is False


def test_disconnect_waits_for_active_execution() -> None:
    from threading import Event, Thread

    execution_started = Event()
    allow_execution_to_finish = Event()
    disconnect_finished = Event()

    class BlockingDevice(DummyDevice):
        def run(self, **kwargs):
            execution_started.set()
            assert allow_execution_to_finish.wait(timeout=2)
            return kwargs

    device = BlockingDevice()
    device.connect()

    execution_thread = Thread(target=device.execute)
    execution_thread.start()

    assert execution_started.wait(timeout=1)

    def disconnect_device() -> None:
        device.disconnect()
        disconnect_finished.set()

    disconnect_thread = Thread(target=disconnect_device)
    disconnect_thread.start()

    assert not disconnect_finished.wait(timeout=0.1)

    allow_execution_to_finish.set()

    execution_thread.join(timeout=2)
    disconnect_thread.join(timeout=2)

    assert not execution_thread.is_alive()
    assert not disconnect_thread.is_alive()
    assert disconnect_finished.is_set()
    assert device.connected is False
