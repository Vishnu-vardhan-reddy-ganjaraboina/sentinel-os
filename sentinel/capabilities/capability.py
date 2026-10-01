"""
Base implementation of a Sentinel capability.
"""

from __future__ import annotations

from abc import abstractmethod
from threading import RLock
from typing import Any

from sentinel.capabilities.exceptions import (
    CapabilityDisabledError,
)
from sentinel.capabilities.interfaces import Capability
from sentinel.capabilities.metadata import CapabilityMetadata


class BaseCapability(Capability):
    """
    Base implementation for Sentinel capabilities.

    Capability execution and enabled-state transitions are protected
    against concurrent state changes.
    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
    ) -> None:
        if not isinstance(metadata, CapabilityMetadata):
            raise TypeError(
                "metadata must be a CapabilityMetadata instance."
            )

        self._metadata = metadata
        self._state_lock = RLock()

    @property
    def metadata(self) -> CapabilityMetadata:
        """
        Return the capability metadata.
        """
        return self._metadata

    @property
    def id(self) -> str:
        """
        Return the capability identifier.
        """
        return self._metadata.capability_id

    @property
    def name(self) -> str:
        """
        Return the capability name.
        """
        return self._metadata.name

    @property
    def description(self) -> str:
        """
        Return the capability description.
        """
        return self._metadata.description

    @property
    def version(self) -> str:
        """
        Return the capability version.
        """
        return self._metadata.version

    @property
    def enabled(self) -> bool:
        """
        Return whether the capability is currently enabled.
        """
        with self._state_lock:
            return self._metadata.enabled

    def enable(self) -> None:
        """
        Enable the capability.
        """
        with self._state_lock:
            self._metadata.enabled = True

    def disable(self) -> None:
        """
        Disable the capability.
        """
        with self._state_lock:
            self._metadata.enabled = False

    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the capability.

        The enabled state is checked atomically with respect to
        enable/disable operations.

        Once execution begins, disabling the capability does not
        forcibly interrupt an already-running ``run()`` operation.
        """
        with self._state_lock:
            if not self._metadata.enabled:
                raise CapabilityDisabledError(
                    f"Capability '{self.id}' is disabled."
                )

        return self.run(**kwargs)

    @abstractmethod
    def run(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the concrete capability implementation.
        """