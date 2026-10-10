"""
Network transport server for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

import math
import socket
import threading
import time

from sentinel.control.exceptions import ControlProtocolError
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.transport import ControlPlaneProtocol


class ControlPlaneTransportServer:
    """
    Serve Kernel Control Plane requests over a TCP socket.

    The server is intentionally thin:
    - receives transport messages
    - decodes ControlRequest
    - delegates to ControlPlane
    - encodes ControlResult
    - returns the response

    Authorization, auditing, command validation, and Kernel interaction
    remain inside the Control Plane.
    """

    MAX_MESSAGE_SIZE = 64 * 1024

    def __init__(
        self,
        control_plane: ControlPlane,
        host: str = "127.0.0.1",
        port: int = 0,
        read_timeout: float = 5.0,
        message_timeout: float = 30.0,
        listen_backlog: int = 5,
    ) -> None:
        if not isinstance(control_plane, ControlPlane):
            raise TypeError("control_plane must be a ControlPlane.")

        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must not be empty.")

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if port < 0 or port > 65535:
            raise ValueError("port must be between 0 and 65535.")

        if (
            isinstance(listen_backlog, bool)
            or not isinstance(listen_backlog, int)
            or listen_backlog <= 0
        ):
            raise ValueError("listen_backlog must be a positive integer.")

        if (
            isinstance(read_timeout, bool)
            or not isinstance(read_timeout, (int, float))
            or not math.isfinite(read_timeout)
            or read_timeout <= 0
        ):
            raise ValueError("read_timeout must be a finite positive number.")

        if (
            isinstance(message_timeout, bool)
            or not isinstance(message_timeout, (int, float))
            or not math.isfinite(message_timeout)
            or message_timeout <= 0
        ):
            raise ValueError(
                "message_timeout must be a finite positive number."
            )

        self._control_plane = control_plane
        self._host = host
        self._port = port
        self._listen_backlog = listen_backlog
        self._read_timeout = float(read_timeout)
        self._message_timeout = float(message_timeout)

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._active_connection: socket.socket | None = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

    @property
    def control_plane(self) -> ControlPlane:
        return self._control_plane

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        with self._lock:
            if self._socket is None:
                return self._port
            return int(self._socket.getsockname()[1])

    @property
    def running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.running:
                raise RuntimeError("Control Plane transport server is already running.")

            self._stop_event.clear()

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self._host, self._port))
            server_socket.listen(self._listen_backlog)

            self._socket = server_socket

            thread = threading.Thread(
                target=self._serve,
                name="sentinel-control-plane-transport",
                daemon=True,
            )
            self._thread = thread
            thread.start()

    def stop(self) -> None:
        with self._lock:
            if (
                not self.running
                and self._socket is None
                and self._active_connection is None
            ):
                return

            self._stop_event.set()

            server_socket = self._socket
            self._socket = None
            active_connection = self._active_connection
            thread = self._thread

        if server_socket is not None:
            try:
                server_socket.close()
            except OSError:
                pass

        if active_connection is not None:
            try:
                active_connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                active_connection.close()
            except OSError:
                pass

        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

        with self._lock:
            if thread is not None and not thread.is_alive():
                if self._thread is thread:
                    self._thread = None

    def _serve(self) -> None:
        with self._lock:
            server_socket = self._socket

        if server_socket is None:
            return

        while not self._stop_event.is_set():
            try:
                connection, _address = server_socket.accept()
            except OSError:
                if self._stop_event.is_set():
                    break
                continue

            with self._lock:
                stopping = self._stop_event.is_set()
                if not stopping:
                    self._active_connection = connection

            if stopping:
                try:
                    connection.close()
                except OSError:
                    pass
                break

            try:
                self._handle_connection(connection)
            finally:
                with self._lock:
                    if self._active_connection is connection:
                        self._active_connection = None

                try:
                    connection.close()
                except OSError:
                    pass

    def _handle_connection(self, connection: socket.socket) -> None:
        try:
            deadline = time.monotonic() + self._message_timeout
            message = self._receive_message(connection, deadline)
            request = ControlPlaneProtocol.decode_request(message)

            result = self._control_plane.execute_request(request)

            response = ControlPlaneProtocol.encode_response(result)
            connection.sendall(response)

        except TimeoutError:
            self._send_protocol_error(connection, "Control message timed out.")
        except ControlProtocolError as exc:
            self._send_protocol_error(connection, str(exc))

        except Exception as exc:
            self._send_protocol_error(
                connection,
                f"Control Plane request failed: {exc}",
            )

    def _receive_message(
        self,
        connection: socket.socket,
        deadline: float,
    ) -> bytes:
        chunks: list[bytes] = []
        total_size = 0

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Control message timed out.")

            connection.settimeout(min(self._read_timeout, remaining))
            chunk = connection.recv(4096)

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > self.MAX_MESSAGE_SIZE:
                raise ControlProtocolError(
                    "Control message exceeds maximum size."
                )

            chunks.append(chunk)

            if b"\n" in chunk:
                break

        if not chunks:
            raise ControlProtocolError(
                "Control message cannot be empty."
            )

        return b"".join(chunks)

    @staticmethod
    def _send_protocol_error(
        connection: socket.socket,
        message: str,
    ) -> None:
        try:
            response = ControlPlaneProtocol.encode_response(
                _protocol_error_result(message)
            )
            connection.sendall(response)
        except (OSError, ControlProtocolError):
            pass


def _protocol_error_result(message: str) -> ControlResult:

    return ControlResult(
        success=False,
        command="transport.error",
        error=message,
    )