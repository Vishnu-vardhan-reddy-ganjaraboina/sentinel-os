import pytest

from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service


class DummyService(Service):
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
    application = DummyService("application", ("database",))

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
    application = DummyService("application", ("logger",))

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

    result = kernel.get_typed("logger", DummyService)

    assert result is logger


def test_get_typed_rejects_wrong_type() -> None:
    kernel = Kernel()
    logger = DummyService("logger")

    kernel.register(logger)

    with pytest.raises(TypeError):
        kernel.get_typed("logger", Service)