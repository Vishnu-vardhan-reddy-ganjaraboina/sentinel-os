"""
Persistent storage contracts for Sentinel Control Plane audit events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel.control_plane.audit import ControlAuditEvent

from sentinel.control_plane.audit_query import ControlAuditQuery


class ControlAuditStore(ABC):
    """
    Persistent storage interface for Control Plane audit events.
    """

    @abstractmethod
    def append(self, event: ControlAuditEvent) -> None:
        """
        Persist one audit event.
        """
        raise NotImplementedError

    @abstractmethod
    def events(self) -> tuple[ControlAuditEvent, ...]:
        """
        Return all persisted audit events in chronological order.
        """
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        query: ControlAuditQuery,
    ) -> tuple[ControlAuditEvent, ...]:
        """
        Return audit events matching the supplied query.
        """
        raise NotImplementedError