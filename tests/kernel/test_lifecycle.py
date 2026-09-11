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


class Dummy(Service):

    def __init__(self):
        super().__init__("dummy")
        self.initialized = False
        self.stopped = False

    def initialize(self):
        self.initialized = True

    def shutdown(self):
        self.stopped = True


class FailingInitialize(Service):

    def __init__(self):
        super().__init__("failing")

    def initialize(self):
        raise RuntimeError("initialize failed")

    def shutdown(self):
        pass


class FailingShutdown(Service):

    def __init__(self):
        super().__init__("failing")

    def initialize(self):
        pass

    def shutdown(self):
        raise RuntimeError("shutdown failed")


def test_start():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    manager.start(service)

    assert service.initialized
    assert manager.state(service) is ServiceState.RUNNING


def test_stop():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    manager.start(service)
    manager.stop(service)

    assert service.stopped
    assert manager.state(service) is ServiceState.STOPPED


def test_start_twice_raises():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    manager.start(service)

    with pytest.raises(
        ServiceAlreadyRunningError,
        match="already running",
    ):
        manager.start(service)


def test_stop_before_start_raises():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    with pytest.raises(
        ServiceNotRunningError,
        match="not running",
    ):
        manager.stop(service)


def test_initialize_failure_sets_failed_state():
    manager = LifecycleManager(EventBus())
    service = FailingInitialize()

    with pytest.raises(
        RuntimeError,
        match="initialize failed",
    ):
        manager.start(service)

    assert manager.state(service) is ServiceState.FAILED


def test_shutdown_failure_sets_failed_state():
    manager = LifecycleManager(EventBus())
    service = FailingShutdown()

    manager.start(service)

    with pytest.raises(
        RuntimeError,
        match="shutdown failed",
    ):
        manager.stop(service)

    assert manager.state(service) is ServiceState.FAILED


def test_is_running():
    manager = LifecycleManager(EventBus())
    service = Dummy()

    assert not manager.is_running(service)

    manager.start(service)

    assert manager.is_running(service)

    manager.stop(service)

    assert not manager.is_running(service)


def test_invalid_service_rejected():
    manager = LifecycleManager(EventBus())

    with pytest.raises(TypeError):
        manager.start(object())  # type: ignore[arg-type]


def test_invalid_event_bus_rejected():
    with pytest.raises(TypeError):
        LifecycleManager(object())  # type: ignore[arg-type]


def test_concurrent_start_only_starts_once():
    manager = LifecycleManager(EventBus())

    class SlowService(Service):
        def __init__(self):
            super().__init__("slow")
            self.initialize_count = 0
            self._count_lock = threading.Lock()

        def initialize(self):
            with self._count_lock:
                self.initialize_count += 1

        def shutdown(self):
            pass

    service = SlowService()
    errors: list[Exception] = []

    def start_service():
        try:
            manager.start(service)
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=start_service)
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert manager.state(service) is ServiceState.RUNNING
    assert service.initialize_count == 1
    assert len(errors) == 9
    assert all(
        isinstance(error, ServiceAlreadyRunningError)
        for error in errors
    )