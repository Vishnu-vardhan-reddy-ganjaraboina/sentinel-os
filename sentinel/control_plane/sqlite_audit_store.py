"""
SQLite persistence for Sentinel Control Plane audit events.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock

from sentinel.control_plane.audit import ControlAuditEvent
from sentinel.control_plane.audit_store import ControlAuditStore


class SQLiteControlAuditStore(ControlAuditStore):
    """
    Persist Control Plane audit events in SQLite.
    """

    def __init__(self, database: str | Path) -> None:
        self._database = Path(database)
        self._connection: sqlite3.Connection | None = None
        self._lock = RLock()

        self._database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connect()

    def connect(self) -> None:
        """
        Open the database and initialize the audit schema.
        """
        with self._lock:
            if self._connection is not None:
                return

            connection = sqlite3.connect(
                self._database,
                check_same_thread=False,
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS control_audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    caller_id TEXT NOT NULL,
                    caller_type TEXT NOT NULL,
                    command TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    error TEXT
                )
                """
            )

            connection.commit()
            self._connection = connection

    def disconnect(self) -> None:
        """
        Close the database connection.
        """
        with self._lock:
            if self._connection is None:
                return

            self._connection.close()
            self._connection = None

    def close(self) -> None:
        """
        Close the database connection.
        """
        self.disconnect()

    def append(self, event: ControlAuditEvent) -> None:
        """
        Persist one audit event.
        """
        if not isinstance(event, ControlAuditEvent):
            raise TypeError(
                "event must be a ControlAuditEvent."
            )

        with self._lock:
            connection = self._ensure_connected()

            connection.execute(
                """
                INSERT INTO control_audit_events (
                    timestamp,
                    caller_id,
                    caller_type,
                    command,
                    success,
                    data,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp.isoformat(),
                    event.caller_id,
                    event.caller_type,
                    event.command,
                    int(event.success),
                    json.dumps(dict(event.data)),
                    event.error,
                ),
            )

            connection.commit()

    def events(self) -> tuple[ControlAuditEvent, ...]:
        """
        Return persisted audit events in chronological order.
        """
        with self._lock:
            connection = self._ensure_connected()

            cursor = connection.execute(
                """
                SELECT
                    timestamp,
                    caller_id,
                    caller_type,
                    command,
                    success,
                    data,
                    error
                FROM control_audit_events
                ORDER BY id ASC
                """
            )

            rows = cursor.fetchall()

        return tuple(
            self._event_from_row(row)
            for row in rows
        )

    def _ensure_connected(self) -> sqlite3.Connection:
        """
        Return the active database connection.
        """
        if self._connection is None:
            raise RuntimeError(
                "SQLite audit store is not connected."
            )

        return self._connection

    @staticmethod
    def _event_from_row(
        row: tuple[object, ...],
    ) -> ControlAuditEvent:
        """
        Reconstruct an audit event from a database row.
        """
        (
            timestamp,
            caller_id,
            caller_type,
            command,
            success,
            data,
            error,
        ) = row

        return ControlAuditEvent(
            timestamp=datetime.fromisoformat(str(timestamp)),
            caller_id=str(caller_id),
            caller_type=str(caller_type),
            command=str(command),
            success=bool(success),
            data=json.loads(str(data)),
            error=None if error is None else str(error),
        )