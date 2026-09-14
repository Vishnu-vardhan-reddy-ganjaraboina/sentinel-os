"""
Tests for Sentinel application lifecycle management.
"""

import pytest

import threading

from sentinel.application import Application
from sentinel.application_manager import ApplicationManager
from sentinel.application_registry import ApplicationRegistry
from sentinel.application_state import ApplicationState
from sentinel.application_manifest import ApplicationManifest


def create_application() -> Application:
    """Create a fresh Sentinel application for testing."""
    return Application()


def test_manager_starts_empty() -> None:
    manager = ApplicationManager()

    assert len(manager.registry) == 0
    assert manager.states() == {}


def test_register_application() -> None:
    manager = ApplicationManager()
    application = create_application()

    manager.register("test-app", application)

    assert manager.get("test-app") is application
    assert manager.state("test-app") == ApplicationState.REGISTERED
    assert not manager.running("test-app")


def test_register_trims_name() -> None:
    manager = ApplicationManager()
    application = create_application()

    manager.register("  test-app  ", application)

    assert manager.get("test-app") is application
    assert manager.state("test-app") == ApplicationState.REGISTERED


def test_custom_registry_is_used() -> None:
    registry = ApplicationRegistry()
    manager = ApplicationManager(registry)

    application = create_application()

    manager.register("test-app", application)

    assert manager.registry is registry
    assert registry.get("test-app") is application


def test_register_duplicate_application_is_rejected() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())

    with pytest.raises(ValueError):
        manager.register("test-app", create_application())


def test_register_rejects_invalid_registry() -> None:
    with pytest.raises(TypeError):
        ApplicationManager(registry="invalid")  # type: ignore[arg-type]


def test_register_rejects_invalid_name() -> None:
    manager = ApplicationManager()

    with pytest.raises(TypeError):
        manager.register(123, create_application())  # type: ignore[arg-type]


def test_register_rejects_empty_name() -> None:
    manager = ApplicationManager()

    with pytest.raises(ValueError):
        manager.register("   ", create_application())


def test_register_rejects_invalid_application() -> None:
    manager = ApplicationManager()

    with pytest.raises(TypeError):
        manager.register("test-app", object())  # type: ignore[arg-type]


def test_start_application() -> None:
    manager = ApplicationManager()
    application = create_application()

    manager.register("test-app", application)

    result = manager.start("test-app")

    assert result is application
    assert application.running
    assert manager.running("test-app")
    assert manager.state("test-app") == ApplicationState.RUNNING


def test_start_already_running_application_is_rejected() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())
    manager.start("test-app")

    with pytest.raises(RuntimeError):
        manager.start("test-app")

    manager.stop("test-app")


def test_stop_application() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())
    manager.start("test-app")
    manager.stop("test-app")

    assert not manager.get("test-app").running
    assert not manager.running("test-app")
    assert manager.state("test-app") == ApplicationState.STOPPED


def test_stop_non_running_application_is_rejected() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())

    with pytest.raises(RuntimeError):
        manager.stop("test-app")


def test_restart_application() -> None:
    class RestartableApplication(Application):
        def __init__(self) -> None:
            super().__init__()
            self.start_count = 0
            self.shutdown_count = 0

        def start(self):  # type: ignore[override]
            self.start_count += 1
            return None

        def shutdown(self) -> None:  # type: ignore[override]
            self.shutdown_count += 1

    manager = ApplicationManager()
    application = RestartableApplication()

    manager.register("test-app", application)
    manager.start("test-app")

    result = manager.restart("test-app")

    assert result is application
    assert application.start_count == 2
    assert application.shutdown_count == 1
    assert manager.running("test-app")
    assert manager.state("test-app") == ApplicationState.RUNNING

    manager.stop("test-app")


def test_unregister_stopped_application() -> None:
    manager = ApplicationManager()
    application = create_application()

    manager.register("test-app", application)
    manager.start("test-app")
    manager.stop("test-app")

    result = manager.unregister("test-app")

    assert result is application
    assert len(manager.registry) == 0
    assert manager.states() == {}


def test_unregister_running_application_is_rejected() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())
    manager.start("test-app")

    with pytest.raises(RuntimeError):
        manager.unregister("test-app")

    manager.stop("test-app")


def test_unregister_missing_application_is_rejected() -> None:
    manager = ApplicationManager()

    with pytest.raises(KeyError):
        manager.unregister("missing")


def test_get_missing_application_is_rejected() -> None:
    manager = ApplicationManager()

    with pytest.raises(KeyError):
        manager.get("missing")


