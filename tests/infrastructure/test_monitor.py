import pytest

from sentinel.infrastructure.monitor import Monitor
from sentinel.kernel.exceptions import ServiceNotFoundError
from sentinel.kernel.service_state import ServiceState


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