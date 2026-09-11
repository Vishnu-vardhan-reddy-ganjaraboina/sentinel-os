import pytest

from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service


class DummyService(Service):
    """
    Test service used to verify Kernel behavior.
    """

    def __init__(
        self,
        name: str,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        super().__init__(name, dependencies)
        self.initialized = False
        self.stopped = False

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.stopped = True


class OtherService(Service):
    """
    Different concrete Service type used for get_typed()
    rejection testing.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def test_register_service() -> None:
    kernel = Kernel()
    service = DummyService("logger")

    kernel.register(service)

    assert kernel.get("logger") is service
    assert len(kernel) == 1


def test_get_missing_service() -> None:
    kernel = Kernel()

    with pytest.raises(ServiceNotFoundError):
        kernel.get("missing")


def test_boot_starts_services_in_dependency_order() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    database = DummyService("database", ("logger",))
    application = DummyService(
        "application",
        ("database",),
    )

    kernel.register(application)
    kernel.register(database)
    kernel.register(logger)

    kernel.boot()

    assert logger.initialized
    assert database.initialized
    assert application.initialized

    assert kernel.running("logger")
    assert kernel.running("database")
    assert kernel.running("application")


def test_shutdown_stops_services() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    application = DummyService(
        "application",
        ("logger",),
    )

    kernel.register(application)
    kernel.register(logger)

    kernel.boot()
    kernel.shutdown()

    assert logger.stopped
    assert application.stopped


def test_services_returns_registered_services() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    brain = DummyService("brain")

    kernel.register(logger)
    kernel.register(brain)

    services = kernel.services()

    assert services == (logger, brain)


def test_get_typed_returns_expected_type() -> None:
    kernel = Kernel()
    logger = DummyService("logger")

    kernel.register(logger)

    result = kernel.get_typed(
        "logger",
        DummyService,
    )

    assert result is logger


def test_get_typed_accepts_parent_service_type() -> None:
    kernel = Kernel()
    logger = DummyService("logger")

    kernel.register(logger)

    result = kernel.get_typed(
        "logger",
        Service,
    )

    assert result is logger


def test_get_typed_rejects_wrong_type() -> None:
    kernel = Kernel()
    logger = DummyService("logger")

    kernel.register(logger)

    with pytest.raises(TypeError):
        kernel.get_typed(
            "logger",
            OtherService,
        )

def test_boot_rolls_back_started_services_on_failure() -> None:
    kernel = Kernel()

    logger = DummyService("logger")

    class FailingService(Service):
        def __init__(self) -> None:
            super().__init__(
                "failing",
                ("logger",),
            )

        def initialize(self) -> None:
            raise RuntimeError("startup failed")

        def shutdown(self) -> None:
            pass

    failing = FailingService()

    kernel.register(failing)
    kernel.register(logger)

    with pytest.raises(RuntimeError, match="startup failed"):
        kernel.boot()

    assert logger.stopped
    assert not kernel.running("logger")


def test_shutdown_continues_when_one_service_fails() -> None:
    kernel = Kernel()

    class FailingShutdownService(Service):
        def __init__(
            self,
            name: str,
            dependencies: tuple[str, ...] = (),
        ) -> None:
            super().__init__(name, dependencies)
            self.initialized = False
            self.stopped = False

        def initialize(self) -> None:
            self.initialized = True

        def shutdown(self) -> None:
            self.stopped = True
            raise RuntimeError("shutdown failed")

    logger = DummyService("logger")

    failing = FailingShutdownService(
        "failing",
        ("logger",),
    )

    application = DummyService(
        "application",
        ("failing",),
    )

    kernel.register(application)
    kernel.register(failing)
    kernel.register(logger)

    kernel.boot()

    with pytest.raises(RuntimeError, match="shutdown failed"):
        kernel.shutdown()

    assert application.stopped
    assert failing.stopped
    assert logger.stopped

def test_health_reports_all_services() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    database = DummyService(
        "database",
        ("logger",),
    )

    kernel.register(logger)
    kernel.register(database)

    health = kernel.health()

    assert health["healthy"] is False
    assert health["services"] == {
        "logger": {"healthy": True},
        "database": {"healthy": True},
    }


def test_health_reports_unhealthy_service() -> None:
    kernel = Kernel()

    class UnhealthyService(Service):
        def __init__(self) -> None:
            super().__init__("unhealthy")

        def initialize(self) -> None:
            pass

        def shutdown(self) -> None:
            pass

        def health(self) -> dict[str, bool]:
            return {"healthy": False}

    healthy = DummyService("healthy")
    unhealthy = UnhealthyService()

    kernel.register(healthy)
    kernel.register(unhealthy)

    health = kernel.health()

    assert health["healthy"] is False
    assert health["services"]["healthy"] == {
        "healthy": True,
    }
    assert health["services"]["unhealthy"] == {
        "healthy": False,
    }


def test_health_is_healthy_after_all_services_start() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    database = DummyService(
        "database",
        ("logger",),
    )

    kernel.register(database)
    kernel.register(logger)

    assert kernel.health()["healthy"] is False

    kernel.boot()

    health = kernel.health()

    assert health["healthy"] is True
    assert health["services"]["logger"]["healthy"] is True
    assert health["services"]["database"]["healthy"] is True


def test_health_is_unhealthy_after_services_stop() -> None:
    kernel = Kernel()

    logger = DummyService("logger")
    kernel.register(logger)

    kernel.boot()
    assert kernel.health()["healthy"] is True

    kernel.shutdown()

    health = kernel.health()

    assert health["healthy"] is False
    assert health["services"]["logger"]["healthy"] is True