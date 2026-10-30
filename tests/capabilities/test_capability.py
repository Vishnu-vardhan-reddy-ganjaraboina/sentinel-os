from threading import Event, Thread

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

def test_disabled_error_is_not_transformed() -> None:
    capability = DummyCapability()

    capability.disable()

    with pytest.raises(CapabilityDisabledError):
        capability.execute()

def test_disable_rejects_new_execution_but_allows_admitted_run() -> None:
    entered_run = Event()
    release_run = Event()

    class BlockingCapability(DummyCapability):
        def run(self, **kwargs):
            entered_run.set()
            if not release_run.wait(timeout=5):
                raise TimeoutError("Test did not release the running capability.")
            return kwargs

    capability = BlockingCapability()
    result_holder = {}
    error_holder = {}

    def execute_in_thread() -> None:
        try:
            result_holder["result"] = capability.execute(value=10)
        except Exception as exc:
            error_holder["error"] = exc

    worker = Thread(target=execute_in_thread)
    worker.start()

    try:
        assert entered_run.wait(timeout=5), "Execution did not enter run()."

        capability.disable()

        with pytest.raises(CapabilityDisabledError):
            capability.execute(value=20)

        release_run.set()
        worker.join(timeout=5)

        assert not worker.is_alive(), "Worker thread did not finish."
        assert "error" not in error_holder
        assert result_holder["result"] == {"value": 10}
        assert capability.enabled is False
    finally:
        release_run.set()
        worker.join(timeout=5)

def test_metadata_property_returns_isolated_snapshot() -> None:
    capability = DummyCapability()

    metadata = capability.metadata
    metadata.name = "Modified"
    metadata.enabled = False
    metadata.permissions.append("admin")
    metadata.input_schema["type"] = "string"

    assert capability.name == "Dummy"
    assert capability.enabled is True
    assert "admin" not in capability.metadata.permissions
    assert capability.metadata.input_schema == {}


def test_constructor_copies_supplied_metadata() -> None:
    metadata = CapabilityMetadata(
        capability_id="dummy.echo",
        name="Dummy",
        description="Echo capability",
        category=CapabilityCategory.CUSTOM,
    )

    capability = DummyCapability.__new__(DummyCapability)
    BaseCapability.__init__(capability, metadata)

    metadata.name = "Modified"
    metadata.enabled = False

    assert capability.name == "Dummy"
    assert capability.enabled is True
