"""
Tests for the Sentinel OS system lifecycle coordinator.
"""

from __future__ import annotations

from threading import Event, Thread

import pytest

from sentinel.application import Application
from sentinel.application_manifest import ApplicationManifest
from sentinel.application_state import ApplicationState
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.platform import Platform
from sentinel.system import System


class SystemTestApplication(Application):
    """Restartable application test double."""

    def __init__(
        self,
        fail_start: bool = False,
        fail_shutdown: bool = False,
    ) -> None:
        super().__init__()
        self.fail_start = fail_start
        self.fail_shutdown = fail_shutdown
        self.start_count = 0
        self.shutdown_count = 0

    def start(self):  # type: ignore[override]
        self.start_count += 1

        if self.fail_start:
            raise RuntimeError("application startup failed")

    def shutdown(self) -> None:  # type: ignore[override]
        self.shutdown_count += 1

        if self.fail_shutdown:
            raise RuntimeError("application shutdown failed")

    @property
    def health(self):  # type: ignore[override]
        return {"healthy": not self.fail_start}


class SystemTestService(Service):
    """Simple kernel service test double."""

    def __init__(
        self,
        name: str,
        events: list[str],
        fail_initialize: bool = False,
        fail_shutdown: bool = False,
    ) -> None:
        super().__init__(name)
        self.events = events
        self.fail_initialize = fail_initialize
        self.fail_shutdown = fail_shutdown

    def initialize(self) -> None:
        self.events.append(f"start:{self.name}")

        if self.fail_initialize:
            raise RuntimeError("kernel startup failed")

    def shutdown(self) -> None:
        self.events.append(f"stop:{self.name}")

        if self.fail_shutdown:
            raise RuntimeError("kernel shutdown failed")


class BlockingSystemTestService(SystemTestService):
    """Kernel service that blocks during initialization."""

    def __init__(
        self,
        name: str,
        events: list[str],
        entered: Event,
        release: Event,
    ) -> None:
        super().__init__(name, events)
        self.entered = entered
        self.release = release

    def initialize(self) -> None:
        self.events.append(f"start:{self.name}")
        self.entered.set()

        if not self.release.wait(timeout=5):
            raise RuntimeError("timed out waiting for startup release")


class BlockingShutdownApplication(SystemTestApplication):
    """Application that blocks during shutdown."""

    def __init__(
        self,
        entered: Event,
        release: Event,
    ) -> None:
        super().__init__()
        self.entered = entered
        self.release = release

    def shutdown(self) -> None:  # type: ignore[override]
        self.shutdown_count += 1
        self.entered.set()

        if not self.release.wait(timeout=5):
            raise RuntimeError("timed out waiting for shutdown release")


def test_system_starts_stopped() -> None:
    system = System(Kernel())

    assert not system.running


def test_invalid_kernel_is_rejected() -> None:
    with pytest.raises(TypeError):
        System("invalid")  # type: ignore[arg-type]


def test_invalid_platform_is_rejected() -> None:
    with pytest.raises(TypeError):
        System(Kernel(), "invalid")  # type: ignore[arg-type]


def test_custom_platform_is_used() -> None:
    platform = Platform()
    system = System(Kernel(), platform)

    assert system.platform is platform
    assert system.host is platform.host


def test_register_application_before_start() -> None:
    system = System(Kernel())
    application = SystemTestApplication()

    system.register_application(
        "test-app",
        application,
        ApplicationManifest(name="test-app"),
    )

    assert system.platform.application("test-app") is application
    assert system.platform.application_states()["test-app"] == (
        ApplicationState.REGISTERED
    )


def test_register_application_while_running_is_rejected() -> None:
    system = System(Kernel())

    system.start()

    with pytest.raises(
        RuntimeError,
        match="while system is running",
    ):
        system.register_application(
            "test-app",
            SystemTestApplication(),
        )

    system.shutdown()


def test_start_system() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    system = System(kernel)

    system.start()

    assert system.running
    assert system.kernel.health()["healthy"] is True

    system.shutdown()


def test_start_system_starts_kernel_before_platform() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    class RecordingApplication(SystemTestApplication):
        def start(self):  # type: ignore[override]
            events.append("application")
            super().start()

    system = System(kernel)
    system.register_application(
        "app",
        RecordingApplication(),
    )

    system.start()

    assert events == [
        "start:service",
        "application",
    ]

    system.shutdown()


def test_double_start_is_rejected() -> None:
    system = System(Kernel())

    system.start()

    with pytest.raises(
        RuntimeError,
        match="already running",
    ):
        system.start()

    system.shutdown()


