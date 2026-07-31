"""
Abstract interfaces for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sentinel.plugins.constants import PluginState, PluginType


class Plugin(ABC):
    """
    Base interface for all Sentinel plugins.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        ...

    @property
    @abstractmethod
    def state(self) -> PluginState:
        ...

    @abstractmethod
    def load(self) -> None:
        ...

    @abstractmethod
    def enable(self) -> None:
        ...

    @abstractmethod
    def disable(self) -> None:
        ...

    @abstractmethod
    def unload(self) -> None:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class PluginRegistry(ABC):
    """
    Stores and manages plugins.
    """

    @abstractmethod
    def register(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def unregister(self, name: str) -> None:
        ...

    @abstractmethod
    def get(self, name: str) -> Plugin:
        ...

    @abstractmethod
    def all(self) -> list[Plugin]:
        ...


class PluginLoader(ABC):
    """
    Loads and manages the lifecycle of plugins.
    """

    @abstractmethod
    def load(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def enable(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def disable(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def unload(self, plugin: Plugin) -> None:
        ...