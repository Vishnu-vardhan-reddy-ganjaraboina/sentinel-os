"""
Network transport server for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

import socket
import threading
from concurrent.futures import ThreadPoolExecutor

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
    DEFAULT_CLIENT_TIMEOUT = 5.0
    DEFAULT_MAX_WORKERS = 4

    def __init__(
        self,
        control_plane: ControlPlane,
        host: str = "127.0.0.1",
        port: int = 0,
        client_timeout: float = DEFAULT_CLIENT_TIMEOUT,
        *,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        if not isinstance(control_plane, ControlPlane):
            raise TypeError("control_plane must be a ControlPlane.")

        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must not be empty.")

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if port < 0 or port > 65535:
            raise ValueError("port must be between 0 and 65535.")

        if isinstance(client_timeout, bool) or not isinstance(
            client_timeout,
            (int, float),
        ):
            raise TypeError("client_timeout must be a number.")

        if client_timeout <= 0:
            raise ValueError("client_timeout must be greater than zero.")

        if isinstance(max_workers, bool) or not isinstance(max_workers, int):
            raise TypeError("max_workers must be an integer.")

        if max_workers <= 0:
            raise ValueError("max_workers must be greater than zero.")

        self._control_plane = control_plane
        self._host = host
        self._port = port
        self._client_timeout = float(client_timeout)
        self._max_workers = max_workers

        self._executor: ThreadPoolExecutor | None = None
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
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
    def client_timeout(self) -> float:
        return self._client_timeout

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.running:
                raise RuntimeError("Control Plane transport server is already running.")

            self._stop_event.clear()

            executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="sentinel-control-plane-worker",
            )

            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_REUSEADDR,
                    1,
                )
                server_socket.bind((self._host, self._port))
                server_socket.listen()
            except Exception:
                executor.shutdown(wait=True)
                raise

            self._socket = server_socket
            self._executor = executor

            thread = threading.Thread(
                target=self._serve,
                name="sentinel-control-plane-transport",
                daemon=True,
            )
            self._thread = thread

            try:
                thread.start()
            except Exception:
                self._thread = None
                self._socket = None
                self._executor = None

                try:
                    server_socket.close()
                except OSError:
                    pass

                executor.shutdown(wait=True)
                raise
    def stop(self) -> None:
        with self._lock:
            if (
                not self.running
                and self._socket is None
                and self._executor is None
            ):
                return

            self._stop_event.set()

            server_socket = self._socket
            executor = self._executor

            self._socket = None
            self._executor = None

        if server_socket is not None:
            try:
                server_socket.close()
            except OSError:
                pass

        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

        if executor is not None:
            executor.shutdown(wait=True)

        with self._lock:
            self._thread = None
    def _serve(self) -> None:
        server_socket = self._socket
        executor = self._executor

        if server_socket is None or executor is None:
            return

        while not self._stop_event.is_set():
            try:
                connection, _address = server_socket.accept()
            except OSError:
                if self._stop_event.is_set():
                    break
                continue

            try:
                executor.submit(
                    self._handle_connection_and_close,
                    connection,
                )
            except RuntimeError:
                try:
                    connection.close()
                except OSError:
                    pass
    def _handle_connection_and_close(
        self,
        connection: socket.socket,
    ) -> None:
        try:
            self._handle_connection(connection)
        finally:
            try:
                connection.close()
            except OSError:
                pass

    def _handle_connection(self, connection: socket.socket) -> None:
        try:
            connection.settimeout(self._client_timeout)
            message = self._receive_message(connection)
            connection.settimeout(None)

            request = ControlPlaneProtocol.decode_request(message)

            result = self._control_plane.execute_request(request)

            response = ControlPlaneProtocol.encode_response(result)
            connection.sendall(response)

        except ControlProtocolError as exc:
            self._send_protocol_error(connection, str(exc))

        except Exception as exc:
            self._send_protocol_error(
                connection,
                f"Control Plane request failed: {exc}",
            )

    def _receive_message(self, connection: socket.socket) -> bytes:
        chunks: list[bytes] = []
        total_size = 0

        while True:
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
    from sentinel.control_plane.result import ControlResult

    return ControlResult(
        success=False,
        command="transport.error",
        error=message,
    )
