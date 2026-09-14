"""
Tests for the Sentinel application host.
"""

import pytest

from sentinel.application import Application
from sentinel.application_host import ApplicationHost
from sentinel.application_manager import ApplicationManager
from sentinel.application_state import ApplicationState

from sentinel.application_dependency_resolver import (
    ApplicationDependencyCycleError,
    ApplicationDependencyMissingError,
    ApplicationDependencyResolver,
)
from sentinel.application_manifest import ApplicationManifest



class HostTestApplication(Application):
    """Restartable test application for host tests."""

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
        if self.fail_start:
            return {
                "healthy": False,
                "reason": "startup failure configured",
            }

        return {
            "healthy": True,
        }


def test_host_starts_empty() -> None:
    host = ApplicationHost()

    assert len(host) == 0
    assert not host.running
    assert host.states() == {}


def test_custom_manager_is_used() -> None:
    manager = ApplicationManager()
    host = ApplicationHost(manager)

    assert host.manager is manager


def test_invalid_manager_is_rejected() -> None:
    with pytest.raises(TypeError):
        ApplicationHost("invalid")  # type: ignore[arg-type]


def test_register_and_get_application() -> None:
    host = ApplicationHost()
    application = HostTestApplication()

    host.register("test-app", application)

    assert host.get("test-app") is application
    assert host.state("test-app") == ApplicationState.REGISTERED


def test_host_cannot_start_single_application_when_stopped() -> None:
    host = ApplicationHost()
    host.register("test-app", HostTestApplication())

    with pytest.raises(
        RuntimeError,
        match="Application host is not running",
    ):
        host.start("test-app")


def test_start_all_starts_applications_in_order() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    second = HostTestApplication()
    third = HostTestApplication()

    host.register("first", first)
    host.register("second", second)
    host.register("third", third)

    started = host.start_all()

    assert started == (first, second, third)
    assert host.running

    assert first.start_count == 1
    assert second.start_count == 1
    assert third.start_count == 1

    assert all(
        state == ApplicationState.RUNNING
        for state in host.states().values()
    )


def test_start_all_is_idempotence_protected() -> None:
    host = ApplicationHost()
    host.register("test-app", HostTestApplication())

    host.start_all()

    with pytest.raises(
        RuntimeError,
        match="Application host is already running",
    ):
        host.start_all()

    host.stop_all()


def test_stop_all_stops_in_reverse_order() -> None:
    events: list[str] = []

    class RecordingApplication(HostTestApplication):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.application_name = name

        def shutdown(self) -> None:
            events.append(self.application_name)
            super().shutdown()

    host = ApplicationHost()

    first = RecordingApplication("first")
    second = RecordingApplication("second")
    third = RecordingApplication("third")

    host.register("first", first)
    host.register("second", second)
    host.register("third", third)

    host.start_all()
    host.stop_all()

    assert events == ["third", "second", "first"]
    assert not host.running


def test_stop_all_requires_running_host() -> None:
    host = ApplicationHost()

    with pytest.raises(
        RuntimeError,
        match="Application host is not running",
    ):
        host.stop_all()


def test_start_all_rolls_back_started_applications() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    failing = HostTestApplication(fail_start=True)
    third = HostTestApplication()

    host.register("first", first)
    host.register("failing", failing)
    host.register("third", third)

    with pytest.raises(
        RuntimeError,
        match="startup failed",
    ):
        host.start_all()

    assert first.shutdown_count == 1
    assert first.start_count == 1
    assert failing.start_count == 1
    assert third.start_count == 0

    assert not host.running
    assert host.state("first") == ApplicationState.STOPPED
    assert host.state("failing") == ApplicationState.FAILED
    assert host.state("third") == ApplicationState.REGISTERED


def test_stop_all_continues_after_failure() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    failing = HostTestApplication(fail_shutdown=True)
    third = HostTestApplication()

    host.register("first", first)
    host.register("failing", failing)
    host.register("third", third)

    host.start_all()

    with pytest.raises(
        RuntimeError,
        match="shutdown failed",
    ):
        host.stop_all()

    assert third.shutdown_count == 1
    assert failing.shutdown_count == 1
    assert first.shutdown_count == 1
    assert not host.running


def test_health_all() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    second = HostTestApplication()

    host.register("first", first)
    host.register("second", second)

    health = host.health_all()

    assert health["first"]["healthy"] is False
    assert health["second"]["healthy"] is False

    host.start_all()

    health = host.health_all()

    assert health["first"]["healthy"] is True
    assert health["second"]["healthy"] is True

    host.stop_all()


def test_unregister_application() -> None:
    host = ApplicationHost()
    application = HostTestApplication()

    host.register("test-app", application)

    result = host.unregister("test-app")

    assert result is application
    assert len(host) == 0


def test_unregister_active_application_is_rejected() -> None:
    host = ApplicationHost()
    host.register("test-app", HostTestApplication())

    host.start_all()

    with pytest.raises(
        RuntimeError,
        match="Application 'test-app' is active",
    ):
        host.unregister("test-app")

    host.stop_all()


