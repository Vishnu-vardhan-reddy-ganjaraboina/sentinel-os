from __future__ import annotations

from typing import Any

from sentinel.brain.intent_resolver import DefaultIntentResolver
from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata


class ResolverDiscoveryCapability(BaseCapability):
    """Capability that records whether its run method was called."""

    def __init__(
        self,
        capability_id: str,
        name: str,
        input_schema: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id=capability_id,
                name=name,
                description="Handles database query requests.",
                category=CapabilityCategory.CUSTOM,
                input_schema=input_schema or {},
                tags=tags or [],
            )
        )
        self.run_called = False

    def run(self, **kwargs: Any) -> dict[str, Any]:
        self.run_called = True
        return dict(kwargs)


def make_resolver(
    *capabilities: ResolverDiscoveryCapability,
) -> tuple[DefaultIntentResolver, list[ResolverDiscoveryCapability]]:
    manager = CapabilityManager()
    for capability in capabilities:
        manager.register(capability)
    return DefaultIntentResolver(capabilities=manager), list(capabilities)


def test_high_confidence_match_is_selected() -> None:
    capability = ResolverDiscoveryCapability(
        "database.query",
        "Database Query",
    )
    resolver, _ = make_resolver(capability)

    intent = resolver.resolve("database query")

    assert intent.capability_id == "database.query"
    assert dict(intent.arguments) == {}
    discovery = intent.context["capability_discovery"]
    assert discovery["selected"] is True
    assert discovery["selection_reason"] == "eligible"


def test_capability_requiring_arguments_is_not_selected() -> None:
    capability = ResolverDiscoveryCapability(
        "database.query",
        "Database Query",
        input_schema={
            "type": "object",
            "properties": {"table": {"type": "string"}},
            "required": ["table"],
            "additionalProperties": False,
        },
    )
    resolver, _ = make_resolver(capability)

    intent = resolver.resolve("database query")

    assert intent.capability_id == "database.query"
    discovery = intent.context["capability_discovery"]
    assert discovery["selected"] is False
    assert discovery["selection_reason"] == "needs_clarification"
    assert discovery["missing_required_arguments"] == ["table"]


def test_ambiguous_match_is_not_selected() -> None:
    first = ResolverDiscoveryCapability(
        "database.alpha",
        "Database Query",
    )
    second = ResolverDiscoveryCapability(
        "database.beta",
        "Database Query",
    )
    resolver, _ = make_resolver(first, second)

    intent = resolver.resolve("database query")

    assert intent.capability_id is None
    discovery = intent.context["capability_discovery"]
    assert discovery["status"] == "ambiguous"
    assert discovery["selection_reason"] == "ambiguous"


def test_low_confidence_match_is_not_selected() -> None:
    capability = ResolverDiscoveryCapability(
        "database.query",
        "Database Query",
    )
    resolver, _ = make_resolver(capability)

    intent = resolver.resolve("database query report")

    assert intent.capability_id is None
    discovery = intent.context["capability_discovery"]
    assert discovery["selected"] is False
    assert (
        discovery["selection_reason"]
        == "below_confidence_threshold"
    )


def test_resolving_intent_never_executes_capability() -> None:
    capability = ResolverDiscoveryCapability(
        "database.query",
        "Database Query",
    )
    resolver, capabilities = make_resolver(capability)

    resolver.resolve("database query")

    assert all(not item.run_called for item in capabilities)


def test_resolver_without_discovery_preserves_default_behavior() -> None:
    resolver = DefaultIntentResolver()

    intent = resolver.resolve("database query")

    assert intent.capability_id is None
    assert dict(intent.arguments) == {}
    assert dict(intent.context) == {}
