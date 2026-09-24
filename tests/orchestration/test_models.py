from sentinel.brain.intent import Intent
from sentinel.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)


def test_request() -> None:
    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={"user": "Sentinel"},
    )

    assert request.id == "req.1"
    assert request.input == "hello"
    assert request.context == {"user": "Sentinel"}
    assert request.intent is None


def test_request_default_context() -> None:
    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert request.context == {}
    assert request.intent is None


def test_request_with_intent() -> None:
    intent = Intent(
        name="open_application",
        input="Open Chrome",
        capability_id="system.open_application",
        arguments={
            "application": "chrome",
        },
        context={
            "source": "user",
        },
    )

    request = OrchestrationRequest(
        request_id="req.1",
        input="Open Chrome",
        intent=intent,
    )

    assert request.intent is not None
    assert request.intent.name == "open_application"
    assert request.intent.input == "Open Chrome"
    assert request.intent.capability_id == "system.open_application"
    assert request.intent.arguments == {
        "application": "chrome",
    }
    assert request.intent.context == {
        "source": "user",
    }


def test_request_rejects_invalid_intent() -> None:
    import pytest

    with pytest.raises(
        TypeError,
        match="intent must be an Intent instance or None",
    ):
        OrchestrationRequest(
            request_id="req.1",
            input="hello",
            intent="invalid",  # type: ignore[arg-type]
        )


def test_request_intent_is_isolated() -> None:
    intent = Intent(
        name="open_application",
        input="Open Chrome",
        arguments={
            "application": "chrome",
        },
    )

    request = OrchestrationRequest(
        request_id="req.1",
        input="Open Chrome",
        intent=intent,
    )

    returned = request.intent

    assert returned is not None

    returned_arguments = dict(returned.arguments)
    returned_arguments["application"] = "firefox"

    assert request.intent is not None
    assert request.intent.arguments["application"] == "chrome"


def test_result() -> None:
    result = OrchestrationResult(
        request_id="req.1",
        success=True,
        data="completed",
    )

    assert result.request_id == "req.1"
    assert result.success is True
    assert result.data == "completed"
    assert result.error is None


def test_result_error() -> None:
    result = OrchestrationResult(
        request_id="req.1",
        success=False,
        error="Not authorized.",
    )

    assert result.success is False
    assert result.error == "Not authorized."


def test_result_to_dict() -> None:
    result = OrchestrationResult(
        request_id="req.1",
        success=True,
        data={"value": 42},
    )

    assert result.to_dict() == {
        "request_id": "req.1",
        "success": True,
        "data": {"value": 42},
        "error": None,
    }


def test_request_context_isolated() -> None:
    context = {
        "user": "Sentinel",
        "nested": {
            "value": 1,
        },
    }

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context=context,
    )

    context["user"] = "changed"
    context["nested"]["value"] = 2

    assert request.context["user"] == "Sentinel"
    assert request.context["nested"]["value"] == 1


def test_request_context_property_returns_copy() -> None:
    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={
            "user": "Sentinel",
        },
    )

    returned = request.context
    returned["user"] = "changed"

    assert request.context["user"] == "Sentinel"


def test_result_to_dict_is_isolated() -> None:
    data = {
        "nested": {
            "value": 1,
        },
    }

    result = OrchestrationResult(
        request_id="req.1",
        success=True,
        data=data,
    )

    serialized = result.to_dict()

    serialized["data"]["nested"]["value"] = 99

    assert result.data["nested"]["value"] == 1