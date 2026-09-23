"""
CLI adapter for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

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

        client = ControlPlaneTransportClient(
            host=endpoint.host,
            port=endpoint.port,
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