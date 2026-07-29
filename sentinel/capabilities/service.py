"""
High-level service for the Sentinel Capabilities subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.registry import CapabilityRegistry


class CapabilityService:
    """
    Public API for interacting with Sentinel capabilities.

    The service delegates capability management and execution to the
    underlying CapabilityManager while providing a stable interface for
    other Sentinel subsystems.
    """

    def __init__(
        self,
        manager: CapabilityManager | None = None,
    ) -> None:
        self._manager = manager or CapabilityManager()

    @property
    def manager(self) -> CapabilityManager:
        """
        Return the underlying capability manager.
        """
        return self._manager

    @property
    def registry(self) -> CapabilityRegistry:
        """
        Return the underlying capability registry.
        """
        return self._manager.registry

    def register(
        self,
        capability: BaseCapability,
    ) -> None:
        """
        Register a capability.
        """
        self._manager.register(capability)

    def unregister(
        self,
        capability_id: str,
    ) -> None:
        """
        Unregister a capability.
        """
        self._manager.unregister(capability_id)

    def execute(
        self,
        capability_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a registered capability.
        """
        return self._manager.execute(
            capability_id,
            **kwargs,
        )

    def exists(
        self,
        capability_id: str,
    ) -> bool:
        """
        Return True if the capability exists.
        """
        return self._manager.exists(capability_id)

    def list(self) -> list[BaseCapability]:
        """
        Return all registered capabilities.
        """
        return self._manager.list()

    def clear(self) -> None:
        """
        Remove all registered capabilities.
        """
        self._manager.clear()