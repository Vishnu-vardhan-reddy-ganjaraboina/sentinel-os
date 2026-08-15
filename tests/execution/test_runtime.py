from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.execution.service import ExecutionService


def test_runtime_service() -> None:
    execution = ExecutionService()
    runtime = ExecutionRuntimeService(execution)

    assert runtime.name == "execution"
    assert runtime.execution is execution
    assert runtime.dependencies == ()

    runtime.initialize()
    runtime.shutdown()


def test_runtime_health() -> None:
    runtime = ExecutionRuntimeService()

    assert runtime.health() == {
        "healthy": True,
    }

    runtime.shutdown()