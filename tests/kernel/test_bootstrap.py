import pytest

from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service


class DummyService(Service):
    def __init__(self, name: str = "dummy") -> None:
        super().__init__(name)
        self.initialized = False
        self.stopped = False

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.stopped = True


class FailingService(Service):
    def __init__(self) -> None:
        super().__init__("failing")

    def initialize(self) -> None:
        raise RuntimeError("boot failed")

    def shutdown(self) -> None:
        pass


def test_start_creates_kernel() -> None:
    bootstrap = Bootstrap(
        services=(DummyService(),)
    )

    kernel = bootstrap.start()

    assert isinstance(kernel, Kernel)
    assert kernel.running("dummy")


def test_double_start_raises() -> None:
    bootstrap = Bootstrap(
        services=(DummyService(),)
    )

    bootstrap.start()

    with pytest.raises(
        RuntimeError,
        match="already running",
    ):
        bootstrap.start()


def test_shutdown_without_start_raises() -> None:
    bootstrap = Bootstrap()

    with pytest.raises(
        RuntimeError,
        match="not running",
    ):
        bootstrap.shutdown()


def test_shutdown_clears_kernel() -> None:
    bootstrap = Bootstrap(
        services=(DummyService(),)
    )

    bootstrap.start()
    bootstrap.shutdown()

    with pytest.raises(
        RuntimeError,
        match="not been started",
    ):
        bootstrap.kernel


def test_kernel_property_before_start_raises() -> None:
    bootstrap = Bootstrap()

    with pytest.raises(
        RuntimeError,
        match="not been started",
    ):
        bootstrap.kernel


def test_failed_start_does_not_retain_kernel() -> None:
    bootstrap = Bootstrap(
        services=(FailingService(),)
    )

    with pytest.raises(
        RuntimeError,
        match="boot failed",
    ):
        bootstrap.start()

    with pytest.raises(
        RuntimeError,
        match="not been started",
    ):
        bootstrap.kernel


def test_failed_start_can_be_retried() -> None:
    bootstrap = Bootstrap(
        services=(FailingService(),)
    )

    with pytest.raises(RuntimeError, match="boot failed"):
        bootstrap.start()

    with pytest.raises(RuntimeError, match="boot failed"):
        bootstrap.start()