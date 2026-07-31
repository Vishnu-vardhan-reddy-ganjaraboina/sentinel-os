"""
Abstract interfaces for the Sentinel UI subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sentinel.ui.constants import (
    Theme,
    ViewState,
    WindowState,
)


class View(ABC):
    """
    Base interface for UI views.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def state(self) -> ViewState:
        ...

    @abstractmethod
    def show(self) -> None:
        ...

    @abstractmethod
    def hide(self) -> None:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class Window(ABC):
    """
    Base interface for application windows.
    """

    @property
    @abstractmethod
    def title(self) -> str:
        ...

    @property
    @abstractmethod
    def state(self) -> WindowState:
        ...

    @property
    @abstractmethod
    def theme(self) -> Theme:
        ...

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def minimize(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class UIManager(ABC):
    """
    Coordinates windows and views.
    """

    @abstractmethod
    def add_view(self, view: View) -> None:
        ...

    @abstractmethod
    def remove_view(self, name: str) -> None:
        ...

    @abstractmethod
    def get_view(self, name: str) -> View:
        ...

    @abstractmethod
    def set_window(self, window: Window) -> None:
        ...

    @abstractmethod
    def get_window(self) -> Window:
        ...

    @abstractmethod
    def views(self) -> list[View]:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...