def test_shutdown_stops_platform_before_kernel() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    class RecordingApplication(SystemTestApplication):
        def shutdown(self) -> None:
            events.append("application")
            super().shutdown()

    system = System(kernel)
    system.register_application(
        "app",
        RecordingApplication(),
    )

    system.start()
    system.shutdown()

    assert events == [
        "start:service",
        "application",
        "stop:service",
    ]


def test_shutdown_requires_running_system() -> None:
    system = System(Kernel())

    with pytest.raises(
        RuntimeError,
        match="not running",
    ):
        system.shutdown()


def test_application_start_failure_shuts_down_kernel() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    system = System(kernel)

    system.register_application(
        "failing",
        SystemTestApplication(fail_start=True),
    )

    with pytest.raises(
        RuntimeError,
        match="application startup failed",
    ):
        system.start()

    assert not system.running
    assert system.platform.running is False
    assert system.kernel.health()["healthy"] is False


def test_kernel_start_failure_does_not_start_platform() -> None:
    kernel = Kernel()

    kernel.register(
        SystemTestService(
            "failing",
            [],
            fail_initialize=True,
        ),
    )

    application = SystemTestApplication()
    system = System(kernel)

    system.register_application(
        "app",
        application,
    )

    with pytest.raises(
        RuntimeError,
        match="kernel startup failed",
    ):
        system.start()

    assert not system.running
    assert application.start_count == 0
    assert not system.platform.running


def test_shutdown_continues_to_kernel_after_application_failure() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    system = System(kernel)

    system.register_application(
        "failing",
        SystemTestApplication(fail_shutdown=True),
    )

    system.start()

    with pytest.raises(
        RuntimeError,
        match="application shutdown failed",
    ):
        system.shutdown()

    assert not system.running
    assert "stop:service" in events


def test_health_when_running() -> None:
    events: list[str] = []

    kernel = Kernel()
    kernel.register(
        SystemTestService("service", events),
    )

    system = System(kernel)

    system.start()

    health = system.health()

    assert health["running"] is True
    assert health["kernel"]["healthy"] is True
    assert health["platform"] == {}
    assert health["healthy"] is True

    system.shutdown()


def test_health_before_start() -> None:
    system = System(Kernel())

    health = system.health()

    assert health["running"] is False
    assert health["kernel"]["healthy"] is False
    assert health["healthy"] is False


def test_repr() -> None:
    system = System(Kernel())

    assert repr(system) == (
        "System(running=False, applications=0)"
    )


def test_start_rejects_concurrent_start_during_startup() -> None:
    events: list[str] = []
    entered = Event()
    release = Event()

    kernel = Kernel()
    kernel.register(
        BlockingSystemTestService(
            "blocking",
            events,
            entered,
            release,
        ),
    )

    system = System(kernel)
    errors: list[Exception] = []

    def start_system() -> None:
        try:
            system.start()
        except Exception as exc:
            errors.append(exc)

    thread = Thread(target=start_system)
    thread.start()

    assert entered.wait(timeout=5)

    with pytest.raises(
        RuntimeError,
        match="transitioning",
    ):
        system.start()

    release.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert errors == []
    assert system.running

    system.shutdown()


def test_register_application_rejects_during_system_startup() -> None:
    events: list[str] = []
    entered = Event()
    release = Event()

    kernel = Kernel()
    kernel.register(
        BlockingSystemTestService(
            "blocking",
            events,
            entered,
            release,
        ),
    )

    system = System(kernel)
    startup_errors: list[Exception] = []

    def start_system() -> None:
        try:
            system.start()
        except Exception as exc:
            startup_errors.append(exc)

    thread = Thread(target=start_system)
    thread.start()

    assert entered.wait(timeout=5)

    with pytest.raises(
        RuntimeError,
        match="transitioning",
    ):
        system.register_application(
            "during-start",
            SystemTestApplication(),
        )

    release.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert startup_errors == []
    assert system.running

    system.shutdown()


def test_shutdown_rejects_concurrent_shutdown() -> None:
    entered = Event()
    release = Event()

    system = System(Kernel())
    application = BlockingShutdownApplication(
        entered,
        release,
    )

    system.register_application(
        "blocking-shutdown",
        application,
    )

    system.start()

    shutdown_errors: list[Exception] = []

    def shutdown_system() -> None:
        try:
            system.shutdown()
        except Exception as exc:
            shutdown_errors.append(exc)

    thread = Thread(target=shutdown_system)
    thread.start()

    assert entered.wait(timeout=5)

    with pytest.raises(
        RuntimeError,
        match="transitioning",
    ):
        system.shutdown()

    release.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert shutdown_errors == []
    assert not system.running
    assert application.shutdown_count == 1