def test_repr() -> None:
    host = ApplicationHost()

    assert repr(host) == (
        "ApplicationHost(applications=0, running=False)"
    )

def test_concurrent_start_all_allows_only_one_start() -> None:
    import threading

    class BlockingApplication(HostTestApplication):
        def __init__(self) -> None:
            super().__init__()
            self.started = threading.Event()
            self.release = threading.Event()

        def start(self):  # type: ignore[override]
            self.start_count += 1
            self.started.set()
            self.release.wait(timeout=5)

    host = ApplicationHost()
    application = BlockingApplication()

    host.register("test-app", application)

    errors: list[Exception] = []

    def start_host() -> None:
        try:
            host.start_all()
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=start_host)
    second = threading.Thread(target=start_host)

    first.start()
    application.started.wait(timeout=5)
    second.start()

    second.join(timeout=5)

    application.release.set()
    first.join(timeout=5)

    assert application.start_count == 1
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert host.running
    assert host.state("test-app") == ApplicationState.RUNNING

    host.stop_all()


def test_concurrent_stop_all_allows_only_one_stop() -> None:
    import threading

    class BlockingApplication(HostTestApplication):
        def __init__(self) -> None:
            super().__init__()
            self.shutdown_started = threading.Event()
            self.release = threading.Event()

        def shutdown(self) -> None:  # type: ignore[override]
            self.shutdown_count += 1
            self.shutdown_started.set()
            self.release.wait(timeout=5)

    host = ApplicationHost()
    application = BlockingApplication()

    host.register("test-app", application)
    host.start_all()

    errors: list[Exception] = []

    def stop_host() -> None:
        try:
            host.stop_all()
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=stop_host)
    second = threading.Thread(target=stop_host)

    first.start()
    application.shutdown_started.wait(timeout=5)
    second.start()

    second.join(timeout=5)

    application.release.set()
    first.join(timeout=5)

    assert application.shutdown_count == 1
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert not host.running
    assert host.state("test-app") == ApplicationState.STOPPED


def test_start_all_failure_resets_host_running_state() -> None:
    host = ApplicationHost()

    host.register(
        "failing",
        HostTestApplication(fail_start=True),
    )

    with pytest.raises(RuntimeError, match="startup failed"):
        host.start_all()

    assert not host.running


def test_stop_all_failure_resets_host_running_state() -> None:
    host = ApplicationHost()

    host.register(
        "failing",
        HostTestApplication(fail_shutdown=True),
    )

    host.start_all()

    with pytest.raises(RuntimeError, match="shutdown failed"):
        host.stop_all()

    assert not host.running

def test_custom_dependency_resolver_is_used() -> None:
    resolver = ApplicationDependencyResolver()
    host = ApplicationHost(resolver=resolver)

    assert host.resolver is resolver

def test_invalid_dependency_resolver_is_rejected() -> None:
    with pytest.raises(TypeError):
        ApplicationHost(
            resolver="invalid",  # type: ignore[arg-type]
        )

def test_start_all_uses_manifest_dependency_order() -> None:
    events: list[str] = []

    class RecordingApplication(HostTestApplication):
        def __init__(
            self,
            name: str,
        ) -> None:
            super().__init__()
            self.application_name = name

        def start(self):  # type: ignore[override]
            events.append(self.application_name)
            super().start()

        def shutdown(self) -> None:  # type: ignore[override]
            events.append(f"stop:{self.application_name}")
            super().shutdown()

    host = ApplicationHost()

    database = RecordingApplication("database")
    backend = RecordingApplication("backend")
    frontend = RecordingApplication("frontend")

    host.register(
        "frontend",
        frontend,
    )
    host.register(
        "backend",
        backend,
    )
    host.register(
        "database",
        database,
    )

    # Current ApplicationHost registers through ApplicationManager,
    # whose registry now owns manifests. We configure them directly
    # through the manager registry for this contract test.
    host.manager.registry.clear()

    host.manager.registry.register(
        "frontend",
        frontend,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend",),
        ),
    )
    host.manager.registry.register(
        "backend",
        backend,
        ApplicationManifest(
            name="backend",
            dependencies=("database",),
        ),
    )
    host.manager.registry.register(
        "database",
        database,
        ApplicationManifest(
            name="database",
        ),
    )

    # Rebuild manager lifecycle state after direct registry setup.
    host = ApplicationHost(
        ApplicationManager(host.manager.registry),
    )

    for name in host.manager.names():
        host.manager._states[name] = ApplicationState.REGISTERED
        host.manager._errors[name] = None

    host.start_all()

    assert events == [
        "database",
        "backend",
        "frontend",
    ]

    host.stop_all()


