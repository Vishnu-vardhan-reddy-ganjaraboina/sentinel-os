"""
View implementation for the Sentinel UI subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.ui.constants import ViewState
from sentinel.ui.interfaces import View


class UIView(View):
    """
    Default implementation of a UI view.
    """

    def __init__(
        self,
        name: str,
    ) -> None:

        if not name:
            raise ValueError("name cannot be empty")

        self._name = name
        self._state = ViewState.CREATED

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> ViewState:
        return self._state

    def show(self) -> None:
        self._state = ViewState.ACTIVE

    def hide(self) -> None:
        self._state = ViewState.HIDDEN

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
        }

    def __repr__(self) -> str:
        return (
            f"UIView("
            f"name={self.name!r}, "
            f"state={self.state.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UIView):
            return False

        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)