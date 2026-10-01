"""
Capability manager for the Sentinel Capabilities subsystem.

The manager provides the execution boundary between registered
capabilities and the rest of Sentinel OS.
"""

from __future__ import annotations

from typing import Any

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.exceptions import (
    CapabilityDisabledError,
    CapabilityExecutionError,
)
from sentinel.capabilities.registry import CapabilityRegistry


class CapabilityManager:
    """
    Manages capability registration and execution.

    The manager deliberately does not maintain a second capability store.
    The registry remains the source of truth.
    """

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        self._registry = (
            registry
            if registry is not None
            else CapabilityRegistry()
        )

    @property
    def registry(self) -> CapabilityRegistry:
        """
        Return the capability registry.
        """
        return self._registry

    def register(
        self,
        capability: BaseCapability,
    ) -> None:
        """
        Register a capability.
        """
        self._registry.register(capability)

    def unregister(
        self,
        capability_id: str,
    ) -> None:
        """
        Unregister a capability.
        """
        self._registry.unregister(capability_id)

    def execute(
        self,
        capability_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a registered capability.

        The capability is looked up before execution. The registry lock
        is not held during execution, which prevents long-running
        capabilities from blocking registry operations.

        CapabilityDisabledError is intentionally preserved.

        Other exceptions are wrapped in CapabilityExecutionError while
        preserving the original exception as ``__cause__``.
        """
        capability = self._registry.get(capability_id)

        try:
            return capability.execute(**kwargs)

        except CapabilityDisabledError:
            raise

        except Exception as exc:
            raise CapabilityExecutionError(
                f"Capability '{capability_id}' failed."
            ) from exc

    def list(self) -> list[BaseCapability]:
        """
        Return a stable snapshot of registered capabilities.
        """
        return self._registry.list()

    def exists(
        self,
        capability_id: str,
    ) -> bool:
        """
        Return whether a capability is registered.
        """
        return self._registry.exists(capability_id)

    def clear(self) -> None:
        """
        Remove all registered capabilities.
        """
        self._registry.clear()