def test_start_all_rejects_missing_application_dependency() -> None:
    host = ApplicationHost()

    application = HostTestApplication()

    host.register(
        "frontend",
        application,
    )

    host.manager.registry.unregister("frontend")
    host.manager.registry.register(
        "frontend",
        application,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend",),
        ),
    )

    host = ApplicationHost(
        ApplicationManager(host.manager.registry),
    )

    host.manager._states["frontend"] = ApplicationState.REGISTERED
    host.manager._errors["frontend"] = None

    with pytest.raises(
        ApplicationDependencyMissingError,
        match="missing application 'backend'",
    ):
        host.start_all()

    assert not host.running


def test_start_all_rejects_dependency_cycle() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    second = HostTestApplication()

    host.register(
        "one",
        first,
        ApplicationManifest(
            name="one",
            dependencies=("two",),
        ),
    )

    host.register(
        "two",
        second,
        ApplicationManifest(
            name="two",
            dependencies=("one",),
        ),
    )

    with pytest.raises(
        ApplicationDependencyCycleError,
        match="dependency cycle",
    ):
        host.start_all()

    assert not host.running
    assert first.start_count == 0
    assert second.start_count == 0

def test_start_all_uses_manifest_dependency_order() -> None:
    events: list[str] = []

    class RecordingApplication(HostTestApplication):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.application_name = name

        def start(self):  # type: ignore[override]
            events.append(self.application_name)
            super().start()

        def shutdown(self) -> None:  # type: ignore[override]
            events.append(f"stop:{self.application_name}")
            super().shutdown()

    host = ApplicationHost()

    frontend = RecordingApplication("frontend")
    backend = RecordingApplication("backend")
    database = RecordingApplication("database")

    host.register(
        "frontend",
        frontend,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend",),
        ),
    )
    host.register(
        "backend",
        backend,
        ApplicationManifest(
            name="backend",
            dependencies=("database",),
        ),
    )
    host.register(
        "database",
        database,
        ApplicationManifest(
            name="database",
        ),
    )

    host.start_all()

    assert events == [
        "database",
        "backend",
        "frontend",
    ]

    host.stop_all()


def test_start_all_rejects_missing_application_dependency() -> None:
    host = ApplicationHost()

    frontend = HostTestApplication()

    host.register(
        "frontend",
        frontend,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend",),
        ),
    )

    with pytest.raises(
        ApplicationDependencyMissingError,
        match="missing application 'backend'",
    ):
        host.start_all()

    assert not host.running
    assert frontend.start_count == 0


def test_start_all_rejects_application_dependency_cycle() -> None:
    host = ApplicationHost()

    first = HostTestApplication()
    second = HostTestApplication()

    host.register(
        "one",
        first,
        ApplicationManifest(
            name="one",
            dependencies=("two",),
        ),
    )
    host.register(
        "two",
        second,
        ApplicationManifest(
            name="two",
            dependencies=("one",),
        ),
    )

    with pytest.raises(
        ApplicationDependencyCycleError,
        match="dependency cycle",
    ):
        host.start_all()

    assert not host.running
    assert first.start_count == 0
    assert second.start_count == 0


def test_stop_all_uses_reverse_dependency_order() -> None:
    events: list[str] = []

    class RecordingApplication(HostTestApplication):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.application_name = name

        def start(self):  # type: ignore[override]
            super().start()

        def shutdown(self) -> None:
            events.append(self.application_name)
            super().shutdown()

    host = ApplicationHost()

    frontend = RecordingApplication("frontend")
    backend = RecordingApplication("backend")
    database = RecordingApplication("database")

    host.register(
        "frontend",
        frontend,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend",),
        ),
    )
    host.register(
        "backend",
        backend,
        ApplicationManifest(
            name="backend",
            dependencies=("database",),
        ),
    )
    host.register(
        "database",
        database,
        ApplicationManifest(
            name="database",
        ),
    )

    host.start_all()
    host.stop_all()

    assert events == [
        "frontend",
        "backend",
        "database",
    ]

def test_start_all_handles_shared_dependencies() -> None:
    events: list[str] = []

    class RecordingApplication(HostTestApplication):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.application_name = name

        def start(self):  # type: ignore[override]
            events.append(self.application_name)
            super().start()

    host = ApplicationHost()

    database = RecordingApplication("database")
    backend = RecordingApplication("backend")
    cache = RecordingApplication("cache")
    frontend = RecordingApplication("frontend")

    host.register(
        "frontend",
        frontend,
        ApplicationManifest(
            name="frontend",
            dependencies=("backend", "cache"),
        ),
    )

    host.register(
        "backend",
        backend,
        ApplicationManifest(
            name="backend",
            dependencies=("database",),
        ),
    )

    host.register(
        "cache",
        cache,
        ApplicationManifest(
            name="cache",
        ),
    )

    host.register(
        "database",
        database,
        ApplicationManifest(
            name="database",
        ),
    )

    started = host.start_all()

    assert started == (
        database,
        backend,
        cache,
        frontend,
    )

    assert events == [
        "database",
        "backend",
        "cache",
        "frontend",
    ]

    host.stop_all()