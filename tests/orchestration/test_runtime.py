from sentinel.kernel.service import Service
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.orchestration.service import OrchestrationService


def test_runtime_is_kernel_service() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(runtime, Service)
    assert runtime.name == "orchestration"


def test_runtime_orchestration_property() -> None:
    orchestration = OrchestrationService()

    runtime = OrchestrationRuntimeService(
        orchestration=orchestration,
    )

    assert runtime.orchestration is orchestration


def test_runtime_default_service() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(
        runtime.orchestration,
        OrchestrationService,
    )


def test_runtime_initialize() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_shutdown() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": True,
    }