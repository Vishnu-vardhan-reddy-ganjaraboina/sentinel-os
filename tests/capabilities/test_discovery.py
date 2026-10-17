from __future__ import annotations

import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.discovery import (
    CapabilityDiscovery,
    DiscoveryStatus,
)
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata


class DiscoveryTestCapability(BaseCapability):
    """A capability used to test discovery without side effects."""

    def __init__(
        self,
        capability_id: str,
        name: str,
        description: str = "Performs a test operation.",
        tags: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id=capability_id,
                name=name,
                description=description,
                category=CapabilityCategory.CUSTOM,
                tags=tags or [],
                enabled=enabled,
            )
        )
        self.run_called = False

    def run(self, **kwargs: object) -> dict[str, object]:
        self.run_called = True
        return dict(kwargs)


def make_discovery(
    *capabilities: DiscoveryTestCapability,
) -> tuple[CapabilityDiscovery, list[DiscoveryTestCapability]]:
    manager = CapabilityManager()
    for capability in capabilities:
        manager.register(capability)
    return CapabilityDiscovery(manager), list(capabilities)


def test_discovery_ranks_matching_capability() -> None:
    database = DiscoveryTestCapability(
        "database.query",
        "Database Query",
        "Run SQL database queries",
        ["sql", "database"],
    )
    filesystem = DiscoveryTestCapability(
        "filesystem.read",
        "Read File",
        "Read a local document",
        ["file", "read"],
    )
    discovery, capabilities = make_discovery(database, filesystem)

    result = discovery.discover("run a database query")

    assert result.status == DiscoveryStatus.MATCHED
    assert result.candidate is not None
    assert result.candidate.capability_id == "database.query"
    assert result.candidates[0].score >= 0.6
    assert all(not capability.run_called for capability in capabilities)


def test_disabled_capability_is_not_a_candidate() -> None:
    disabled = DiscoveryTestCapability(
        "database.disabled",
        "Database Query",
        "Run SQL database queries",
        ["database", "query"],
        enabled=False,
    )
    discovery, _ = make_discovery(disabled)

    result = discovery.discover("database query")

    assert result.status == DiscoveryStatus.UNMATCHED
    assert result.candidate is None
    assert result.candidates == ()


def test_equal_matches_are_ambiguous_and_unselected() -> None:
    first = DiscoveryTestCapability(
        "database.alpha",
        "Database Query",
        "Run SQL database queries",
        ["database", "query"],
    )
    second = DiscoveryTestCapability(
        "database.beta",
        "Database Query",
        "Run SQL database queries",
        ["database", "query"],
    )
    discovery, _ = make_discovery(first, second)

    result = discovery.discover("database query")

    assert result.status == DiscoveryStatus.AMBIGUOUS
    assert result.candidate is None
    assert [item.capability_id for item in result.candidates] == [
        "database.alpha",
        "database.beta",
    ]


def test_irrelevant_request_is_unmatched() -> None:
    capability = DiscoveryTestCapability(
        "filesystem.read",
        "Read File",
        "Read a local document",
        ["file", "read"],
    )
    discovery, _ = make_discovery(capability)

    result = discovery.discover("calculate galaxy orbit")

    assert result.status == DiscoveryStatus.UNMATCHED
    assert result.candidate is None


@pytest.mark.parametrize("user_input", ["", "   ", "to be or", "!!!"])
def test_request_without_searchable_tokens_is_unmatched(
    user_input: str,
) -> None:
    capability = DiscoveryTestCapability(
        "database.query",
        "Database Query",
        "Run SQL database queries",
        ["database", "query"],
    )
    discovery, _ = make_discovery(capability)

    result = discovery.discover(user_input)

    assert result.status == DiscoveryStatus.UNMATCHED
    assert result.candidate is None


def test_discovery_rejects_non_string_request() -> None:
    discovery, _ = make_discovery()

    with pytest.raises(TypeError, match="request must be a string"):
        discovery.discover(123)  # type: ignore[arg-type]
