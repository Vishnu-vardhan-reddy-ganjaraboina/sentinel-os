from __future__ import annotations

import pytest

from sentinel.control import ControlProtocolError
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.transport import ControlPlaneProtocol


def create_context() -> ControlContext:
    return ControlContext(
        caller_id="test-user",
        caller_type="cli",
        metadata={"source": "test"},
    )


def create_request() -> ControlRequest:
    return ControlRequest(
        command=KernelCommand.SERVICE_STATUS,
        context=create_context(),
        data={"service": "memory"},
    )


def create_result() -> ControlResult:
    return ControlResult(
        success=True,
        command=KernelCommand.SERVICE_STATUS.value,
        data={"service": "memory"},
    )


def test_encode_request_returns_newline_delimited_json() -> None:
    request = create_request()

    encoded = ControlPlaneProtocol.encode_request(request)

    assert encoded.endswith(b"\n")
    assert b'"version":1' in encoded
    assert b'"type":"request"' in encoded
    assert b'"command":"service.status"' in encoded


def test_decode_request_round_trips() -> None:
    request = create_request()

    encoded = ControlPlaneProtocol.encode_request(request)
    decoded = ControlPlaneProtocol.decode_request(encoded)

    assert decoded == request


def test_decode_request_accepts_string() -> None:
    request = create_request()

    encoded = ControlPlaneProtocol.encode_request(request).decode()
    decoded = ControlPlaneProtocol.decode_request(encoded)

    assert decoded == request


def test_encode_response_returns_newline_delimited_json() -> None:
    result = create_result()

    encoded = ControlPlaneProtocol.encode_response(result)

    assert encoded.endswith(b"\n")
    assert b'"version":1' in encoded
    assert b'"type":"response"' in encoded
    assert b'"success":true' in encoded


def test_decode_response_round_trips() -> None:
    result = create_result()

    encoded = ControlPlaneProtocol.encode_response(result)
    decoded = ControlPlaneProtocol.decode_response(encoded)

    assert decoded == result


def test_decode_response_accepts_string() -> None:
    result = create_result()

    encoded = ControlPlaneProtocol.encode_response(result).decode()
    decoded = ControlPlaneProtocol.decode_response(encoded)

    assert decoded == result


@pytest.mark.parametrize(
    "message",
    [
        b"",
        b"not json",
        b"[]",
        b"{}",
        (
            b'{"version":999,"type":"request",'
            b'"command":"service.list","context":{},"data":{}}'
        ),
        (
            b'{"version":1,"type":"response",'
            b'"success":"yes","data":{}}'
        ),
        (
            b'{"version":1,"type":"request",'
            b'"command":"invalid","context":{},"data":{}}'
        ),
    ],
)
def test_decode_rejects_invalid_messages(
    message: bytes,
) -> None:
    with pytest.raises(ControlProtocolError):
        if b'"type":"response"' in message:
            ControlPlaneProtocol.decode_response(message)
        else:
            ControlPlaneProtocol.decode_request(message)


def test_decode_request_rejects_missing_context() -> None:
    message = (
        b'{"version":1,"type":"request",'
        b'"command":"service.list","data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="context",
    ):
        ControlPlaneProtocol.decode_request(message)


def test_decode_request_rejects_invalid_context() -> None:
    message = (
        b'{"version":1,"type":"request",'
        b'"command":"service.list",'
        b'"context":"invalid","data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="context",
    ):
        ControlPlaneProtocol.decode_request(message)


def test_decode_request_rejects_non_mapping_data() -> None:
    message = (
        b'{"version":1,"type":"request",'
        b'"command":"service.status",'
        b'"context":{"caller_id":"user","caller_type":"cli"},'
        b'"data":[]}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="dictionary",
    ):
        ControlPlaneProtocol.decode_request(message)


def test_decode_response_rejects_non_boolean_success() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":"yes","command":"service.list",'
        b'"data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="boolean",
    ):
        ControlPlaneProtocol.decode_response(message)


def test_decode_response_rejects_non_mapping_data() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":true,"command":"service.list",'
        b'"data":[]}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="dictionary",
    ):
        ControlPlaneProtocol.decode_response(message)


def test_decode_response_rejects_failure_without_error() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":false,"command":"service.list",'
        b'"data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="error",
    ):
        ControlPlaneProtocol.decode_response(message)


def test_decode_response_rejects_success_with_error() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":true,"command":"service.list",'
        b'"data":{},"error":"unexpected"}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="error",
    ):
        ControlPlaneProtocol.decode_response(message)


def test_request_data_is_isolated() -> None:
    request = create_request()

    encoded = ControlPlaneProtocol.encode_request(request)
    decoded = ControlPlaneProtocol.decode_request(encoded)

    decoded.data["service"] = "execution"

    assert request.data["service"] == "memory"


def test_protocol_commands_are_serialized_by_value() -> None:
    for command in KernelCommand:
        context = create_context()

        request = ControlRequest(
            command=command,
            context=context,
            data=(
                {"service": "memory"}
                if command
                in {
                    KernelCommand.SERVICE_STATUS,
                    KernelCommand.SERVICE_START,
                    KernelCommand.SERVICE_STOP,
                    KernelCommand.SERVICE_RESTART,
                }
                else {}
            ),
        )

        encoded = ControlPlaneProtocol.encode_request(request)

        assert command.value.encode() in encoded