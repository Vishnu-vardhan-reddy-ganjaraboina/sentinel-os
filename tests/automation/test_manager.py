import pytest

from sentinel.automation.exceptions import (
    WorkflowExecutionError,
)
from sentinel.automation.manager import WorkflowManager
from sentinel.automation.workflow import BaseWorkflow


class EchoWorkflow(BaseWorkflow):

    def __init__(self):
        super().__init__(
            workflow_id="echo.workflow",
            name="Echo Workflow",
        )

    def run(self, **kwargs):
        return kwargs


class FailingWorkflow(BaseWorkflow):

    def __init__(self):
        super().__init__(
            workflow_id="fail.workflow",
            name="Fail Workflow",
        )

    def run(self, **kwargs):
        raise RuntimeError("boom")


def test_register():
    manager = WorkflowManager()
    workflow = EchoWorkflow()

    manager.register(workflow)

    assert manager.exists(workflow.id)


def test_execute():
    manager = WorkflowManager()
    workflow = EchoWorkflow()

    manager.register(workflow)

    result = manager.execute(
        workflow.id,
        value=100,
    )

    assert result["value"] == 100


def test_execute_failure():
    manager = WorkflowManager()
    workflow = FailingWorkflow()

    manager.register(workflow)

    with pytest.raises(WorkflowExecutionError):
        manager.execute(workflow.id)


def test_enable_disable():
    manager = WorkflowManager()
    workflow = EchoWorkflow()

    manager.register(workflow)

    manager.disable(workflow.id)
    assert not workflow.enabled

    manager.enable(workflow.id)
    assert workflow.enabled


def test_unregister():
    manager = WorkflowManager()
    workflow = EchoWorkflow()

    manager.register(workflow)
    manager.unregister(workflow.id)

    assert not manager.exists(workflow.id)


def test_list():
    manager = WorkflowManager()

    manager.register(EchoWorkflow())

    assert len(manager.list()) == 1


def test_clear():
    manager = WorkflowManager()

    manager.register(EchoWorkflow())
    manager.clear()

    assert len(manager.list()) == 0