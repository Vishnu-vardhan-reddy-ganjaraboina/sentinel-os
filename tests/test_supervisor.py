from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.boot import BootManager
from sentinel.control import ControlEndpointRegistry
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.process import ProcessHost, ProcessState
from sentinel.supervisor import (
    RestartPolicy,
    Supervisor,
    SupervisorState,
    SupervisorStartupError,
    SupervisorStateError,
)
from sentinel.system import System


class SupervisorTestService(Service):
    """Simple service used to create a real ProcessHost."""

    def __init__(
        self,
        *,
        fail_initialize: bool = False,
        fail_shutdown: bool = False,
    ) -> None:
        super().__init__("supervisor-test")
        self.fail_initialize = fail_initialize
        self.fail_shutdown = fail_shutdown

    def initialize(self) -> None:
        if self.fail_initialize:
            raise RuntimeError("supervisor startup failed")

    def shutdown(self) -> None:
        if self.fail_shutdown:
            raise RuntimeError("supervisor shutdown failed")


def make_process(
    *,
    tmp_path: Path | None = None,
    fail_initialize: bool = False,
    fail_shutdown: bool = False,
) -> ProcessHost:
    kernel = Kernel()

    kernel.register(
        SupervisorTestService(
            fail_initialize=fail_initialize,
            fail_shutdown=fail_shutdown,
        )
    )

    system = System(kernel)
    boot_manager = BootManager(system)

    if tmp_path is None:
        return ProcessHost(boot_manager)

    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    return ProcessHost(
        boot_manager,
        endpoint_registry=registry,
    )


def test_constructor() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    assert supervisor.process is process
    assert supervisor.policy == RestartPolicy()
    assert supervisor.state == SupervisorState.STOPPED
    assert supervisor.running is False
    assert supervisor.restart_count == 0


def test_invalid_process() -> None:
    with pytest.raises(TypeError):
        Supervisor(object())  # type: ignore[arg-type]


def test_invalid_policy() -> None:
    process = make_process()

    with pytest.raises(TypeError):
        Supervisor(
            process,
            policy=object(),  # type: ignore[arg-type]
        )


def test_default_policy() -> None:
    policy = RestartPolicy()

    assert policy.enabled is True
    assert policy.max_restarts == 3
    assert policy.backoff_seconds == 1.0


@pytest.mark.parametrize(
    "enabled",
    [True, False],
)
def test_policy_enabled_validation(enabled: bool) -> None:
    policy = RestartPolicy(enabled=enabled)

    assert policy.enabled is enabled


@pytest.mark.parametrize(
    "max_restarts",
    [-1, -5],
)
def test_policy_rejects_negative_restarts(
    max_restarts: int,
) -> None:
    with pytest.raises(ValueError):
        RestartPolicy(max_restarts=max_restarts)


