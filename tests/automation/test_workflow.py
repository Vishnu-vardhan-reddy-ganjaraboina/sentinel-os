import pytest

from sentinel.automation.constants import WorkflowStatus
from sentinel.automation.exceptions import (
    WorkflowDisabledError,
)
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


def test_properties():
    workflow = EchoWorkflow()

    assert workflow.id == "echo.workflow"
    assert workflow.name == "Echo Workflow"
    assert workflow.enabled is True
    assert workflow.status == WorkflowStatus.IDLE


def test_execute():
    workflow = EchoWorkflow()

    result = workflow.execute(value=100)

    assert result["value"] == 100
    assert workflow.status == WorkflowStatus.COMPLETED


def test_disable():
    workflow = EchoWorkflow()

    workflow.disable()

    with pytest.raises(WorkflowDisabledError):
        workflow.execute()

    assert workflow.status == WorkflowStatus.DISABLED


def test_failure():
    workflow = FailingWorkflow()

    with pytest.raises(RuntimeError):
        workflow.execute()

    assert workflow.status == WorkflowStatus.FAILED


def test_enable():
    workflow = EchoWorkflow()

    workflow.disable()
    workflow.enable()

    assert workflow.enabled is True


def test_empty_id():

    class InvalidWorkflow(BaseWorkflow):
        def run(self, **kwargs):
            return None

    with pytest.raises(ValueError):
        InvalidWorkflow("", "Test")


def test_empty_name():

    class InvalidWorkflow(BaseWorkflow):
        def run(self, **kwargs):
            return None

    with pytest.raises(ValueError):
        InvalidWorkflow("id", "")


def test_workflow_is_abstract():
    with pytest.raises(TypeError):
        BaseWorkflow("id", "Test")