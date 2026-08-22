from sentinel.brain.context import BrainContext


def test_properties():
    context = BrainContext("ctx.1")

    assert context.id == "ctx.1"
    assert context.data == {}


def test_update():
    context = BrainContext("ctx.1")

    context.update(user="sentinel")

    assert context.get("user") == "sentinel"


def test_default():
    context = BrainContext("ctx.1")

    assert context.get("missing") is None
    assert context.get("missing", 100) == 100


def test_clear():
    context = BrainContext("ctx.1")

    context.update(a=1, b=2)

    context.clear()

    assert context.data == {}


def test_to_dict():
    context = BrainContext("ctx.1")

    context.update(user="AI")

    data = context.to_dict()

    assert data["id"] == "ctx.1"
    assert data["data"]["user"] == "AI"


def test_initial_data():
    context = BrainContext(
        "ctx.1",
        {"name": "Sentinel"},
    )

    assert context.get("name") == "Sentinel"


def test_empty_id():
    import pytest

    with pytest.raises(ValueError):
        BrainContext("")

def test_nested_data_is_isolated() -> None:
    context = BrainContext("ctx.1")

    context.update(
        profile={
            "name": "Sentinel",
        }
    )

    data = context.data
    data["profile"]["name"] = "changed"

    assert context.get("profile")["name"] == "Sentinel"