from __future__ import annotations

from threading import Barrier, Thread

import pytest

from pathlib import Path

from sentinel.control import ControlEndpointRegistry

from sentinel.boot import (
    BootManager,
    BootShutdownError,
    BootStartupError,
    BootStateError,
)
from sentinel.process import (
    ProcessHost,
    ProcessShutdownError,
    ProcessStartupError,
    ProcessState,
    ProcessStateError,
)
from sentinel.system import System
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service




class ProcessTestService(Service):
    def __init__(
        self,
        *,
        fail_initialize: bool = False,
        fail_shutdown: bool = False,
    ) -> None:
        super().__init__("process-test")
        self.fail_initialize = fail_initialize
        self.fail_shutdown = fail_shutdown

    def initialize(self) -> None:
        if self.fail_initialize:
            raise RuntimeError("process startup failed")

    def shutdown(self) -> None:
        if self.fail_shutdown:
            raise RuntimeError("process shutdown failed")


def make_boot_manager(
    *,
    fail_initialize: bool = False,
    fail_shutdown: bool = False,
) -> BootManager:
    kernel = Kernel()
    kernel.register(
        ProcessTestService(
            fail_initialize=fail_initialize,
            fail_shutdown=fail_shutdown,
        )
    )

    system = System(kernel)
    return BootManager(system)


def test_constructor() -> None:
    manager = make_boot_manager()
    host = ProcessHost(manager)

    assert host.boot_manager is manager
    assert host.state == ProcessState.STOPPED
    assert host.running is False
    assert host.last_result is None


def test_invalid_boot_manager() -> None:
    with pytest.raises(TypeError):
        ProcessHost(object())  # type: ignore[arg-type]


def test_start() -> None:
    host = ProcessHost(make_boot_manager())

    result = host.start()

    assert result.success is True
    assert host.state == ProcessState.RUNNING
    assert host.running is True
    assert host.last_result is result

    host.stop()


def test_double_start_rejected() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()

    with pytest.raises(
        ProcessStateError,
        match="already running",
    ):
        host.start()

    host.stop()


def test_stop() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()
    result = host.stop()

    assert result.success is True
    assert host.state == ProcessState.STOPPED
    assert host.running is False
    assert host.last_result is result


def test_stop_requires_running() -> None:
    host = ProcessHost(make_boot_manager())

    with pytest.raises(
        ProcessStateError,
        match="not running",
    ):
        host.stop()


def test_startup_failure() -> None:
    host = ProcessHost(
        make_boot_manager(
            fail_initialize=True,
        )
    )

    with pytest.raises(ProcessStartupError) as exc_info:
        host.start()

    assert isinstance(exc_info.value.__cause__, BootStartupError)
    assert host.state == ProcessState.STOPPED
    assert host.running is False
    assert host.last_result is None


def test_shutdown_failure() -> None:
    host = ProcessHost(
        make_boot_manager(
            fail_shutdown=True,
        )
    )

    host.start()

    with pytest.raises(ProcessShutdownError) as exc_info:
        host.stop()

    assert isinstance(
        exc_info.value.__cause__,
        BootShutdownError,
    )
    assert host.state == ProcessState.FAILED
    assert host.running is False


def test_request_stop() -> None:
    host = ProcessHost(make_boot_manager())

    assert host.wait(0) is False

    host.request_stop()

    assert host.wait(0) is True


def test_wait_timeout() -> None:
    host = ProcessHost(make_boot_manager())

    assert host.wait(0) is False
    assert host.wait(0.01) is False


@pytest.mark.parametrize(
    "timeout",
    [-1, "invalid", object()],
)
def test_wait_rejects_invalid_timeout(timeout: object) -> None:
    host = ProcessHost(make_boot_manager())

    with pytest.raises((TypeError, ValueError)):
        host.wait(timeout)  # type: ignore[arg-type]


def test_health_before_start() -> None:
    host = ProcessHost(make_boot_manager())

    health = host.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False
    assert health["last_result"] is None


def test_health_while_running() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()

    health = host.health()

    assert health["state"] == "running"
    assert health["running"] is True
    assert health["healthy"] is True
    assert health["boot"]["healthy"] is True

    host.stop()


def test_health_after_stop() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()
    host.stop()

    health = host.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False


def test_context_manager() -> None:
    host = ProcessHost(make_boot_manager())

    with host as active:
        assert active is host
        assert host.running is True

    assert host.running is False
    assert host.state == ProcessState.STOPPED


