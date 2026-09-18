"""
Audit events for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ControlAuditEvent:
    """
    Immutable record of a Control Plane request.

    An audit event records who requested an operation, what was
    requested, when it occurred, and whether the operation succeeded.
    """

    caller_id: str
    caller_type: str
    command: str
    success: bool
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    data: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.caller_id.strip():
            raise ValueError("caller_id must not be empty.")

        if not self.caller_type.strip():
            raise ValueError("caller_type must not be empty.")

        if not self.command.strip():
            raise ValueError("command must not be empty.")

        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if self.error is not None and not isinstance(self.error, str):
            raise TypeError("error must be a string or None.")

        if self.success and self.error is not None:
            raise ValueError(
                "Successful audit events cannot contain an error."
            )

        if not self.success and not self.error:
            raise ValueError(
                "Failed audit events must contain an error."
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware."
            )

        object.__setattr__(
            self,
            "data",
            dict(self.data),
        )


class ControlAuditRecorder:
    """
    Interface for recording Control Plane audit events.
    """

    def record(
        self,
        event: ControlAuditEvent,
    ) -> None:
        """
        Record an audit event.
        """
        raise NotImplementedError

class InMemoryControlAuditRecorder(ControlAuditRecorder):
    """
    Store Control Plane audit events in memory.

    This implementation is intended for testing and lightweight
    runtime usage. Persistent audit storage can be added later without
    changing the controller's audit interface.
    """

    def __init__(self) -> None:
        self._events: list[ControlAuditEvent] = []

    @property
    def events(self) -> tuple[ControlAuditEvent, ...]:
        """
        Return all recorded events.
        """
        return tuple(self._events)

    def record(
        self,
        event: ControlAuditEvent,
    ) -> None:
        """
        Record an audit event.
        """
        if not isinstance(event, ControlAuditEvent):
            raise TypeError(
                "event must be a ControlAuditEvent."
            )

        self._events.append(event)

    def clear(self) -> None:
        """
        Remove all recorded events.
        """
        self._events.clear()