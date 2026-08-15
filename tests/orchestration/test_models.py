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


def test_request_default_context() -> None:
    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert request.context == {}


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