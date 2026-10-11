"""
CLI adapter for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

import os
import ssl
from collections.abc import Mapping

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.transport_client import (
    ControlPlaneTransportClient,
)
from sentinel.security.credentials import SecurityCredentials


class CLIKernelControl:
    """
    Execute Kernel Control Plane commands from the CLI.

    The CLI does not access the Kernel directly.

    Request path:

        CLI
          ↓
        Endpoint Registry
          ↓
        ControlPlaneTransportClient
          ↓
        Control Plane Transport
          ↓
        Control Plane
          ↓
        Kernel
    """

    def __init__(
        self,
        endpoint_registry: ControlPlaneEndpointRegistry | None = None,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        if endpoint_registry is not None and not isinstance(
            endpoint_registry,
            ControlPlaneEndpointRegistry,
        ):
            raise TypeError(
                "endpoint_registry must be a "
                "ControlPlaneEndpointRegistry instance."
            )

        self._endpoint_registry = (
            endpoint_registry
            if endpoint_registry is not None
            else ControlPlaneEndpointRegistry()
        )
        self._environ = os.environ if environ is None else environ

    @property
    def endpoint_registry(
        self,
    ) -> ControlPlaneEndpointRegistry:
        return self._endpoint_registry

    def execute(
        self,
        command: KernelCommand,
        data: dict[str, object] | None = None,
    ) -> ControlResult:
        """
        Execute a Kernel Control Plane command.
        """
        if not isinstance(command, KernelCommand):
            raise TypeError(
                "command must be a KernelCommand."
            )

        endpoint = self._endpoint_registry.load()

        security_keys = (
            "SENTINEL_ADMIN_USERNAME",
            "SENTINEL_ADMIN_SECRET",
            "SENTINEL_TLS_CA_FILE",
        )
        client_options: dict[str, object] = {}
        if any(key in self._environ for key in security_keys):
            username = self._environ.get("SENTINEL_ADMIN_USERNAME", "")
            secret = self._environ.get("SENTINEL_ADMIN_SECRET", "")
            ca_file = self._environ.get("SENTINEL_TLS_CA_FILE", "")
            if not all(
                isinstance(value, str) and value.strip()
                for value in (username, secret, ca_file)
            ):
                raise RuntimeError(
                    "Secure Control Plane access requires "
                    "SENTINEL_ADMIN_USERNAME, SENTINEL_ADMIN_SECRET, "
                    "and SENTINEL_TLS_CA_FILE."
                )

            ssl_context = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH,
                cafile=ca_file,
            )
            if (
                ssl_context.verify_mode == ssl.CERT_NONE
                or not ssl_context.check_hostname
            ):
                raise RuntimeError(
                    "TLS certificate and hostname verification are required."
                )
            client_options = {
                "ssl_context": ssl_context,
                "credentials": SecurityCredentials(username, secret),
            }

        client = ControlPlaneTransportClient(
            host=endpoint.host,
            port=endpoint.port,
            **client_options,
        )

        context = ControlContext(
            caller_id="cli",
            caller_type="cli",
        )

        request = ControlRequest(
            command=command,
            context=context,
            data=data or {},
        )

        return client.execute(request)

    def __repr__(self) -> str:
        return (
            "CLIKernelControl("
            f"endpoint_registry={self._endpoint_registry!r}"
            ")"
        )