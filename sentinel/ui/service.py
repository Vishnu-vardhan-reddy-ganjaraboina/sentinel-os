"""
Service layer for the Sentinel UI subsystem.
"""

from __future__ import annotations

from sentinel.ui.interfaces import View, Window
from sentinel.ui.manager import SentinelUIManager


class UIService:
    """
    High-level service for managing the Sentinel UI.
    """

    def __init__(
        self,
        manager: SentinelUIManager | None = None,
    ) -> None:
        self._manager = (
            manager if manager is not None else SentinelUIManager()
        )

    @property
    def manager(self) -> SentinelUIManager:
        return self._manager

    def add_view(
        self,
        view: View,
    ) -> None:
        self._manager.add_view(view)

    def remove_view(
        self,
        name: str,
    ) -> None:
        self._manager.remove_view(name)

    def get_view(
        self,
        name: str,
    ):
        return self._manager.get_view(name)

    def views(self):
        return self._manager.views()

    def set_window(
        self,
        window: Window,
    ) -> None:
        self._manager.set_window(window)

    def get_window(self):
        return self._manager.get_window()

    def clear(self) -> None:
        self._manager.clear()

    def to_dict(self):
        return self._manager.to_dict()

    def __len__(self) -> int:
        return len(self._manager)