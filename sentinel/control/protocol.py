"""
Protocol definitions for Sentinel local control.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from sentinel.control.exceptions import ControlProtocolError


class ControlCommand(str, Enum):
    """Commands supported by the Sentinel local control plane."""

    STATUS = "status"
    HEALTH = "health"
    STOP = "stop"


class ControlProtocol:
    """
    Encode and decode local Sentinel control messages.

    Messages are JSON objects terminated by a newline. The protocol is
    intentionally small and explicit so it can be hardened before being
    exposed through the local TCP control server.
    """

    VERSION = 1

    @staticmethod
    def encode_request(
        command: ControlCommand,
        data: dict[str, Any] | None = None,
    ) -> bytes:
        """Encode a control request."""
        if not isinstance(command, ControlCommand):
            raise TypeError(
                "command must be a ControlCommand."
            )

        if data is not None and not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary or None."
            )

        payload: dict[str, Any] = {
            "version": ControlProtocol.VERSION,
            "type": "request",
            "command": command.value,
            "data": dict(data) if data is not None else {},
        }

        return (
            json.dumps(
                payload,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )

    @staticmethod
    def decode_request(
        message: bytes | str,
    ) -> tuple[ControlCommand, dict[str, Any]]:
        """Decode and validate a control request."""
        payload = ControlProtocol._decode_json(message)

        if payload.get("version") != ControlProtocol.VERSION:
            raise ControlProtocolError(
                "Unsupported control protocol version."
            )

        if payload.get("type") != "request":
            raise ControlProtocolError(
                "Control message must be a request."
            )

        command_value = payload.get("command")

        try:
            command = ControlCommand(command_value)
        except (TypeError, ValueError) as exc:
            raise ControlProtocolError(
                f"Unsupported control command: {command_value!r}."
            ) from exc

        data = payload.get("data", {})

        if not isinstance(data, dict):
            raise ControlProtocolError(
                "Request data must be a dictionary."
            )

        return command, dict(data)

    @staticmethod
    def encode_response(
        success: bool,
        *,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> bytes:
        """Encode a control response."""
        if not isinstance(success, bool):
            raise TypeError(
                "success must be a boolean."
            )

        if data is not None and not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary or None."
            )

        if error is not None and not isinstance(error, str):
            raise TypeError(
                "error must be a string or None."
            )

        if success and error is not None:
            raise ValueError(
                "Successful responses cannot contain an error."
            )

        if not success and not error:
            raise ValueError(
                "Failed responses must contain an error."
            )

        payload: dict[str, Any] = {
            "version": ControlProtocol.VERSION,
            "type": "response",
            "success": success,
            "data": dict(data) if data is not None else {},
        }

        if error is not None:
            payload["error"] = error

        return (
            json.dumps(
                payload,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )

    @staticmethod
    def decode_response(
        message: bytes | str,
    ) -> tuple[bool, dict[str, Any], str | None]:
        """Decode and validate a control response."""
        payload = ControlProtocol._decode_json(message)

        if payload.get("version") != ControlProtocol.VERSION:
            raise ControlProtocolError(
                "Unsupported control protocol version."
            )

        if payload.get("type") != "response":
            raise ControlProtocolError(
                "Control message must be a response."
            )

        success = payload.get("success")

        if not isinstance(success, bool):
            raise ControlProtocolError(
                "Response success must be a boolean."
            )

        data = payload.get("data", {})

        if not isinstance(data, dict):
            raise ControlProtocolError(
                "Response data must be a dictionary."
            )

        error = payload.get("error")

        if error is not None and not isinstance(error, str):
            raise ControlProtocolError(
                "Response error must be a string or None."
            )

        if success and error is not None:
            raise ControlProtocolError(
                "Successful responses cannot contain an error."
            )

        if not success and not error:
            raise ControlProtocolError(
                "Failed responses must contain an error."
            )

        return success, dict(data), error

    @staticmethod
    def _decode_json(
        message: bytes | str,
    ) -> dict[str, Any]:
        """Decode a JSON control message."""
        if isinstance(message, bytes):
            try:
                text = message.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ControlProtocolError(
                    "Control message is not valid UTF-8."
                ) from exc
        elif isinstance(message, str):
            text = message
        else:
            raise TypeError(
                "message must be bytes or string."
            )

        text = text.strip()

        if not text:
            raise ControlProtocolError(
                "Control message cannot be empty."
            )

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ControlProtocolError(
                "Control message is not valid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise ControlProtocolError(
                "Control message must be a JSON object."
            )

        return payload
