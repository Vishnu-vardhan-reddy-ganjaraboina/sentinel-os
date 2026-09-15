from __future__ import annotations

from threading import Barrier, Thread

import pytest

from sentinel.application import Application
from sentinel.boot import (
    BootManager,
    BootProfile,
    BootShutdownError,
    BootStartupError,
    BootStateError,
)
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.platform import Platform
from sentinel.system import System


class BootTestService(Service):
    def __init__(
        self,
        name: str = "boot-test",
        *,
        fail_initialize: bool = False,
        fail_shutdown: bool = False,
    ) -> None:
        super().__init__(name)
        self.fail_initialize = fail_initialize
        self.fail_shutdown = fail_shutdown
        self.initialized = False
        self.shutdown_called = False

    def initialize(self) -> None:
        if self.fail_initialize:
            raise RuntimeError("initialize failed")
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True
        if self.fail_shutdown:
            raise RuntimeError("shutdown failed")
        self.initialized = False


def make_system(
    *,
    fail_initialize: bool = False,
    fail_shutdown: bool = False,
) -> tuple[System, BootTestService]:
    kernel = Kernel()
    service = BootTestService(
        fail_initialize=fail_initialize,
        fail_shutdown=fail_shutdown,
    )
    kernel.register(service)
    return System(kernel=kernel, platform=Platform()), service


def test_constructor_defaults() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    assert manager.system is system
    assert manager.profile.name == "default"
    assert manager.state == "stopped"
    assert manager.running is False
    assert manager.last_result is None


def test_custom_profile() -> None:
    system, _ = make_system()
    profile = BootProfile(
        name="development",
        metadata={"debug": True},
    )
    manager = BootManager(system, profile)

    assert manager.profile is profile
    assert manager.profile.name == "development"


@pytest.mark.parametrize(
    "system",
    [None, object(), "invalid"],
)
def test_invalid_system(system: object) -> None:
    with pytest.raises(TypeError):
        BootManager(system)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "profile",
    [object(), "invalid", 123],
)
def test_invalid_profile(profile: object) -> None:
    system, _ = make_system()

    with pytest.raises(TypeError):
        BootManager(system, profile)  # type: ignore[arg-type]


def test_start_returns_success() -> None:
    system, service = make_system()
    manager = BootManager(system)

    result = manager.start()

    assert result.success is True
    assert result.profile == "default"
    assert manager.state == "running"
    assert manager.running is True
    assert system.running is True
    assert service.initialized is True
    assert manager.last_result is result


def test_start_is_idempotence_protected() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    manager.start()

    with pytest.raises(BootStateError):
        manager.start()


def test_start_failure_returns_error_contract() -> None:
    system, _ = make_system(fail_initialize=True)
    manager = BootManager(system)

    with pytest.raises(BootStartupError) as exc_info:
        manager.start()

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert manager.state == "stopped"
    assert manager.running is False
    assert system.running is False
    assert manager.last_result is not None
    assert manager.last_result.success is False
    assert manager.last_result.profile == "default"
    assert manager.last_result.details["error"] == "initialize failed"


def test_stop_returns_success() -> None:
    system, service = make_system()
    manager = BootManager(system)

    manager.start()
    result = manager.stop()

    assert result.success is True
    assert manager.state == "stopped"
    assert manager.running is False
    assert system.running is False
    assert service.shutdown_called is True
    assert service.initialized is False
    assert manager.last_result is result


def test_stop_requires_running_state() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    with pytest.raises(BootStateError):
        manager.stop()


def test_shutdown_failure_transitions_to_failed() -> None:
    system, _ = make_system(fail_shutdown=True)
    manager = BootManager(system)

    manager.start()

    with pytest.raises(BootShutdownError) as exc_info:
        manager.stop()

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert manager.state == "failed"
    assert manager.running is False
    assert manager.last_result is not None
    assert manager.last_result.success is False
    assert manager.last_result.details["error"] == "shutdown failed"


def test_health_before_start() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    health = manager.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False
    assert health["last_result"] is None


def test_health_while_running() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    manager.start()

    health = manager.health()

    assert health["state"] == "running"
    assert health["running"] is True
    assert health["healthy"] is True
    assert health["system"]["healthy"] is True


def test_health_after_shutdown() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    manager.start()
    manager.stop()

    health = manager.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False


def test_result_is_isolated() -> None:
    system, _ = make_system()
    manager = BootManager(
        system,
        BootProfile(
            metadata={"nested": {"value": 1}},
        ),
    )

    result = manager.start()
    result_dict = result.to_dict()

    result_dict["details"]["state"] = "changed"

    assert result.details["state"] == "running"


def test_repr() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    representation = repr(manager)

    assert "BootManager" in representation
    assert "default" in representation
    assert "stopped" in representation


def test_concurrent_start_allows_only_one_transition() -> None:
    system, _ = make_system()
    manager = BootManager(system)

    barrier = Barrier(2)
    outcomes: list[str] = []

    def start() -> None:
        barrier.wait()

        try:
            manager.start()
            outcomes.append("started")
        except BootStateError:
            outcomes.append("rejected")

    threads = [
        Thread(target=start),
        Thread(target=start),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["rejected", "started"]
    assert manager.running is True

    manager.stop()


def test_concurrent_stop_allows_only_one_transition() -> None:
    system, _ = make_system()
    manager = BootManager(system)
    manager.start()

    barrier = Barrier(2)
    outcomes: list[str] = []

    def stop() -> None:
        barrier.wait()

        try:
            manager.stop()
            outcomes.append("stopped")
        except BootStateError:
            outcomes.append("rejected")

    threads = [
        Thread(target=stop),
        Thread(target=stop),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["rejected", "stopped"]
    assert manager.running is False
