from datetime import datetime, timezone

import pytest

from sentinel.control_plane.audit_query import ControlAuditQuery


def test_default_query() -> None:
    query = ControlAuditQuery()

    assert query.caller_id is None
    assert query.caller_type is None
    assert query.command is None
    assert query.success is None
    assert query.since is None
    assert query.until is None
    assert query.limit is None


def test_valid_query() -> None:
    timestamp = datetime.now(timezone.utc)

    query = ControlAuditQuery(
        caller_id="user-1",
        caller_type="user",
        command="service.start",
        success=True,
        since=timestamp,
        until=timestamp,
        limit=10,
    )

    assert query.caller_id == "user-1"
    assert query.command == "service.start"
    assert query.success is True
    assert query.limit == 10


@pytest.mark.parametrize(
    "kwargs",
    [
        {"caller_id": ""},
        {"caller_type": ""},
        {"command": ""},
        {"limit": 0},
        {"limit": -1},
    ],
)
def test_invalid_query_values(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        ControlAuditQuery(**kwargs)  # type: ignore[arg-type]


def test_naive_since_rejected() -> None:
    with pytest.raises(ValueError):
        ControlAuditQuery(
            since=datetime.now()
        )


def test_since_after_until_rejected() -> None:
    start = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    with pytest.raises(ValueError):
        ControlAuditQuery(
            since=start,
            until=end,
        )