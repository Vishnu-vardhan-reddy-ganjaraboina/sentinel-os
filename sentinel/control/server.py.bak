"""
Local TCP control server for Sentinel OS.
"""

from __future__ import annotations

import socketserver
from threading import RLock, Thread
from typing import Any

from sentinel.control.exceptions import ControlRequestError
from sentinel.control.protocol import ControlCommand, ControlProtocol
from sentinel.control.target import ProcessControlTarget


class _ControlTCPServer(
    socketserver.ThreadingTCPServer,
):
    allow_reuse_address = True
    daemon_threads = True


class _ControlRequestHandler(
    socketserver.BaseRequestHandler,
):
    """Handle a single Sentinel control request."""

    def handle(self) -> None:
        server = self.server
        if not isinstance(server, _ControlTCPServer):
            return

        host = getattr(server, "process_host", None)

        if host is None:
            return

        self.request.settimeout(5.0)

        try:
            message = self._receive_message()
            command, data = ControlProtocol.decode_request(message)

            response = self._dispatch(
                host,
                command,
                data,
            )

        except Exception as exc:
            response = ControlProtocol.encode_response(
                False,
                error=str(exc),
            )

        self.request.sendall(response)

    def _receive_message(self) -> bytes:
        """Read one newline-delimited request."""
        chunks: list[bytes] = []
        total = 0
        maximum = 64 * 1024

        while True:
            chunk = self.request.recv(4096)

            if not chunk:
                break

            chunks.append(chunk)
            total += len(chunk)

            if total > maximum:
                raise ControlRequestError(
                    "Control request exceeds maximum size."
                )

            if b"\n" in chunk:
                break

        message = b"".join(chunks)

        if b"\n" in message:
            message = message.split(b"\n", 1)[0]

        return message

    @staticmethod
    def _dispatch(
        host: ProcessControlTarget,
        command: ControlCommand,
        data: dict[str, Any],
    ) -> bytes:
        """Dispatch a validated control command."""
        if data:
            # The initial protocol does not define command-specific input.
            # Rejecting unexpected data keeps the control surface explicit.
            raise ControlRequestError(
                "Control command data is not supported."
            )

        if command is ControlCommand.STATUS:
            return ControlProtocol.encode_response(
                True,
                data={
                    "state": host.state.value,
                    "running": host.running,
                },
            )

        if command is ControlCommand.HEALTH:
            return ControlProtocol.encode_response(
                True,
                data=host.health(),
            )

        if command is ControlCommand.STOP:
            host.request_stop()

            return ControlProtocol.encode_response(
                True,
                data={
                    "state": host.state.value,
                    "stop_requested": True,
                },
            )

        raise ControlRequestError(
            f"Unsupported control command: {command.value!r}."
        )


class ControlServer:
    """
    Run the Sentinel local control endpoint.

    The endpoint is always bound to loopback only.
    """

    def __init__(
        self,
        process_host: ProcessControlTarget,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        if not isinstance(
            process_host,
            ProcessControlTarget,
        ):
            raise TypeError(
                "process_host must implement ProcessControlTarget."
            )

        if not isinstance(host, str):
            raise TypeError("host must be a string.")

        host = host.strip()

        if host != "127.0.0.1":
            raise ValueError(
                "ControlServer must bind to 127.0.0.1."
            )

        if not isinstance(port, int):
            raise TypeError("port must be an integer.")

        if not 0 <= port <= 65535:
            raise ValueError(
                "port must be between 0 and 65535."
            )

        self._process_host = process_host
        self._host = host
        self._port = port
        self._server: _ControlTCPServer | None = None
        self._thread: Thread | None = None
        self._lock = RLock()

    @property
    def process_host(self) -> ProcessControlTarget:
        """Return the managed process-control target."""
        return self._process_host

    @property
    def host(self) -> str:
        """Return the loopback host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the bound port."""
        with self._lock:
            if self._server is None:
                return self._port

            return int(self._server.server_address[1])

    @property
    def running(self) -> bool:
        """Return whether the control server is running."""
        with self._lock:
            return self._server is not None

    @property
    def address(self) -> tuple[str, int]:
        """Return the control endpoint address."""
        return self.host, self.port

    def start(self) -> None:
        """Start serving control requests in a background thread."""
        with self._lock:
            if self._server is not None:
                raise RuntimeError(
                    "Control server is already running."
                )

            server = _ControlTCPServer(
                (self._host, self._port),
                _ControlRequestHandler,
            )
            server.process_host = self._process_host

            thread = Thread(
                target=server.serve_forever,
                name="sentinel-control-server",
                daemon=True,
            )

            self._server = server
            self._thread = thread

        try:
            thread.start()
        except Exception:
            with self._lock:
                self._server = None
                self._thread = None

            server.server_close()
            raise

    def stop(self) -> None:
        """Stop the control server."""
        with self._lock:
            server = self._server
            thread = self._thread

            if server is None:
                return

            self._server = None
            self._thread = None

        server.shutdown()
        server.server_close()

        if thread is not None:
            thread.join(timeout=5.0)

    def __enter__(self) -> ControlServer:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.stop()

    def __repr__(self) -> str:
        return (
            "ControlServer("
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"running={self.running}"
            ")"
        )
