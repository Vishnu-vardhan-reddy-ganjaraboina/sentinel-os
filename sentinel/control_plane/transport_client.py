"""
TCP client for the Sentinel Kernel Control Plane transport.
"""

from __future__ import annotations

import math
import socket
import ssl

from sentinel.control.exceptions import ControlConnectionError, ControlProtocolError
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.transport import ControlPlaneProtocol
from sentinel.security.credentials import SecurityCredentials


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
        ssl_context: ssl.SSLContext | None = None,
        credentials: SecurityCredentials | None = None,
    ) -> None:
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must not be empty.")

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if port < 1 or port > 65535:
            raise ValueError("port must be between 1 and 65535.")

        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a number.")

        try:
            valid_timeout = math.isfinite(timeout) and timeout > 0
        except OverflowError:
            valid_timeout = False

        if not valid_timeout:
            raise ValueError("timeout must be a finite positive number.")

        if ssl_context is not None and not isinstance(
            ssl_context,
            ssl.SSLContext,
        ):
            raise TypeError("ssl_context must be an SSLContext or None.")

        if credentials is not None and not isinstance(
            credentials,
            SecurityCredentials,
        ):
            raise TypeError(
                "credentials must be SecurityCredentials or None."
            )

        if credentials is not None and ssl_context is None:
            raise ValueError(
                "TLS must be configured before sending credentials."
            )

        if ssl_context is not None:
            if ssl_context.verify_mode == ssl.CERT_NONE:
                raise ValueError(
                    "TLS certificate verification must be enabled."
                )
            if not ssl_context.check_hostname:
                raise ValueError(
                    "TLS hostname verification must be enabled."
                )

        self._host = host
        self._port = port
        self._timeout = float(timeout)
        self._ssl_context = ssl_context
        self._credentials = credentials

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
            message = ControlPlaneProtocol.encode_request(
                request,
                credentials=self._credentials,
            )

            with socket.create_connection(
                (self._host, self._port),
                timeout=self._timeout,
            ) as raw_connection:
                raw_connection.settimeout(self._timeout)

                if self._ssl_context is not None:
                    with self._ssl_context.wrap_socket(
                        raw_connection,
                        server_hostname=self._host,
                    ) as connection:
                        connection.settimeout(self._timeout)
                        connection.sendall(message)
                        response = self._receive_response(connection)
                else:
                    raw_connection.sendall(message)
                    response = self._receive_response(raw_connection)

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