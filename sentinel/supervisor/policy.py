from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RestartPolicy:
    """
    Define how supervised process recovery is performed.
    """

    enabled: bool = True
    max_restarts: int = 3
    backoff_seconds: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean.")

        if not isinstance(self.max_restarts, int):
            raise TypeError("max_restarts must be an integer.")

        if self.max_restarts < 0:
            raise ValueError(
                "max_restarts cannot be negative."
            )

        if not isinstance(self.backoff_seconds, (int, float)):
            raise TypeError(
                "backoff_seconds must be a number."
            )

        if self.backoff_seconds < 0:
            raise ValueError(
                "backoff_seconds cannot be negative."
            )