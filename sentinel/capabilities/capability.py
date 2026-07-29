"""
Base implementation of a Sentinel capability.
"""

from __future__ import annotations

from abc import abstractmethod
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
        self._metadata = metadata

    @property
    def metadata(self) -> CapabilityMetadata:
        """
        Return the capability metadata.
        """
        return self._metadata

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
        return self._metadata.enabled

    def enable(self) -> None:
        self._metadata.enabled = True

    def disable(self) -> None:
        self._metadata.enabled = False

    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the capability.
        """
        if not self.enabled:
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
        Execute the concrete capability.
        """