import pytest

from sentinel.automation.exceptions import (
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from sentinel.automation.registry import WorkflowRegistry
from sentinel.automation.workflow import BaseWorkflow


class DummyWorkflow(BaseWorkflow):

    def __init__(self, workflow_id="workflow.one"):
        super().__init__(
            workflow_id=workflow_id,
            name="Dummy Workflow",
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    registry = WorkflowRegistry()
    workflow = DummyWorkflow()

    registry.register(workflow)

    assert len(registry) == 1
    assert registry.exists(workflow.id)


def test_duplicate_register():
    registry = WorkflowRegistry()
    workflow = DummyWorkflow()

    registry.register(workflow)

    with pytest.raises(WorkflowAlreadyExistsError):
        registry.register(workflow)


def test_get():
    registry = WorkflowRegistry()
    workflow = DummyWorkflow()

    registry.register(workflow)

    assert registry.get(workflow.id) is workflow


def test_get_not_found():
    registry = WorkflowRegistry()

    with pytest.raises(WorkflowNotFoundError):
        registry.get("missing")


def test_unregister():
    registry = WorkflowRegistry()
    workflow = DummyWorkflow()

    registry.register(workflow)
    registry.unregister(workflow.id)

    assert len(registry) == 0


def test_unregister_not_found():
    registry = WorkflowRegistry()

    with pytest.raises(WorkflowNotFoundError):
        registry.unregister("missing")


def test_list():
    registry = WorkflowRegistry()

    registry.register(DummyWorkflow("one"))
    registry.register(DummyWorkflow("two"))

    assert len(registry.list()) == 2


def test_enabled_disabled_lists():
    registry = WorkflowRegistry()

    enabled = DummyWorkflow("enabled")
    disabled = DummyWorkflow("disabled")
    disabled.disable()

    registry.register(enabled)
    registry.register(disabled)

    assert len(registry.list_enabled()) == 1
    assert len(registry.list_disabled()) == 1


def test_clear():
    registry = WorkflowRegistry()

    registry.register(DummyWorkflow())

    registry.clear()

    assert len(registry) == 0


def test_contains():
    registry = WorkflowRegistry()
    workflow = DummyWorkflow()

    registry.register(workflow)

    assert workflow.id in registry


def test_iteration():
    registry = WorkflowRegistry()

    registry.register(DummyWorkflow("one"))
    registry.register(DummyWorkflow("two"))

    ids = {workflow.id for workflow in registry}

    assert ids == {"one", "two"}