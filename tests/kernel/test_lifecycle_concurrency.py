import threading

import pytest

from sentinel.kernel.event_bus import EventBus
from sentinel.kernel.exceptions import (
    ServiceAlreadyRunningError,
    ServiceNotRunningError,
)
from sentinel.kernel.lifecycle import LifecycleManager
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


class BlockingInitializeService(Service):
    def __init__(self):
        super().__init__("blocking-start")
        self.initialize_started = threading.Event()
        self.allow_initialize = threading.Event()

    def initialize(self):
        self.initialize_started.set()
        self.allow_initialize.wait(timeout=5)

    def shutdown(self):
        pass


class BlockingShutdownService(Service):
    def __init__(self):
        super().__init__("blocking-stop")
        self.shutdown_started = threading.Event()
        self.allow_shutdown = threading.Event()

    def initialize(self):
        pass

    def shutdown(self):
        self.shutdown_started.set()
        self.allow_shutdown.wait(timeout=5)


def test_concurrent_stop_during_start_is_rejected():
    manager = LifecycleManager(EventBus())
    service = BlockingInitializeService()

    errors: list[Exception] = []

    def start_service():
        try:
            manager.start(service)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=start_service)
    thread.start()

    assert service.initialize_started.wait(timeout=2)
    assert manager.state(service) is ServiceState.STARTING

    with pytest.raises(
        ServiceNotRunningError,
        match="not running",
    ):
        manager.stop(service)

    service.allow_initialize.set()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert manager.state(service) is ServiceState.RUNNING
    assert errors == []


def test_concurrent_start_during_stop_is_rejected():
    manager = LifecycleManager(EventBus())
    service = BlockingShutdownService()

    manager.start(service)

    errors: list[Exception] = []

    def stop_service():
        try:
            manager.stop(service)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=stop_service)
    thread.start()

    assert service.shutdown_started.wait(timeout=2)
    assert manager.state(service) is ServiceState.STOPPING

    with pytest.raises(
        ServiceAlreadyRunningError,
        match="already stopping",
    ):
        manager.start(service)

    service.allow_shutdown.set()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert manager.state(service) is ServiceState.STOPPED
    assert errors == []