def test_state_missing_application_is_rejected() -> None:
    manager = ApplicationManager()

    with pytest.raises(KeyError):
        manager.state("missing")


def test_running_missing_application_is_rejected() -> None:
    manager = ApplicationManager()

    with pytest.raises(KeyError):
        manager.running("missing")


def test_states_returns_snapshot() -> None:
    manager = ApplicationManager()

    manager.register("one", create_application())
    manager.register("two", create_application())

    states = manager.states()
    states["one"] = ApplicationState.FAILED

    assert manager.state("one") == ApplicationState.REGISTERED


def test_health_before_start() -> None:
    manager = ApplicationManager()
    manager.register("test-app", create_application())

    health = manager.health("test-app")

    assert health["healthy"] is False
    assert health["state"] == "registered"


def test_health_after_start() -> None:
    manager = ApplicationManager()
    manager.register("test-app", create_application())
    manager.start("test-app")

    health = manager.health("test-app")

    assert health["healthy"] is True
    assert health["state"] == "running"

    manager.stop("test-app")


def test_health_after_stop() -> None:
    manager = ApplicationManager()
    manager.register("test-app", create_application())
    manager.start("test-app")
    manager.stop("test-app")

    health = manager.health("test-app")

    assert health["healthy"] is False
    assert health["state"] == "stopped"


def test_health_missing_application_is_rejected() -> None:
    manager = ApplicationManager()

    with pytest.raises(KeyError):
        manager.health("missing")


def test_lifecycle_failure_sets_failed_state() -> None:
    class FailingApplication(Application):
        def start(self):  # type: ignore[override]
            raise RuntimeError("startup failed")

    manager = ApplicationManager()
    manager.register("failing", FailingApplication())

    with pytest.raises(RuntimeError, match="startup failed"):
        manager.start("failing")

    assert manager.state("failing") == ApplicationState.FAILED
    assert not manager.running("failing")
    assert manager.health("failing")["healthy"] is False
    assert manager.health("failing")["error"] == "startup failed"


def test_shutdown_failure_sets_failed_state() -> None:
    class FailingShutdownApplication(Application):
        def shutdown(self):  # type: ignore[override]
            raise RuntimeError("shutdown failed")

    manager = ApplicationManager()
    manager.register("failing", FailingShutdownApplication())
    manager.start("failing")

    with pytest.raises(RuntimeError, match="shutdown failed"):
        manager.stop("failing")

    assert manager.state("failing") == ApplicationState.FAILED
    assert not manager.running("failing")
    assert manager.health("failing")["healthy"] is False
    assert manager.health("failing")["error"] == "shutdown failed"

def test_all_returns_snapshot() -> None:
    manager = ApplicationManager()

    one = create_application()
    two = create_application()

    manager.register("one", one)
    manager.register("two", two)

    applications = manager.all()

    assert applications == (one, two)


def test_names_returns_snapshot() -> None:
    manager = ApplicationManager()

    manager.register("one", create_application())
    manager.register("two", create_application())

    names = manager.names()

    assert names == ("one", "two")


def test_contains_registered_application() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())

    assert manager.contains("test-app")
    assert not manager.contains("missing")


def test_errors_returns_snapshot() -> None:
    manager = ApplicationManager()

    class FailingApplication(Application):
        def start(self):  # type: ignore[override]
            raise RuntimeError("startup failed")

    manager.register("failing", FailingApplication())

    with pytest.raises(RuntimeError, match="startup failed"):
        manager.start("failing")

    errors = manager.errors()

    assert errors["failing"] == "startup failed"

    errors["failing"] = None

    assert manager.errors()["failing"] == "startup failed"


def test_clear_removes_inactive_applications() -> None:
    manager = ApplicationManager()

    manager.register("one", create_application())
    manager.register("two", create_application())

    manager.clear()

    assert len(manager) == 0
    assert manager.states() == {}
    assert manager.errors() == {}


def test_clear_rejects_active_applications() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())
    manager.start("test-app")

    with pytest.raises(
        RuntimeError,
        match="Cannot clear active applications",
    ):
        manager.clear()

    assert manager.contains("test-app")
    assert manager.running("test-app")

    manager.stop("test-app")


def test_clear_after_stopping_active_application() -> None:
    manager = ApplicationManager()

    manager.register("test-app", create_application())
    manager.start("test-app")
    manager.stop("test-app")

    manager.clear()

    assert len(manager) == 0


