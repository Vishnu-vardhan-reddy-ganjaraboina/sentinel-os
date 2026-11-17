from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.isolated import IsolatedCapability
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.execution.isolated_worker import IsolatedWorker


def test_isolated_capability_executes_in_worker_process():
    capability = IsolatedCapability(
        CapabilityMetadata(
            capability_id="isolated-add",
            name="Isolated Add",
            description="Adds two values in a worker.",
            category=CapabilityCategory.CUSTOM,
        ),
        worker=IsolatedWorker(
            allowed_modules={"tests.execution.worker_fixtures"},
        ),
        callable_ref="tests.execution.worker_fixtures:add",
    )
    assert capability.execute(a=20, b=22) == 42
