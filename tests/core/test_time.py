from datetime import UTC, datetime

from sentinel.core.time import (
    ensure_utc,
    now_utc,
    timestamp,
)


def test_now_utc() -> None:
    value = now_utc()

    assert isinstance(value, datetime)
    assert value.tzinfo == UTC


def test_ensure_utc_with_utc_datetime() -> None:
    value = datetime(2026, 1, 1, tzinfo=UTC)

    result = ensure_utc(value)

    assert result == value
    assert result.tzinfo == UTC


def test_ensure_utc_with_naive_datetime() -> None:
    value = datetime(2026, 1, 1)

    result = ensure_utc(value)

    assert result.tzinfo == UTC
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 1


def test_timestamp() -> None:
    value = datetime(2026, 1, 1, tzinfo=UTC)

    result = timestamp(value)

    assert result == "2026-01-01T00:00:00+00:00"