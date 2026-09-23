"""
TCP client for the Sentinel Kernel Control Plane transport.
"""

from __future__ import annotations

import socket

from sentinel.control.exceptions import ControlConnectionError, ControlProtocolError
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.transport import ControlPlaneProtocol


class ControlPlaneTransportClient:
    """
    Client for the Sentinel Kernel Control Plane TCP transport.

    The client is responsible only for:
    - connecting to the transport endpoint
    - encoding ControlRequest messages
    - sending requests
    - receiving responses
    - decoding ControlResult messages

    Authorization and Kernel operations remain server-side.
    """

    MAX_RESPONSE_SIZE = 64 * 1024

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        timeout: float = 5.0,
    ) -> None:
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must not be empty.")

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if port < 1 or port > 65535:
            raise ValueError("port must be between 1 and 65535.")

        if not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a number.")

        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        self._host = host
        self._port = port
        self._timeout = float(timeout)

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def timeout(self) -> float:
        return self._timeout

    def execute(self, request: ControlRequest) -> ControlResult:
        """
        Send a ControlRequest and return the ControlResult.
        """
        if not isinstance(request, ControlRequest):
            raise TypeError("request must be a ControlRequest.")

        try:
            message = ControlPlaneProtocol.encode_request(request)

            with socket.create_connection(
                (self._host, self._port),
                timeout=self._timeout,
            ) as connection:
                connection.settimeout(self._timeout)
                connection.sendall(message)

                response = self._receive_response(connection)

        except (OSError, TimeoutError) as exc:
            raise ControlConnectionError(
                f"Unable to communicate with Control Plane at "
                f"{self._host}:{self._port}."
            ) from exc

        try:
            return ControlPlaneProtocol.decode_response(response)
        except ControlProtocolError:
            raise

    def _receive_response(self, connection: socket.socket) -> bytes:
        chunks: list[bytes] = []
        total_size = 0

        while True:
            chunk = connection.recv(4096)

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > self.MAX_RESPONSE_SIZE:
                raise ControlProtocolError(
                    "Control Plane response exceeds maximum size."
                )

            chunks.append(chunk)

            if b"\n" in chunk:
                break

        if not chunks:
            raise ControlProtocolError(
                "Control Plane response cannot be empty."
            )

        return b"".join(chunks)