def test_unregister_failed_application() -> None:
    class FailingApplication(Application):
        def start(self):  # type: ignore[override]
            raise RuntimeError("startup failed")

    manager = ApplicationManager()
    manager.register("failing", FailingApplication())

    with pytest.raises(RuntimeError, match="startup failed"):
        manager.start("failing")

    application = manager.unregister("failing")

    assert isinstance(application, Application)
    assert len(manager) == 0
    assert manager.states() == {}
    assert manager.errors() == {}


def test_repr() -> None:
    manager = ApplicationManager()
    manager.register("one", create_application())

    assert repr(manager) == "ApplicationManager(applications=1)"

def test_concurrent_start_allows_only_one_start() -> None:
    class BlockingApplication(Application):
        def __init__(self) -> None:
            super().__init__()
            self.start_count = 0
            self.started = threading.Event()
            self.release = threading.Event()

        def start(self):  # type: ignore[override]
            self.start_count += 1
            self.started.set()
            self.release.wait(timeout=5)

        def shutdown(self) -> None:  # type: ignore[override]
            return None

    manager = ApplicationManager()
    application = BlockingApplication()

    manager.register("test-app", application)

    errors: list[Exception] = []

    def start_application() -> None:
        try:
            manager.start("test-app")
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=start_application)
    second = threading.Thread(target=start_application)

    first.start()
    application.started.wait(timeout=5)
    second.start()

    second.join(timeout=5)

    application.release.set()
    first.join(timeout=5)

    assert application.start_count == 1
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert manager.state("test-app") == ApplicationState.RUNNING

    manager.stop("test-app")


def test_concurrent_stop_allows_only_one_stop() -> None:
    class BlockingApplication(Application):
        def __init__(self) -> None:
            super().__init__()
            self.shutdown_count = 0
            self.shutdown_started = threading.Event()
            self.release = threading.Event()

        def start(self):  # type: ignore[override]
            return None

        def shutdown(self) -> None:  # type: ignore[override]
            self.shutdown_count += 1
            self.shutdown_started.set()
            self.release.wait(timeout=5)

    manager = ApplicationManager()
    application = BlockingApplication()

    manager.register("test-app", application)
    manager.start("test-app")

    errors: list[Exception] = []

    def stop_application() -> None:
        try:
            manager.stop("test-app")
        except Exception as exc:
            errors.append(exc)

    first = threading.Thread(target=stop_application)
    second = threading.Thread(target=stop_application)

    first.start()
    application.shutdown_started.wait(timeout=5)
    second.start()

    second.join(timeout=5)

    application.release.set()
    first.join(timeout=5)

    assert application.shutdown_count == 1
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert manager.state("test-app") == ApplicationState.STOPPED


def test_concurrent_registration_rejects_duplicate_name() -> None:
    manager = ApplicationManager()

    errors: list[Exception] = []
    success_count = 0
    lock = threading.Lock()

    def register_application() -> None:
        nonlocal success_count

        try:
            manager.register("shared", Application())
            with lock:
                success_count += 1
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=register_application)
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=5)

    assert success_count == 1
    assert len(errors) == 9
    assert all(
        isinstance(error, ValueError)
        for error in errors
    )
    assert len(manager) == 1

def test_register_with_manifest() -> None:
    manager = ApplicationManager()
    application = Application()

    manifest = ApplicationManifest(
        name="test-app",
        version="1.2.3",
        dependencies=("database",),
        permissions=("execute",),
    )

    manager.register(
        "test-app",
        application,
        manifest,
    )

    assert manager.manifest("test-app") is manifest


def test_register_rejects_invalid_manifest() -> None:
    manager = ApplicationManager()

    with pytest.raises(TypeError):
        manager.register(
            "test-app",
            Application(),
            "invalid",  # type: ignore[arg-type]
        )


def test_manager_manifest_lookup() -> None:
    manager = ApplicationManager()

    manager.register(
        "test-app",
        Application(),
        ApplicationManifest(
            name="test-app",
            version="2.0.0",
        ),
    )

    manifest = manager.manifest("test-app")

    assert manifest.name == "test-app"
    assert manifest.version == "2.0.0"


def test_manager_manifests_snapshot() -> None:
    manager = ApplicationManager()

    first = ApplicationManifest(name="first")
    second = ApplicationManifest(name="second")

    manager.register("first", Application(), first)
    manager.register("second", Application(), second)

    assert manager.manifests() == (
        ("first", first),
        ("second", second),
    )