@pytest.mark.parametrize(
    "backoff_seconds",
    [-1, -0.1],
)
def test_policy_rejects_negative_backoff(
    backoff_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        RestartPolicy(backoff_seconds=backoff_seconds)


def test_policy_rejects_invalid_enabled() -> None:
    with pytest.raises(TypeError):
        RestartPolicy(enabled="yes")  # type: ignore[arg-type]


def test_policy_rejects_invalid_max_restarts() -> None:
    with pytest.raises(TypeError):
        RestartPolicy(max_restarts="3")  # type: ignore[arg-type]


def test_policy_rejects_invalid_backoff() -> None:
    with pytest.raises(TypeError):
        RestartPolicy(backoff_seconds="1")  # type: ignore[arg-type]


def test_start() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()

    try:
        assert supervisor.state == SupervisorState.RUNNING
        assert supervisor.running is True
        assert process.running is True
    finally:
        supervisor.stop()


def test_double_start_rejected() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()

    try:
        with pytest.raises(
            SupervisorStateError,
            match="already running",
        ):
            supervisor.start()
    finally:
        supervisor.stop()


def test_stop() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()
    supervisor.stop()

    assert supervisor.state == SupervisorState.STOPPED
    assert supervisor.running is False
    assert process.running is False


def test_stop_requires_running() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    with pytest.raises(
        SupervisorStateError,
        match="not running",
    ):
        supervisor.stop()


def test_restart() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()

    try:
        first_endpoint = process.endpoint_registry.load()

        supervisor.restart()

        assert supervisor.state == SupervisorState.RUNNING
        assert supervisor.running is True
        assert process.running is True
        assert supervisor.restart_count == 1

        second_endpoint = process.endpoint_registry.load()

        assert second_endpoint.port != 0
        assert first_endpoint.port != 0
    finally:
        supervisor.stop()


def test_multiple_restarts() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()

    try:
        supervisor.restart()
        supervisor.restart()
        supervisor.restart()

        assert supervisor.state == SupervisorState.RUNNING
        assert supervisor.restart_count == 3
    finally:
        supervisor.stop()


def test_restart_requires_running() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    with pytest.raises(
        SupervisorStateError,
        match="not running",
    ):
        supervisor.restart()


def test_startup_failure_returns_to_stopped() -> None:
    process = make_process(
        fail_initialize=True,
    )
    supervisor = Supervisor(process)

    with pytest.raises(SupervisorStartupError):
        supervisor.start()

    assert supervisor.state == SupervisorState.STOPPED
    assert supervisor.running is False


def test_health_before_start() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    health = supervisor.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False
    assert health["restart_count"] == 0
    assert health["policy"]["enabled"] is True
    assert health["process"]["running"] is False


def test_health_while_running() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()

    try:
        health = supervisor.health()

        assert health["state"] == "running"
        assert health["running"] is True
        assert health["healthy"] is True
        assert health["process"]["running"] is True
        assert health["process"]["healthy"] is True
    finally:
        supervisor.stop()


def test_health_after_stop() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    supervisor.start()
    supervisor.stop()

    health = supervisor.health()

    assert health["state"] == "stopped"
    assert health["running"] is False
    assert health["healthy"] is False
    assert health["process"]["running"] is False


def test_repr() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    representation = repr(supervisor)

    assert "Supervisor" in representation
    assert "stopped" in representation
    assert "restart_count=0" in representation


def test_process_property() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    assert supervisor.process is process


def test_policy_property() -> None:
    process = make_process()
    policy = RestartPolicy(
        enabled=False,
        max_restarts=5,
        backoff_seconds=2.5,
    )

    supervisor = Supervisor(
        process,
        policy=policy,
    )

    assert supervisor.policy is policy


def test_restart_count_is_read_only() -> None:
    process = make_process()
    supervisor = Supervisor(process)

    assert supervisor.restart_count == 0

# ---------------------------------------------------------------------------
# Supervisor monitor tests
# ---------------------------------------------------------------------------

import time

from sentinel.supervisor import SupervisorMonitor


def test_monitor_constructor() -> None:
    process = make_process()
    monitor = SupervisorMonitor(process)

    assert monitor.process is process
    assert monitor.interval == 1.0
    assert monitor.running is False
    assert monitor.failure_detected is False


def test_monitor_rejects_invalid_process() -> None:
    with pytest.raises(TypeError):
        SupervisorMonitor(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "interval",
    [0, -1, -0.1],
)
def test_monitor_rejects_invalid_interval(
    interval: float,
) -> None:
    process = make_process()

    with pytest.raises(ValueError):
        SupervisorMonitor(
            process,
            interval=interval,
        )


def test_monitor_rejects_non_numeric_interval() -> None:
    process = make_process()

    with pytest.raises(TypeError):
        SupervisorMonitor(
            process,
            interval="1",  # type: ignore[arg-type]
        )


def test_monitor_rejects_invalid_callback() -> None:
    process = make_process()

    with pytest.raises(TypeError):
        SupervisorMonitor(
            process,
            on_failure="callback",  # type: ignore[arg-type]
        )


def test_monitor_start() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    monitor.start()

    try:
        assert monitor.running is True
        assert monitor.failure_detected is False
    finally:
        monitor.stop()


def test_monitor_start_is_idempotent() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    monitor.start()

    try:
        first_thread = monitor._thread

        monitor.start()

        assert monitor.running is True
        assert monitor._thread is first_thread
    finally:
        monitor.stop()


def test_monitor_stop_is_safe_before_start() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    monitor.stop()

    assert monitor.running is False


def test_monitor_stop() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    monitor.start()
    monitor.stop()

    assert monitor.running is False


def test_monitor_detects_stopped_process() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    process.start()

    try:
        monitor.start()
        process.stop()

        deadline = time.monotonic() + 1.0

        while (
            not monitor.failure_detected
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert monitor.failure_detected is True
    finally:
        if monitor.running:
            monitor.stop()

        if process.running:
            process.stop()


def test_monitor_does_not_report_running_process_as_failed() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    process.start()

    try:
        monitor.start()

        time.sleep(0.05)

        assert monitor.failure_detected is False
    finally:
        monitor.stop()

        if process.running:
            process.stop()


def test_monitor_failure_callback() -> None:
    process = make_process()
    failures: list[str] = []

    def on_failure() -> None:
        failures.append("failure")

    monitor = SupervisorMonitor(
        process,
        interval=0.01,
        on_failure=on_failure,
    )

    process.start()

    try:
        monitor.start()
        process.stop()

        deadline = time.monotonic() + 1.0

        while (
            not failures
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert failures == ["failure"]
        assert monitor.failure_detected is True
    finally:
        if monitor.running:
            monitor.stop()

        if process.running:
            process.stop()


def test_monitor_failure_callback_is_called_once() -> None:
    process = make_process()
    failures: list[str] = []

    monitor = SupervisorMonitor(
        process,
        interval=0.01,
        on_failure=lambda: failures.append("failure"),
    )

    process.start()

    try:
        monitor.start()
        process.stop()

        deadline = time.monotonic() + 1.0

        while (
            not monitor.failure_detected
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        time.sleep(0.05)

        assert failures == ["failure"]
    finally:
        if monitor.running:
            monitor.stop()

        if process.running:
            process.stop()


def test_monitor_can_restart_after_stop() -> None:
    process = make_process()
    monitor = SupervisorMonitor(
        process,
        interval=0.01,
    )

    monitor.start()
    monitor.stop()

    assert monitor.running is False

    monitor.start()

    try:
        assert monitor.running is True
    finally:
        monitor.stop()


def test_monitor_repr_not_required() -> None:
    process = make_process()
    monitor = SupervisorMonitor(process)

    assert "SupervisorMonitor" in type(monitor).__name__

def test_supervisor_automatic_restart_respects_backoff(monkeypatch, tmp_path):
    process = make_process(tmp_path=tmp_path)
    policy = RestartPolicy(
        enabled=True,
        max_restarts=3,
        backoff_seconds=2.0,
    )
    supervisor = Supervisor(
        process,
        policy=policy,
        monitor_interval=0.01,
    )

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        "sentinel.supervisor.supervisor.sleep",
        fake_sleep,
    )

    supervisor.start()

    supervisor.monitor.stop()
    process.stop()
    supervisor._handle_process_failure()

    assert sleep_calls == [2.0]
    assert supervisor.restart_count == 1
    assert supervisor.state == SupervisorState.RUNNING

    supervisor.stop()


def test_supervisor_explicit_restart_respects_backoff(monkeypatch, tmp_path):
    process = make_process(tmp_path=tmp_path)
    policy = RestartPolicy(
        enabled=True,
        max_restarts=3,
        backoff_seconds=3.0,
    )
    supervisor = Supervisor(
        process,
        policy=policy,
        monitor_interval=0.01,
    )

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        "sentinel.supervisor.supervisor.sleep",
        fake_sleep,
    )

    supervisor.start()
    supervisor.restart()

    assert sleep_calls == [3.0]
    assert supervisor.restart_count == 1
    assert supervisor.state == SupervisorState.RUNNING

    supervisor.stop()


def test_supervisor_zero_backoff_does_not_sleep(monkeypatch, tmp_path):
    process = make_process(tmp_path=tmp_path)
    policy = RestartPolicy(
        enabled=True,
        max_restarts=3,
        backoff_seconds=0,
    )
    supervisor = Supervisor(
        process,
        policy=policy,
        monitor_interval=0.01,
    )

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        "sentinel.supervisor.supervisor.sleep",
        fake_sleep,
    )

    supervisor.start()

    supervisor.monitor.stop()
    process.stop()
    supervisor._handle_process_failure()

    assert sleep_calls == []
    assert supervisor.restart_count == 1
    assert supervisor.state == SupervisorState.RUNNING

    supervisor.stop()