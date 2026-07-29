import pytest

from sentinel.automation.exceptions import WorkflowExecutionError
from sentinel.automation.service import AutomationService
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
    service = AutomationService()
    workflow = EchoWorkflow()

    service.register(workflow)

    assert service.exists(workflow.id)


def test_execute():
    service = AutomationService()
    workflow = EchoWorkflow()

    service.register(workflow)

    result = service.execute(
        workflow.id,
        value=123,
    )

    assert result["value"] == 123


def test_execute_failure():
    service = AutomationService()
    workflow = FailingWorkflow()

    service.register(workflow)

    with pytest.raises(WorkflowExecutionError):
        service.execute(workflow.id)


def test_enable_disable():
    service = AutomationService()
    workflow = EchoWorkflow()

    service.register(workflow)

    service.disable(workflow.id)
    assert not workflow.enabled

    service.enable(workflow.id)
    assert workflow.enabled


def test_unregister():
    service = AutomationService()
    workflow = EchoWorkflow()

    service.register(workflow)
    service.unregister(workflow.id)

    assert not service.exists(workflow.id)


def test_list():
    service = AutomationService()

    service.register(EchoWorkflow())

    assert len(service.list()) == 1


def test_clear():
    service = AutomationService()

    service.register(EchoWorkflow())
    service.clear()

    assert len(service.list()) == 0


def test_get():
    service = AutomationService()
    workflow = EchoWorkflow()

    service.register(workflow)

    assert service.get(workflow.id) is workflow