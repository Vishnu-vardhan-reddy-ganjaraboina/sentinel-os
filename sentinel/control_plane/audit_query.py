"""
Query model for Sentinel Control Plane audit events.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ControlAuditQuery:
    """
    Filters for querying Control Plane audit events.
    """

    caller_id: str | None = None
    caller_type: str | None = None
    command: str | None = None
    success: bool | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.caller_id is not None:
            if not isinstance(self.caller_id, str):
                raise TypeError("caller_id must be a string or None.")
            if not self.caller_id.strip():
                raise ValueError(
                    "caller_id cannot be empty."
                )

        if self.caller_type is not None:
            if not isinstance(self.caller_type, str):
                raise TypeError(
                    "caller_type must be a string or None."
                )
            if not self.caller_type.strip():
                raise ValueError(
                    "caller_type cannot be empty."
                )

        if self.command is not None:
            if not isinstance(self.command, str):
                raise TypeError(
                    "command must be a string or None."
                )
            if not self.command.strip():
                raise ValueError(
                    "command cannot be empty."
                )

        if self.success is not None:
            if not isinstance(self.success, bool):
                raise TypeError(
                    "success must be a boolean or None."
                )

        if self.since is not None:
            self._validate_timestamp(self.since, "since")

        if self.until is not None:
            self._validate_timestamp(self.until, "until")

        if (
            self.since is not None
            and self.until is not None
            and self.since > self.until
        ):
            raise ValueError(
                "since cannot be later than until."
            )

        if self.limit is not None:
            if not isinstance(self.limit, int):
                raise TypeError(
                    "limit must be an integer or None."
                )

            if self.limit <= 0:
                raise ValueError(
                    "limit must be greater than zero."
                )

    @staticmethod
    def _validate_timestamp(
        value: datetime,
        name: str,
    ) -> None:
        if not isinstance(value, datetime):
            raise TypeError(
                f"{name} must be a datetime or None."
            )

        if value.tzinfo is None:
            raise ValueError(
                f"{name} must be timezone-aware."
            )