def test_repr() -> None:
    host = ProcessHost(make_boot_manager())

    representation = repr(host)

    assert "ProcessHost" in representation
    assert "stopped" in representation


def test_start_concurrency() -> None:
    host = ProcessHost(make_boot_manager())

    barrier = Barrier(2)
    outcomes: list[str] = []

    def start() -> None:
        barrier.wait()

        try:
            host.start()
            outcomes.append("started")
        except ProcessStateError:
            outcomes.append("rejected")

    threads = [
        Thread(target=start),
        Thread(target=start),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert sorted(outcomes) == [
        "rejected",
        "started",
    ]
    assert host.running is True

    host.stop()


def test_stop_concurrency() -> None:
    host = ProcessHost(make_boot_manager())
    host.start()

    barrier = Barrier(2)
    outcomes: list[str] = []

    def stop() -> None:
        barrier.wait()

        try:
            host.stop()
            outcomes.append("stopped")
        except ProcessStateError:
            outcomes.append("rejected")

    threads = [
        Thread(target=stop),
        Thread(target=stop),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert sorted(outcomes) == [
        "rejected",
        "stopped",
    ]
    assert host.running is False

def test_control_server_is_owned_by_process_host() -> None:
    host = ProcessHost(make_boot_manager())

    assert host.control_server.process_host is host
    assert host.control_server.running is False


def test_start_starts_control_server() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()

    try:
        assert host.control_server.running is True
        assert host.control_server.port != 0
        assert host.health()["control"]["running"] is True
    finally:
        host.stop()


def test_stop_stops_control_server() -> None:
    host = ProcessHost(make_boot_manager())

    host.start()
    assert host.control_server.running is True

    host.stop()

    assert host.control_server.running is False

def test_endpoint_registry_is_owned_by_process_host(
    tmp_path: Path,
) -> None:
    manager = make_boot_manager()

    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    host = ProcessHost(
        manager,
        endpoint_registry=registry,
    )

    assert host.endpoint_registry is registry
    assert registry.exists() is False


def test_start_publishes_control_endpoint(
    tmp_path: Path,
) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    host = ProcessHost(
        make_boot_manager(),
        endpoint_registry=registry,
    )

    host.start()

    try:
        assert registry.exists() is True

        endpoint = registry.load()

        assert endpoint.host == "127.0.0.1"
        assert endpoint.port == host.control_server.port
        assert endpoint.port != 0
    finally:
        host.stop()


def test_stop_removes_control_endpoint(
    tmp_path: Path,
) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    host = ProcessHost(
        make_boot_manager(),
        endpoint_registry=registry,
    )

    host.start()

    assert registry.exists() is True

    host.stop()

    assert registry.exists() is False


def test_health_reports_endpoint(
    tmp_path: Path,
) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    host = ProcessHost(
        make_boot_manager(),
        endpoint_registry=registry,
    )

    host.start()

    try:
        health = host.health()

        assert health["endpoint"]["registered"] is True
        assert health["endpoint"]["path"] == str(registry.path)
        assert health["healthy"] is True
    finally:
        host.stop()


def test_invalid_endpoint_registry_is_rejected() -> None:
    with pytest.raises(TypeError):
        ProcessHost(
            make_boot_manager(),
            endpoint_registry=object(),  # type: ignore[arg-type]
        )


def test_existing_active_endpoint_prevents_start(
    tmp_path: Path,
) -> None:
    first_registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    first = ProcessHost(
        make_boot_manager(),
        endpoint_registry=first_registry,
    )

    first.start()

    try:
        second = ProcessHost(
            make_boot_manager(),
            endpoint_registry=first_registry,
        )

        with pytest.raises(ProcessStartupError):
            second.start()

        assert second.running is False
        assert first.running is True
    finally:
        first.stop()


def test_failed_endpoint_publication_rolls_back_start(
    tmp_path: Path,
) -> None:
    class FailingRegistry(ControlEndpointRegistry):
        def save(self, endpoint) -> None:  # type: ignore[override]
            raise RuntimeError("registry save failed")

    registry = FailingRegistry(
        tmp_path / "control.json",
    )

    host = ProcessHost(
        make_boot_manager(),
        endpoint_registry=registry,
    )

    with pytest.raises(ProcessStartupError):
        host.start()

    assert host.running is False
    assert host.control_server.running is False