import pytest

from sentinel.application import Application
from sentinel.runtime import Runtime


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

    assert kernel.get("execution") is not None
    assert kernel.running("execution") is True

    application.shutdown()

    assert application.running is False
    assert kernel.running("execution") is False

def test_orchestration_service_is_registered() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.get("orchestration") is not None
    assert kernel.running("orchestration") is True

    application.shutdown()


def test_orchestration_service_stops_on_shutdown() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.running("orchestration") is True

    application.shutdown()

    assert application.running is False
    assert kernel.running("orchestration") is False

def test_memory_service_is_registered() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.get("memory") is not None
    assert kernel.running("memory") is True

    application.shutdown()


def test_memory_service_stops_on_shutdown() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.running("memory") is True

    application.shutdown()

    assert application.running is False
    assert kernel.running("memory") is False

def test_knowledge_service_is_registered() -> None:
    application = Application()

    kernel = application.start()

    knowledge = kernel.get("knowledge")

    assert knowledge is not None
    assert kernel.running("knowledge") is True

    application.shutdown()


def test_knowledge_service_stops_on_shutdown() -> None:
    application = Application()

    kernel = application.start()

    assert kernel.running("knowledge") is True

    application.shutdown()

    assert application.running is False
    assert kernel.running("knowledge") is False

def test_start_failure_leaves_application_stopped() -> None:
    from sentinel.kernel.bootstrap import Bootstrap
    from sentinel.kernel.service import Service

    class FailingService(Service):
        def __init__(self) -> None:
            super().__init__("failing")

        def initialize(self) -> None:
            raise RuntimeError("startup failed")

        def shutdown(self) -> None:
            pass

    application = Application(
        bootstrap=Bootstrap(
            services=(FailingService(),)
        )
    )

    with pytest.raises(
        RuntimeError,
        match="startup failed",
    ):
        application.start()

    assert application.running is False


def test_failed_start_can_be_retried() -> None:
    from sentinel.kernel.bootstrap import Bootstrap
    from sentinel.kernel.service import Service

    class FailingService(Service):
        def __init__(self) -> None:
            super().__init__("failing")

        def initialize(self) -> None:
            raise RuntimeError("startup failed")

        def shutdown(self) -> None:
            pass

    application = Application(
        bootstrap=Bootstrap(
            services=(FailingService(),)
        )
    )

    with pytest.raises(RuntimeError):
        application.start()

    assert application.running is False

    with pytest.raises(RuntimeError):
        application.start()

from sentinel.runtime import Runtime


def test_application_exposes_runtime() -> None:
    application = Application()

    runtime = application.runtime

    assert isinstance(runtime, Runtime)
    assert len(runtime) == 4


def test_application_runtime_contains_core_services() -> None:
    application = Application()

    runtime = application.runtime

    assert runtime.get("execution") is not None
    assert runtime.get("orchestration") is not None
    assert runtime.get("memory") is not None
    assert runtime.get("knowledge") is not None

def test_application_knowledge_uses_runtime() -> None:
    application = Application()

    knowledge = application.knowledge

    assert knowledge is application.runtime.get(
        "knowledge"
    ).knowledge


def test_external_bootstrap_has_no_runtime() -> None:
    from sentinel.kernel.bootstrap import Bootstrap

    application = Application(
        bootstrap=Bootstrap(),
    )

    with pytest.raises(
        RuntimeError,
        match="Runtime is not available",
    ):
        application.runtime

def test_application_runtime_services_match_kernel_services() -> None:
    application = Application()
    kernel = application.start()

    assert application.runtime.execution is kernel.get("execution")
    assert application.runtime.orchestration is kernel.get("orchestration")
    assert application.runtime.memory is kernel.get("memory")
    assert application.runtime.knowledge is kernel.get("knowledge")

    application.shutdown()


def test_application_runtime_services_are_running() -> None:
    application = Application()
    application.start()

    assert application.runtime.execution.health()["healthy"] is True
    assert application.runtime.orchestration.health()["healthy"] is True
    assert application.runtime.memory.health()["healthy"] is True
    assert application.runtime.knowledge.health()["healthy"] is True

    application.shutdown()

def test_application_exposes_execution_runtime() -> None:
    application = Application()

    assert application.execution is application.runtime.execution


def test_application_exposes_orchestration_runtime() -> None:
    application = Application()

    assert application.orchestration is application.runtime.orchestration


def test_application_exposes_memory_runtime() -> None:
    application = Application()

    assert application.memory is application.runtime.memory


def test_application_exposes_knowledge_runtime() -> None:
    application = Application()

    assert application.knowledge_runtime is application.runtime.knowledge