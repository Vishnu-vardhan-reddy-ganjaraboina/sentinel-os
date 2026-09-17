from __future__ import annotations

import pytest

from sentinel.control import (
    ControlCommand,
    ControlProtocol,
    ControlProtocolError,
)


def test_encode_request() -> None:
    message = ControlProtocol.encode_request(
        ControlCommand.STATUS,
    )

    assert message.endswith(b"\n")

    command, data = ControlProtocol.decode_request(message)

    assert command is ControlCommand.STATUS
    assert data == {}


def test_encode_request_with_data() -> None:
    message = ControlProtocol.encode_request(
        ControlCommand.HEALTH,
        {"detail": True},
    )

    command, data = ControlProtocol.decode_request(message)

    assert command is ControlCommand.HEALTH
    assert data == {"detail": True}


def test_decode_request_accepts_string() -> None:
    message = ControlProtocol.encode_request(
        ControlCommand.STOP,
    ).decode()

    command, data = ControlProtocol.decode_request(message)

    assert command is ControlCommand.STOP
    assert data == {}


def test_encode_response_success() -> None:
    message = ControlProtocol.encode_response(
        True,
        data={"state": "running"},
    )

    success, data, error = ControlProtocol.decode_response(message)

    assert success is True
    assert data == {"state": "running"}
    assert error is None


def test_encode_response_failure() -> None:
    message = ControlProtocol.encode_response(
        False,
        error="Sentinel is not running.",
    )

    success, data, error = ControlProtocol.decode_response(message)

    assert success is False
    assert data == {}
    assert error == "Sentinel is not running."


@pytest.mark.parametrize(
    "command",
    [object(), "status", None],
)
def test_encode_request_rejects_invalid_command(
    command: object,
) -> None:
    with pytest.raises(TypeError):
        ControlProtocol.encode_request(
            command,  # type: ignore[arg-type]
        )


def test_success_response_cannot_have_error() -> None:
    with pytest.raises(ValueError):
        ControlProtocol.encode_response(
            True,
            error="unexpected",
        )


def test_failed_response_requires_error() -> None:
    with pytest.raises(ValueError):
        ControlProtocol.encode_response(False)


@pytest.mark.parametrize(
    "message",
    [
        b"",
        b"not json",
        b"[]",
        b"{}",
        b'{"version":999,"type":"request","command":"status"}',
        b'{"version":1,"type":"response","success":"yes"}',
        b'{"version":1,"type":"request","command":"invalid"}',
    ],
)
def test_decode_rejects_invalid_messages(
    message: bytes,
) -> None:
    with pytest.raises(ControlProtocolError):
        if b'"type":"response"' in message:
            ControlProtocol.decode_response(message)
        else:
            ControlProtocol.decode_request(message)


def test_decode_request_rejects_non_mapping_data() -> None:
    message = (
        b'{"version":1,"type":"request",'
        b'"command":"status","data":[]}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="dictionary",
    ):
        ControlProtocol.decode_request(message)


def test_decode_response_rejects_non_boolean_success() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":"yes","data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="boolean",
    ):
        ControlProtocol.decode_response(message)


def test_decode_response_rejects_failure_without_error() -> None:
    message = (
        b'{"version":1,"type":"response",'
        b'"success":false,"data":{}}\n'
    )

    with pytest.raises(
        ControlProtocolError,
        match="error",
    ):
        ControlProtocol.decode_response(message)


def test_request_data_is_isolated() -> None:
    source = {"nested": {"value": 1}}

    message = ControlProtocol.encode_request(
        ControlCommand.STATUS,
        source,
    )

    source["nested"]["value"] = 999

    _, data = ControlProtocol.decode_request(message)

    assert data["nested"]["value"] == 1


def test_protocol_commands() -> None:
    assert list(ControlCommand) == [
        ControlCommand.STATUS,
        ControlCommand.HEALTH,
        ControlCommand.STOP,
    ]
