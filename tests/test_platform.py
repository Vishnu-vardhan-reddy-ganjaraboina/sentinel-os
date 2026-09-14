"""
Tests for the Sentinel platform coordinator.
"""

import pytest

from sentinel.application import Application
from sentinel.application_host import ApplicationHost
from sentinel.platform import Platform
from sentinel.application_state import ApplicationState


class PlatformTestApplication(Application):
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
            raise RuntimeError("startup failed")

    def shutdown(self) -> None:  # type: ignore[override]
        self.shutdown_count += 1

        if self.fail_shutdown:
            raise RuntimeError("shutdown failed")

    @property
    def health(self):  # type: ignore[override]
        return {"healthy": not self.fail_start}


def test_platform_starts_empty() -> None:
    platform = Platform()

    assert len(platform) == 0
    assert not platform.running
    assert platform.application_states() == {}
    assert platform.health() == {}


def test_custom_host_is_used() -> None:
    host = ApplicationHost()
    platform = Platform(host)

    assert platform.host is host
    assert platform.manager is host.manager


def test_invalid_host_is_rejected() -> None:
    with pytest.raises(TypeError):
        Platform("invalid")  # type: ignore[arg-type]


def test_register_and_get_application() -> None:
    platform = Platform()
    application = PlatformTestApplication()

    platform.register_application(
        "test-app",
        application,
    )

    assert platform.application("test-app") is application
    assert platform.application_states()["test-app"] == (
        ApplicationState.REGISTERED
    )


def test_unregister_application() -> None:
    platform = Platform()
    application = PlatformTestApplication()

    platform.register_application(
        "test-app",
        application,
    )

    result = platform.unregister_application("test-app")

    assert result is application
    assert len(platform) == 0


def test_platform_start() -> None:
    platform = Platform()

    first = PlatformTestApplication()
    second = PlatformTestApplication()

    platform.register_application("first", first)
    platform.register_application("second", second)

    started = platform.start()

    assert started == (first, second)
    assert platform.running
    assert first.start_count == 1
    assert second.start_count == 1


def test_platform_start_is_protected() -> None:
    platform = Platform()
    platform.register_application(
        "test-app",
        PlatformTestApplication(),
    )

    platform.start()

    with pytest.raises(
        RuntimeError,
        match="already running",
    ):
        platform.start()

    platform.shutdown()


def test_register_while_running_is_rejected() -> None:
    platform = Platform()
    platform.register_application(
        "test-app",
        PlatformTestApplication(),
    )
    platform.start()

    with pytest.raises(
        RuntimeError,
        match="Cannot register applications",
    ):
        platform.register_application(
            "second",
            PlatformTestApplication(),
        )

    platform.shutdown()


def test_unregister_while_running_is_rejected() -> None:
    platform = Platform()
    platform.register_application(
        "test-app",
        PlatformTestApplication(),
    )
    platform.start()

    with pytest.raises(
        RuntimeError,
        match="Cannot unregister applications",
    ):
        platform.unregister_application("test-app")

    platform.shutdown()


def test_platform_shutdown() -> None:
    platform = Platform()

    first = PlatformTestApplication()
    second = PlatformTestApplication()

    platform.register_application("first", first)
    platform.register_application("second", second)

    platform.start()
    platform.shutdown()

    assert not platform.running
    assert first.shutdown_count == 1
    assert second.shutdown_count == 1


def test_platform_shutdown_requires_running() -> None:
    platform = Platform()

    with pytest.raises(
        RuntimeError,
        match="not running",
    ):
        platform.shutdown()


def test_platform_start_failure_resets_state() -> None:
    platform = Platform()

    platform.register_application(
        "failing",
        PlatformTestApplication(fail_start=True),
    )

    with pytest.raises(
        RuntimeError,
        match="startup failed",
    ):
        platform.start()

    assert not platform.running
    assert platform.application_states()["failing"] == (
        ApplicationState.FAILED
    )


def test_platform_shutdown_failure_resets_state() -> None:
    platform = Platform()

    platform.register_application(
        "failing",
        PlatformTestApplication(fail_shutdown=True),
    )

    platform.start()

    with pytest.raises(
        RuntimeError,
        match="shutdown failed",
    ):
        platform.shutdown()

    assert not platform.running


def test_application_states_are_snapshot() -> None:
    platform = Platform()

    platform.register_application(
        "test-app",
        PlatformTestApplication(),
    )

    states = platform.application_states()
    states["test-app"] = ApplicationState.FAILED

    assert platform.application_states()["test-app"] == (
        ApplicationState.REGISTERED
    )


def test_health() -> None:
    platform = Platform()

    application = PlatformTestApplication()

    platform.register_application(
        "test-app",
        application,
    )

    assert platform.health()["test-app"]["healthy"] is False

    platform.start()

    assert platform.health()["test-app"]["healthy"] is True

    platform.shutdown()


def test_repr() -> None:
    platform = Platform()

    assert repr(platform) == (
        "Platform(applications=0, running=False)"
    )