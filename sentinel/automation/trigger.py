"""
Base implementation of a Sentinel workflow trigger.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from sentinel.automation.interfaces import Trigger


class BaseTrigger(Trigger):
    """
    Base implementation for Sentinel triggers.

    Concrete triggers should inherit from this class and implement
    the `check()` method.
    """

    def __init__(
        self,
        trigger_id: str,
        enabled: bool = True,
    ) -> None:
        if not trigger_id.strip():
            raise ValueError("trigger_id cannot be empty.")

        self._id = trigger_id
        self._enabled = enabled

    @property
    def id(self) -> str:
        return self._id

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def evaluate(
        self,
        **kwargs: Any,
    ) -> bool:
        """
        Evaluate the trigger.

        Disabled triggers never fire.
        """
        if not self.enabled:
            return False

        return self.check(**kwargs)

    @abstractmethod
    def check(
        self,
        **kwargs: Any,
    ) -> bool:
        """
        Concrete trigger evaluation.
        """