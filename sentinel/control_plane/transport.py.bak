"""
JSON transport protocol for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

import json
from typing import Any

from sentinel.control.exceptions import ControlProtocolError
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult


class ControlPlaneProtocol:
    """
    Encode and decode Kernel Control Plane messages.

    Messages are JSON objects terminated by a newline. The protocol
    transports structured ControlRequest and ControlResult objects but
    does not perform authorization or command execution.
    """

    VERSION = 1

    @staticmethod
    def encode_request(
        request: ControlRequest,
    ) -> bytes:
        """Encode a ControlRequest as a newline-delimited JSON message."""
        if not isinstance(request, ControlRequest):
            raise TypeError(
                "request must be a ControlRequest."
            )

        context = request.context

        payload: dict[str, Any] = {
            "version": ControlPlaneProtocol.VERSION,
            "type": "request",
            "command": request.command.value,
            "context": {
                "caller_id": context.caller_id,
                "caller_type": (
                    context.caller_type.value
                    if hasattr(context.caller_type, "value")
                    else context.caller_type
                ),
                "metadata": dict(context.metadata),
            },
            "data": dict(request.data),
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
    ) -> ControlRequest:
        """Decode and validate a ControlRequest message."""
        payload = ControlPlaneProtocol._decode_json(message)

        if payload.get("version") != ControlPlaneProtocol.VERSION:
            raise ControlProtocolError(
                "Unsupported control protocol version."
            )

        if payload.get("type") != "request":
            raise ControlProtocolError(
                "Control message must be a request."
            )

        command_value = payload.get("command")

        try:
            command = KernelCommand(command_value)
        except (TypeError, ValueError) as exc:
            raise ControlProtocolError(
                f"Unsupported control command: {command_value!r}."
            ) from exc

        context_data = payload.get("context")

        if not isinstance(context_data, dict):
            raise ControlProtocolError(
                "Request context must be a dictionary."
            )

        caller_id = context_data.get("caller_id")
        caller_type = context_data.get("caller_type")
        metadata = context_data.get("metadata", {})

        if not isinstance(caller_id, str):
            raise ControlProtocolError(
                "Request context caller_id must be a string."
            )

        if not isinstance(caller_type, str):
            raise ControlProtocolError(
                "Request context caller_type must be a string."
            )

        if not isinstance(metadata, dict):
            raise ControlProtocolError(
                "Request context metadata must be a dictionary."
            )

        data = payload.get("data", {})

        if not isinstance(data, dict):
            raise ControlProtocolError(
                "Request data must be a dictionary."
            )

        try:
            context = ControlContext(
                caller_id=caller_id,
                caller_type=caller_type,
                metadata=metadata,
            )

            return ControlRequest(
                command=command,
                context=context,
                data=data,
            )
        except (TypeError, ValueError) as exc:
            raise ControlProtocolError(
                f"Invalid control request: {exc}"
            ) from exc

    @staticmethod
    def encode_response(
        result: ControlResult,
    ) -> bytes:
        """Encode a ControlResult as a newline-delimited JSON message."""
        if not isinstance(result, ControlResult):
            raise TypeError(
                "result must be a ControlResult."
            )

        payload: dict[str, Any] = {
            "version": ControlPlaneProtocol.VERSION,
            "type": "response",
            "success": result.success,
            "command": result.command,
            "data": dict(result.data),
        }

        if result.error is not None:
            payload["error"] = result.error

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
    ) -> ControlResult:
        """Decode and validate a ControlResult message."""
        payload = ControlPlaneProtocol._decode_json(message)

        if payload.get("version") != ControlPlaneProtocol.VERSION:
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

        command = payload.get("command")

        if not isinstance(command, str):
            raise ControlProtocolError(
                "Response command must be a string."
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

        return ControlResult(
            success=success,
            command=command,
            data=data,
            error=error,
        )

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