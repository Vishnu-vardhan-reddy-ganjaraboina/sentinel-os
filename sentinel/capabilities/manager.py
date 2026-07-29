"""
Capability manager for the Sentinel Capabilities subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.exceptions import (
    CapabilityExecutionError,
)
from sentinel.capabilities.registry import CapabilityRegistry


class CapabilityManager:
    """
    Manages capability execution.

    The manager acts as the runtime layer between the registry
    and the rest of Sentinel OS.
    """

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        self._registry = registry or CapabilityRegistry()

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
        """
        capability = self._registry.get(capability_id)

        try:
            return capability.execute(**kwargs)

        except Exception as exc:
            raise CapabilityExecutionError(
                f"Capability '{capability_id}' failed."
            ) from exc

    def list(self) -> list[BaseCapability]:
        """
        Return all registered capabilities.
        """
        return self._registry.list()

    def exists(
        self,
        capability_id: str,
    ) -> bool:
        """
        Return True if the capability exists.
        """
        return self._registry.exists(capability_id)

    def clear(self) -> None:
        """
        Remove all registered capabilities.
        """
        self._registry.clear()