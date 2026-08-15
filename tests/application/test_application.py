import pytest

from sentinel.application import Application


def test_initial_state() -> None:
    application = Application()

    assert application.running is False


def test_start() -> None:
    application = Application()

    kernel = application.start()

    assert application.running is True
    assert application.kernel is kernel

    application.shutdown()


def test_double_start_raises() -> None:
    application = Application()

    application.start()

    with pytest.raises(RuntimeError):
        application.start()

    application.shutdown()


def test_shutdown() -> None:
    application = Application()

    application.start()
    application.shutdown()

    assert application.running is False


def test_shutdown_without_start_raises() -> None:
    application = Application()

    with pytest.raises(RuntimeError):
        application.shutdown()


def test_context_manager() -> None:
    with Application() as application:
        assert application.running is True

    assert application.running is False

def test_execution_service_is_registered() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.get("execution") is not None
    assert kernel.running("execution") is True

    application.shutdown()

def test_execution_service_stops_on_shutdown() -> None:
    application = Application()

    kernel = application.start()

    execution = kernel.get("execution")

    assert kernel.running("execution") is True

    application.shutdown()

    assert application.running is False
    assert kernel.running("execution") is False