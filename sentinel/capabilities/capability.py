"""
Base implementation of a Sentinel capability.
"""

from __future__ import annotations

from abc import abstractmethod
from copy import deepcopy
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

    Concrete capabilities should inherit from this class and implement
    the `run()` method.
    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
    ) -> None:
        self._metadata = deepcopy(metadata)
        self._state_lock = RLock()

    @property
    def metadata(self) -> CapabilityMetadata:
        """Return an isolated snapshot of the capability metadata."""
        with self._state_lock:
            return deepcopy(self._metadata)

    @property
    def id(self) -> str:
        return self._metadata.capability_id

    @property
    def name(self) -> str:
        return self._metadata.name

    @property
    def description(self) -> str:
        return self._metadata.description

    @property
    def version(self) -> str:
        return self._metadata.version

    @property
    def enabled(self) -> bool:
        with self._state_lock:
            return self._metadata.enabled

    def enable(self) -> None:
        with self._state_lock:
            self._metadata.enabled = True

    def disable(self) -> None:
        with self._state_lock:
            self._metadata.enabled = False

    def _admit_execution(self) -> None:
        """Admit execution only while the capability is enabled."""
        with self._state_lock:
            if not self._metadata.enabled:
                raise CapabilityDisabledError(
                    f"Capability '{self.id}' is disabled."
                )

    def _execute_admitted(self, **kwargs: Any) -> Any:
        """Run a capability whose execution has already been admitted."""
        return self.run(**kwargs)

    def execute(self, **kwargs: Any) -> Any:
        """Execute the capability if it is enabled."""
        self._admit_execution()
        return self._execute_admitted(**kwargs)

    @abstractmethod
    def run(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the concrete capability.
        """