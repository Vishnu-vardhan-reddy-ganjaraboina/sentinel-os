"""
Kernel Control Plane endpoint registry.

The registry publishes the runtime network endpoint of the Kernel Control
Plane so external Sentinel components can discover it without hard-coding
host or port values.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True, slots=True)
class ControlPlaneEndpoint:
    """
    Runtime endpoint information for the Kernel Control Plane.
    """

    version: int
    host: str
    port: int

    def __post_init__(self) -> None:
        if not isinstance(self.version, int):
            raise TypeError("version must be an integer.")

        if self.version < 1:
            raise ValueError("version must be greater than zero.")

        if not isinstance(self.host, str):
            raise TypeError("host must be a string.")

        if not self.host.strip():
            raise ValueError("host must not be empty.")

        if not isinstance(self.port, int):
            raise TypeError("port must be an integer.")

        if not 1 <= self.port <= 65535:
            raise ValueError(
                "port must be between 1 and 65535."
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "host": self.host,
            "port": self.port,
        }

    @classmethod
    def from_mapping(
        cls,
        data: object,
    ) -> "ControlPlaneEndpoint":
        if not isinstance(data, dict):
            raise TypeError(
                "Endpoint data must be a mapping."
            )

        return cls(
            version=data["version"],
            host=data["host"],
            port=data["port"],
        )


class ControlPlaneEndpointRegistry:
    """
    Publish and remove the Kernel Control Plane runtime endpoint.

    The registry does not manage the Control Plane transport lifecycle.
    Callers are responsible for ensuring the transport is running before
    publishing its endpoint.
    """

    def __init__(
        self,
        path: str | Path = "data/sentinel/kernel-control.json",
    ) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def registered(self) -> bool:
        return self._path.is_file()

    def publish(
        self,
        endpoint: ControlPlaneEndpoint,
    ) -> None:
        if not isinstance(
            endpoint,
            ControlPlaneEndpoint,
        ):
            raise TypeError(
                "endpoint must be a ControlPlaneEndpoint instance."
            )

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = json.dumps(
            endpoint.to_mapping(),
            indent=2,
            sort_keys=True,
        ) + "\n"

        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)

            os.replace(
                temporary_path,
                self._path,
            )
            temporary_path = None

        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass

    def load(self) -> ControlPlaneEndpoint:
        if not self._path.is_file():
            raise FileNotFoundError(
                f"Control Plane endpoint registry does not exist: "
                f"{self._path}"
            )

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return ControlPlaneEndpoint.from_mapping(data)

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def __repr__(self) -> str:
        return (
            "ControlPlaneEndpointRegistry("
            f"path={str(self._path)!r}"
            ")"
        )