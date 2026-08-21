"""
Time utilities for Sentinel OS.
"""

from __future__ import annotations

from datetime import UTC, datetime


def now_utc() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """
    Return a UTC-aware datetime.

    Naive datetimes are interpreted as UTC.
    Timezone-aware datetimes are converted to UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def timestamp(value: datetime) -> str:
    """
    Return a UTC datetime as an ISO-8601 timestamp.
    """
    return ensure_utc(value).isoformat()