"""
Persistent local control endpoint metadata for Sentinel OS.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import RLock


@dataclass(frozen=True, slots=True)
class ControlEndpoint:
    """Address of the local Sentinel control server."""

    host: str = "127.0.0.1"
    port: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.host, str):
            raise TypeError("host must be a string.")

        host = self.host.strip()

        if host != "127.0.0.1":
            raise ValueError(
                "Control endpoint must use 127.0.0.1."
            )

        if not isinstance(self.port, int):
            raise TypeError("port must be an integer.")

        if not 1 <= self.port <= 65535:
            raise ValueError(
                "port must be between 1 and 65535."
            )

        object.__setattr__(self, "host", host)

    def to_dict(self) -> dict[str, str | int]:
        """Return an isolated dictionary representation."""
        return {
            "host": self.host,
            "port": self.port,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> ControlEndpoint:
        """Create an endpoint from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary.")

        host = data.get("host", "127.0.0.1")
        port = data.get("port")

        if not isinstance(host, str):
            raise ValueError("Control endpoint host must be a string.")

        if not isinstance(port, int):
            raise ValueError("Control endpoint port must be an integer.")

        return cls(
            host=host,
            port=port,
        )


class ControlEndpointRegistry:
    """
    Persist and retrieve the active Sentinel control endpoint.

    The registry uses an atomic replace operation so readers never
    intentionally observe a partially written JSON file.
    """

    def __init__(
        self,
        path: str | Path = "data/sentinel/control.json",
    ) -> None:
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be a string or Path.")

        resolved = Path(path)

        if resolved.name != "control.json":
            raise ValueError(
                "Control endpoint registry must use control.json."
            )

        self._path = resolved
        self._lock = RLock()

    @property
    def path(self) -> Path:
        """Return the registry path."""
        return self._path

    def exists(self) -> bool:
        """Return whether the registry file exists."""
        with self._lock:
            return self._path.is_file()

    def save(self, endpoint: ControlEndpoint) -> None:
        """Atomically persist the control endpoint."""
        if not isinstance(endpoint, ControlEndpoint):
            raise TypeError(
                "endpoint must be a ControlEndpoint."
            )

        payload = {
            "version": 1,
            "endpoint": endpoint.to_dict(),
        }

        with self._lock:
            self._path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            fd, temporary_path = tempfile.mkstemp(
                prefix=".control-",
                suffix=".tmp",
                dir=self._path.parent,
                text=True,
            )

            try:
                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        payload,
                        file,
                        separators=(",", ":"),
                    )
                    file.flush()
                    os.fsync(file.fileno())

                os.replace(
                    temporary_path,
                    self._path,
                )

            except Exception:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
                raise

    def load(self) -> ControlEndpoint:
        """Load and validate the persisted endpoint."""
        with self._lock:
            if not self._path.is_file():
                raise FileNotFoundError(
                    f"Control endpoint not found: {self._path}"
                )

            try:
                with self._path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    payload = json.load(file)

            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    "Control endpoint registry is invalid."
                ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "Control endpoint registry must contain a JSON object."
            )

        if payload.get("version") != 1:
            raise ValueError(
                "Unsupported control endpoint registry version."
            )

        endpoint_data = payload.get("endpoint")

        if not isinstance(endpoint_data, dict):
            raise ValueError(
                "Control endpoint data must be a dictionary."
            )

        try:
            return ControlEndpoint.from_dict(
                endpoint_data,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Control endpoint registry contains invalid endpoint data."
            ) from exc

    def remove(self) -> None:
        """Remove the persisted control endpoint if present."""
        with self._lock:
            try:
                self._path.unlink()
            except FileNotFoundError:
                return

    def clear_if_stale(self) -> bool:
        """
        Remove an endpoint when the recorded port is no longer listening.

        Returns True when the registry was removed.
        """
        import socket

        try:
            endpoint = self.load()
        except (FileNotFoundError, ValueError):
            return False

        connection = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        try:
            connection.settimeout(0.2)

            if connection.connect_ex(
                (endpoint.host, endpoint.port),
            ) == 0:
                return False

        finally:
            connection.close()

        self.remove()
        return True

    def __repr__(self) -> str:
        return (
            "ControlEndpointRegistry("
            f"path={str(self.path)!r}"
            ")"
        )
