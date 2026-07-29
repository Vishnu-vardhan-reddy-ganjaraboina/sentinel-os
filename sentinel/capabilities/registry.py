"""
Capability registry for the Sentinel Capabilities subsystem.
"""

from __future__ import annotations

from threading import RLock

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityAlreadyExistsError,
    CapabilityNotFoundError,
)


class CapabilityRegistry:
    """
    Thread-safe registry for Sentinel capabilities.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, BaseCapability] = {}
        self._lock = RLock()

    def register(
        self,
        capability: BaseCapability,
    ) -> None:
        """
        Register a capability.
        """
        with self._lock:
            if capability.id in self._capabilities:
                raise CapabilityAlreadyExistsError(
                    f"Capability '{capability.id}' already exists."
                )

            self._capabilities[capability.id] = capability

    def unregister(
        self,
        capability_id: str,
    ) -> None:
        """
        Remove a capability.
        """
        with self._lock:
            if capability_id not in self._capabilities:
                raise CapabilityNotFoundError(
                    capability_id
                )

            del self._capabilities[capability_id]

    def get(
        self,
        capability_id: str,
    ) -> BaseCapability:
        """
        Return a capability.
        """
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise CapabilityNotFoundError(
                capability_id
            ) from exc

    def exists(
        self,
        capability_id: str,
    ) -> bool:
        """
        Check whether a capability exists.
        """
        return capability_id in self._capabilities

    def list(
        self,
    ) -> list[BaseCapability]:
        """
        Return all registered capabilities.
        """
        return list(self._capabilities.values())

    def list_by_category(
        self,
        category: CapabilityCategory,
    ) -> list[BaseCapability]:
        """
        Return capabilities belonging to a category.
        """
        return [
            capability
            for capability in self._capabilities.values()
            if capability.metadata.category == category
        ]

    def clear(self) -> None:
        """
        Remove all registered capabilities.
        """
        with self._lock:
            self._capabilities.clear()

    def __contains__(
        self,
        capability_id: str,
    ) -> bool:
        return capability_id in self._capabilities

    def __len__(self) -> int:
        return len(self._capabilities)

    def __iter__(self):
        return iter(self._capabilities.values())