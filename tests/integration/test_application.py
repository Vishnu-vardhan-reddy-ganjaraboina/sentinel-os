from sentinel.application import Application


def test_application_starts_all_core_runtime_services() -> None:
    application = Application()

    kernel = application.start()

    assert application.running is True

    assert kernel.get("execution") is not None
    assert kernel.get("orchestration") is not None
    assert kernel.get("memory") is not None

    assert kernel.running("execution") is True
    assert kernel.running("orchestration") is True
    assert kernel.running("memory") is True

    application.shutdown()


def test_application_stops_all_core_runtime_services() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.running("execution") is True
    assert kernel.running("orchestration") is True
    assert kernel.running("memory") is True

    application.shutdown()

    assert application.running is False

    assert kernel.running("execution") is False
    assert kernel.running("orchestration") is False
    assert kernel.running("memory") is False


def test_application_context_manager() -> None:
    with Application() as application:
        assert application.running is True

        kernel = application.kernel

        assert kernel.running("execution") is True
        assert kernel.running("orchestration") is True
        assert kernel.running("memory") is True

    assert application.running is False
