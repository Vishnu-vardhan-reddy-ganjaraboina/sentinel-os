import pytest

from sentinel.automation.interfaces import Trigger, Workflow


class DummyTrigger(Trigger):

    def __init__(self):
        self._enabled = True

    @property
    def id(self):
        return "dummy.trigger"

    @property
    def enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def evaluate(self, **kwargs):
        return kwargs.get("fire", False)


class DummyWorkflow(Workflow):

    def __init__(self):
        self._enabled = True

    @property
    def id(self):
        return "dummy.workflow"

    @property
    def name(self):
        return "Dummy Workflow"

    @property
    def enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def execute(self, **kwargs):
        return kwargs


def test_trigger():
    trigger = DummyTrigger()

    assert trigger.id == "dummy.trigger"
    assert trigger.evaluate(fire=True) is True


def test_trigger_enable_disable():
    trigger = DummyTrigger()

    trigger.disable()
    assert trigger.enabled is False

    trigger.enable()
    assert trigger.enabled is True


def test_workflow():
    workflow = DummyWorkflow()

    result = workflow.execute(value=123)

    assert workflow.id == "dummy.workflow"
    assert workflow.name == "Dummy Workflow"
    assert result["value"] == 123


def test_workflow_enable_disable():
    workflow = DummyWorkflow()

    workflow.disable()
    assert workflow.enabled is False

    workflow.enable()
    assert workflow.enabled is True


def test_trigger_is_abstract():
    with pytest.raises(TypeError):
        Trigger()


def test_workflow_is_abstract():
    with pytest.raises(TypeError):
        Workflow()