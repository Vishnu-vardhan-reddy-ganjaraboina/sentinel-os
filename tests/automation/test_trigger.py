import pytest

from sentinel.automation.trigger import BaseTrigger


class DummyTrigger(BaseTrigger):

    def __init__(self):
        super().__init__("dummy.trigger")

    def check(self, **kwargs):
        return kwargs.get("fire", False)


def test_properties():
    trigger = DummyTrigger()

    assert trigger.id == "dummy.trigger"
    assert trigger.enabled is True


def test_evaluate_true():
    trigger = DummyTrigger()

    assert trigger.evaluate(fire=True) is True


def test_evaluate_false():
    trigger = DummyTrigger()

    assert trigger.evaluate(fire=False) is False


def test_disable():
    trigger = DummyTrigger()

    trigger.disable()

    assert trigger.enabled is False
    assert trigger.evaluate(fire=True) is False


def test_enable():
    trigger = DummyTrigger()

    trigger.disable()
    trigger.enable()

    assert trigger.enabled is True


def test_empty_id():

    class InvalidTrigger(BaseTrigger):
        def check(self, **kwargs):
            return True

    with pytest.raises(ValueError):
        InvalidTrigger("")


def test_trigger_is_abstract():
    with pytest.raises(TypeError):
        BaseTrigger("test")