import pytest

from sentinel.brain.interfaces import (
    Context,
    Planner,
    Engine,
)


class DummyContext(Context):

    def __init__(self):
        self._data = {}

    @property
    def id(self):
        return "context.1"

    @property
    def data(self):
        return self._data

    def update(self, **kwargs):
        self._data.update(kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "data": self.data.copy(),
        }


class DummyPlanner(Planner):

    def create_plan(self, request, context):
        return {
            "request": request,
            "context": context.id,
        }


class DummyEngine(Engine):

    def execute(self, request, context):
        return {
            "status": "completed",
            "request": request,
            "context": context.id,
        }


def test_context():
    context = DummyContext()

    context.update(user="sentinel")

    assert context.id == "context.1"
    assert context.data["user"] == "sentinel"

    d = context.to_dict()
    assert d["id"] == "context.1"
    assert d["data"]["user"] == "sentinel"


def test_planner():
    planner = DummyPlanner()
    context = DummyContext()

    plan = planner.create_plan(
        "hello",
        context,
    )

    assert plan["request"] == "hello"
    assert plan["context"] == "context.1"


def test_engine():
    engine = DummyEngine()
    context = DummyContext()

    result = engine.execute(
        "hello",
        context,
    )

    assert result["status"] == "completed"


def test_context_is_abstract():
    with pytest.raises(TypeError):
        Context()


def test_planner_is_abstract():
    with pytest.raises(TypeError):
        Planner()


def test_engine_is_abstract():
    with pytest.raises(TypeError):
        Engine()