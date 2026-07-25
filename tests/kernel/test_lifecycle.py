import pytest

from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.lifecycle import LifecycleManager
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


class Dummy(Service):

    def __init__(self):
        super().__init__("dummy")

    def initialize(self):
        pass

    def shutdown(self):
        pass


def test_start():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    manager.start(service)

    assert manager.state(service) is ServiceState.RUNNING


def test_stop():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    manager.start(service)
    manager.stop(service)

    assert manager.state(service) is ServiceState.STOPPED