"""
Capability registry for the Sentinel Capabilities subsystem.

The registry is responsible for:
- capability registration
- capability removal
- capability lookup
- capability discovery
- thread-safe access
- stable snapshots for readers
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityAlreadyExistsError,
    CapabilityNotFoundError,
)

CapabilityList = list[BaseCapability]


class CapabilityRegistry:
    """
    Thread-safe registry for Sentinel capabilities.

    Concurrency model
    -----------------
    Mutating operations are protected by an RLock.

    Read operations take the same lock while accessing the underlying
    dictionary. Collection-returning operations return snapshots so the
    caller never receives a live view of the registry.

    The lock is never held while a caller consumes an iterator or while
    a capability executes.
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

        Raises
        ------
        CapabilityAlreadyExistsError
            If another capability with the same ID is already registered.
        """
        if not isinstance(capability, BaseCapability):
            raise TypeError(
                "capability must be an instance of BaseCapability."
            )

        capability_id = capability.id

        with self._lock:
            if capability_id in self._capabilities:
                raise CapabilityAlreadyExistsError(
                    f"Capability '{capability_id}' already exists."
                )

            self._capabilities[capability_id] = capability

    def unregister(
        self,
        capability_id: str,
    ) -> None:
        """
        Remove a capability.

        Raises
        ------
        CapabilityNotFoundError
            If the capability is not registered.
        """
        self._validate_capability_id(capability_id)

        with self._lock:
            if capability_id not in self._capabilities:
                raise CapabilityNotFoundError(capability_id)

            del self._capabilities[capability_id]

    def get(
        self,
        capability_id: str,
    ) -> BaseCapability:
        """
        Return a registered capability.

        Raises
        ------
        CapabilityNotFoundError
            If the capability is not registered.
        """
        self._validate_capability_id(capability_id)

        with self._lock:
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
        Check whether a capability is registered.
        """
        self._validate_capability_id(capability_id)

        with self._lock:
            return capability_id in self._capabilities

    def list(
        self,
    ) -> CapabilityList:
        """
        Return a stable snapshot of all registered capabilities.
        """
        with self._lock:
            return list(self._capabilities.values())

    def list_by_category(
        self,
        category: CapabilityCategory,
    ) -> CapabilityList:
        """
        Return a stable snapshot of capabilities in a category.
        """
        if not isinstance(category, CapabilityCategory):
            raise TypeError(
                "category must be a CapabilityCategory."
            )

        with self._lock:
            return [
                capability
                for capability in self._capabilities.values()
                if capability.metadata.category == category
            ]

    @contextmanager
    def execution_admission(
        self,
        capability: BaseCapability,
    ) -> Iterator[None]:
        """Admit execution only for the currently registered instance."""
        with self._lock:
            if self._capabilities.get(capability.id) is not capability:
                raise CapabilityNotFoundError(capability.id)
            capability._admit_execution()

        # Once admitted, an execution may finish after unregistering.
        yield

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
        """
        Support ``capability_id in registry``.
        """
        self._validate_capability_id(capability_id)

        with self._lock:
            return capability_id in self._capabilities

    def __len__(self) -> int:
        """
        Return the number of registered capabilities.
        """
        with self._lock:
            return len(self._capabilities)

    def __iter__(self) -> Iterator[BaseCapability]:
        """
        Iterate over a stable registry snapshot.

        The registry lock is released before the caller consumes the
        iterator. Therefore concurrent registration/unregistration cannot
        invalidate the iterator.
        """
        with self._lock:
            snapshot = tuple(self._capabilities.values())

        return iter(snapshot)

    @staticmethod
    def _validate_capability_id(
        capability_id: str,
    ) -> None:
        """
        Validate a capability identifier.
        """
        if not isinstance(capability_id, str):
            raise TypeError(
                "capability_id must be a string."
            )

        if not capability_id.strip():
            raise ValueError(
                "capability_id cannot be empty."
            )