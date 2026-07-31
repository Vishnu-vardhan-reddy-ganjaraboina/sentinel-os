"""
Window implementation for the Sentinel UI subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.ui.constants import (
    Theme,
    WindowState,
)
from sentinel.ui.interfaces import Window


class UIWindow(Window):
    """
    Default implementation of an application window.
    """

    def __init__(
        self,
        title: str,
        theme: Theme = Theme.SYSTEM,
    ) -> None:

        if not title:
            raise ValueError("title cannot be empty")

        if not isinstance(theme, Theme):
            raise TypeError("theme must be a Theme")

        self._title = title
        self._theme = theme
        self._state = WindowState.CREATED

    @property
    def title(self) -> str:
        return self._title

    @property
    def state(self) -> WindowState:
        return self._state

    @property
    def theme(self) -> Theme:
        return self._theme

    def open(self) -> None:
        self._state = WindowState.OPEN

    def minimize(self) -> None:
        self._state = WindowState.MINIMIZED

    def close(self) -> None:
        self._state = WindowState.CLOSED

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "theme": self.theme.value,
            "state": self.state.value,
        }

    def __repr__(self) -> str:
        return (
            f"UIWindow("
            f"title={self.title!r}, "
            f"theme={self.theme.value!r}, "
            f"state={self.state.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UIWindow):
            return False

        return (
            self.title == other.title
            and self.theme == other.theme
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.title,
                self.theme,
            )
        )