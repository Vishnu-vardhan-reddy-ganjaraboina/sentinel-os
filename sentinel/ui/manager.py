"""
Manager for the Sentinel UI subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.ui.exceptions import (
    ViewNotFoundError,
)
from sentinel.ui.interfaces import (
    UIManager,
    View,
    Window,
)


class SentinelUIManager(UIManager):
    """
    Coordinates windows and views.
    """

    def __init__(self) -> None:

        self._views: dict[str, View] = {}
        self._window: Window | None = None

    @property
    def window(self) -> Window | None:
        return self._window

    def add_view(
        self,
        view: View,
    ) -> None:
        self._views[view.name] = view

    def remove_view(
        self,
        name: str,
    ) -> None:

        if name not in self._views:
            raise ViewNotFoundError(
                f"View '{name}' not found."
            )

        del self._views[name]

    def get_view(
        self,
        name: str,
    ) -> View:

        if name not in self._views:
            raise ViewNotFoundError(
                f"View '{name}' not found."
            )

        return self._views[name]

    def views(self) -> list[View]:
        return list(self._views.values())

    def set_window(
        self,
        window: Window,
    ) -> None:
        self._window = window

    def get_window(self) -> Window | None:
        return self._window

    def clear(self) -> None:
        self._views.clear()
        self._window = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "window": (
                self._window.to_dict()
                if self._window
                else None
            ),
            "views": [
                view.to_dict()
                for view in self._views.values()
            ],
        }

    def __len__(self) -> int:
        return len(self._views)