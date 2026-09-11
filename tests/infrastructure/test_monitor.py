import pytest

from sentinel.infrastructure.monitor import Monitor
from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.infrastructure.exceptions import MonitorError
from sentinel.kernel.service_state import ServiceState
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service


def test_register_service() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.CREATED,
    )

    health = monitor.get_health("kernel")

    assert health.service_name == "kernel"
    assert health.state == ServiceState.CREATED
    assert health.healthy is True
    assert health.error_count == 0


def test_update_state() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.CREATED,
    )

    monitor.update_state(
        "kernel",
        ServiceState.RUNNING,
    )

    assert (
        monitor.get_health("kernel").state
        == ServiceState.RUNNING
    )


def test_mark_unhealthy() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    monitor.mark_unhealthy("kernel")

    health = monitor.get_health("kernel")

    assert health.healthy is False
    assert health.error_count == 1


def test_mark_healthy() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    monitor.mark_unhealthy("kernel")
    monitor.mark_healthy("kernel")

    assert monitor.get_health("kernel").healthy is True


def test_unknown_service() -> None:
    monitor = Monitor()

    with pytest.raises(ServiceNotFoundError):
        monitor.get_health("unknown")


def test_shutdown() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    monitor.shutdown()

    assert monitor.get_all_health() == {}

def test_duplicate_service_rejected() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.CREATED,
    )

    with pytest.raises(ValueError, match="already registered"):
        monitor.register_service(
            "kernel",
            ServiceState.RUNNING,
        )


def test_invalid_service_name_rejected() -> None:
    monitor = Monitor()

    with pytest.raises(TypeError):
        monitor.register_service(
            123,  # type: ignore[arg-type]
            ServiceState.CREATED,
        )

    with pytest.raises(ValueError):
        monitor.register_service(
            "   ",
            ServiceState.CREATED,
        )


def test_invalid_state_rejected() -> None:
    monitor = Monitor()

    with pytest.raises(TypeError):
        monitor.register_service(
            "kernel",
            "running",  # type: ignore[arg-type]
        )


def test_health_snapshot_is_isolated() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    health = monitor.get_health("kernel")
    health.healthy = False
    health.error_count = 999

    actual = monitor.get_health("kernel")

    assert actual.healthy is True
    assert actual.error_count == 0


def test_all_health_snapshot_is_isolated() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    snapshot = monitor.get_all_health()
    snapshot["kernel"].healthy = False
    snapshot.pop("kernel")

    assert len(monitor.get_all_health()) == 1
    assert monitor.get_health("kernel").healthy is True


def test_shutdown_rejects_future_operations() -> None:
    monitor = Monitor()

    monitor.register_service(
        "kernel",
        ServiceState.RUNNING,
    )

    monitor.shutdown()

    with pytest.raises(Exception):
        monitor.get_health("kernel")

def test_sync_kernel_registers_running_services() -> None:
    monitor = Monitor()
    kernel = Kernel()

    class DummyService(Service):
        def __init__(self) -> None:
            super().__init__("dummy")

        def initialize(self) -> None:
            pass

        def shutdown(self) -> None:
            pass

    service = DummyService()
    kernel.register(service)
    kernel.boot()

    monitor.sync_kernel(kernel)

    health = monitor.get_health("dummy")

    assert health.state is ServiceState.RUNNING
    assert health.healthy is True

    kernel.shutdown()
    monitor.shutdown()


def test_sync_kernel_updates_unhealthy_service() -> None:
    monitor = Monitor()
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

    service = UnhealthyService()
    kernel.register(service)
    kernel.boot()

    monitor.sync_kernel(kernel)

    health = monitor.get_health("unhealthy")

    assert health.state is ServiceState.RUNNING
    assert health.healthy is False

    kernel.shutdown()
    monitor.shutdown()


def test_sync_kernel_handles_stopped_services() -> None:
    monitor = Monitor()
    kernel = Kernel()

    class DummyService(Service):
        def __init__(self) -> None:
            super().__init__("dummy")

        def initialize(self) -> None:
            pass

        def shutdown(self) -> None:
            pass

    service = DummyService()
    kernel.register(service)
    kernel.boot()
    kernel.shutdown()

    monitor.sync_kernel(kernel)

    health = monitor.get_health("dummy")

    assert health.state is ServiceState.STOPPED
    assert health.healthy is False

    monitor.shutdown()


def test_sync_kernel_rejects_invalid_kernel() -> None:
    monitor = Monitor()

    with pytest.raises(TypeError):
        monitor.sync_kernel(object())  # type: ignore[arg-type]