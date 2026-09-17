"""
Client for the Sentinel local control endpoint.
"""

from __future__ import annotations

import socket
from typing import Any

from sentinel.control.exceptions import ControlConnectionError
from sentinel.control.protocol import ControlCommand, ControlProtocol


class ControlClient:
    """Send commands to a local Sentinel control server."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int,
        timeout: float = 5.0,
    ) -> None:
        if not isinstance(host, str):
            raise TypeError("host must be a string.")

        host = host.strip()

        if host != "127.0.0.1":
            raise ValueError(
                "ControlClient must connect to 127.0.0.1."
            )

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if not 1 <= port <= 65535:
            raise ValueError(
                "port must be between 1 and 65535."
            )

        if not isinstance(timeout, (int, float)):
            raise TypeError(
                "timeout must be a number."
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        self._host = host
        self._port = port
        self._timeout = float(timeout)

    @property
    def host(self) -> str:
        """Return the control host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the control port."""
        return self._port

    @property
    def timeout(self) -> float:
        """Return the connection timeout."""
        return self._timeout

    def request(
        self,
        command: ControlCommand,
        data: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any], str | None]:
        """Send a control request and decode the response."""
        message = ControlProtocol.encode_request(
            command,
            data,
        )

        try:
            with socket.create_connection(
                (self._host, self._port),
                timeout=self._timeout,
            ) as connection:
                connection.settimeout(self._timeout)
                connection.sendall(message)

                response = self._receive_response(connection)

        except OSError as exc:
            raise ControlConnectionError(
                "Unable to connect to Sentinel control endpoint."
            ) from exc

        return ControlProtocol.decode_response(response)

    def status(self) -> tuple[bool, dict[str, Any], str | None]:
        """Request process status."""
        return self.request(ControlCommand.STATUS)

    def health(self) -> tuple[bool, dict[str, Any], str | None]:
        """Request process health."""
        return self.request(ControlCommand.HEALTH)

    def stop(self) -> tuple[bool, dict[str, Any], str | None]:
        """Request process shutdown."""
        return self.request(ControlCommand.STOP)

    @staticmethod
    def _receive_response(
        connection: socket.socket,
    ) -> bytes:
        """Read one newline-delimited response."""
        chunks: list[bytes] = []
        total = 0
        maximum = 64 * 1024

        while True:
            chunk = connection.recv(4096)

            if not chunk:
                break

            chunks.append(chunk)
            total += len(chunk)

            if total > maximum:
                raise ControlConnectionError(
                    "Control response exceeds maximum size."
                )

            if b"\n" in chunk:
                break

        message = b"".join(chunks)

        if b"\n" in message:
            message = message.split(b"\n", 1)[0]

        if not message:
            raise ControlConnectionError(
                "Control endpoint returned an empty response."
            )

        return message

    def __repr__(self) -> str:
        return (
            "ControlClient("
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"timeout={self.timeout}"
            ")"
        )
