"""
Data models for the Sentinel logging runtime.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

from sentinel.logging.enums import LogLevel


class LogContext(Mapping[str, Any]):
    """
    Immutable contextual data attached to a log record.
    """

    __slots__ = ("_values",)

    def __init__(
        self,
        values: Mapping[str, Any] | None = None,
    ) -> None:
        self._values = MappingProxyType(dict(values or {}))

    @classmethod
    def empty(cls) -> LogContext:
        """
        Return an empty logging context.
        """
        return cls()

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Any],
    ) -> LogContext:
        """
        Create a logging context from a mapping.
        """
        return cls(mapping)

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"LogContext({dict(self._values)!r})"


__all__ = (
    "LogContext",
    "LogMetadata",
    "LogRecord",
)

@dataclass(slots=True, frozen=True)
class LogMetadata:
    """
    Metadata describing the source of a log record.
    """

    process_id: int = 0
    thread_id: int = 0
    module: str = ""
    function: str = ""
    line_number: int = 0


@dataclass(slots=True, frozen=True)
class LogRecord:
    """
    Immutable representation of a single log event.
    """

    timestamp: datetime
    level: LogLevel
    logger: str
    message: str
    context: LogContext = field(
        default_factory=LogContext.empty,
    )
    metadata: LogMetadata = field(
        default_factory=LogMetadata,
    )