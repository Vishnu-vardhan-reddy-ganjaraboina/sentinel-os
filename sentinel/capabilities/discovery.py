"""Deterministic discovery of registered Sentinel capabilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from sentinel.capabilities.manager import CapabilityManager


class DiscoveryStatus(StrEnum):
    """Outcome of a capability discovery query."""

    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNMATCHED = "unmatched"


@dataclass(frozen=True, slots=True)
class CapabilityCandidate:
    """A capability ranked for a request."""

    capability_id: str
    name: str
    score: float


@dataclass(frozen=True, slots=True)
class CapabilityDiscoveryResult:
    """Discovery outcome and its highest-ranked candidates."""

    status: DiscoveryStatus
    candidate: CapabilityCandidate | None
    candidates: tuple[CapabilityCandidate, ...]


class CapabilityDiscovery:
    """Rank capabilities without executing or authorizing them."""

    MINIMUM_SCORE = 0.6
    AMBIGUITY_MARGIN = 0.15
    MAX_CANDIDATES = 5

    _STOP_WORDS = frozenset(
        {
            "a", "an", "and", "are", "as", "at", "be", "by",
            "can", "do", "for", "from", "how", "i", "in",
            "is", "it", "me", "of", "on", "or", "please",
            "show", "the", "to", "what", "with", "you",
        }
    )

    def __init__(self, capabilities: CapabilityManager) -> None:
        if not isinstance(capabilities, CapabilityManager):
            raise TypeError(
                "capabilities must be a CapabilityManager."
            )
        self._capabilities = capabilities

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {
            word
            for word in re.findall(r"[a-z0-9]+", text.lower())
            if len(word) > 2 and word not in cls._STOP_WORDS
        }

    @classmethod
    def _score(
        cls,
        request_tokens: set[str],
        name: str,
        tags: list[str],
        description: str,
    ) -> float:
        if not request_tokens:
            return 0.0

        name_tokens = cls._tokens(name)
        tag_tokens = cls._tokens(" ".join(tags))
        description_tokens = cls._tokens(description)

        matched_weight = sum(
            max(
                3 if token in name_tokens else 0,
                2 if token in tag_tokens else 0,
                1 if token in description_tokens else 0,
            )
            for token in request_tokens
        )
        return matched_weight / (3 * len(request_tokens))

    def discover(self, request: str) -> CapabilityDiscoveryResult:
        """Rank enabled capabilities for a request without running them."""
        if not isinstance(request, str):
            raise TypeError("request must be a string.")

        request_tokens = self._tokens(request)
        if not request_tokens:
            return CapabilityDiscoveryResult(
                DiscoveryStatus.UNMATCHED, None, ()
            )

        ranked: list[CapabilityCandidate] = []

        for capability in self._capabilities.list():
            metadata = capability.metadata
            if not metadata.enabled:
                continue

            score = self._score(
                request_tokens,
                metadata.name,
                metadata.tags,
                metadata.description,
            )
            if score > 0:
                ranked.append(
                    CapabilityCandidate(
                        capability_id=metadata.capability_id,
                        name=metadata.name,
                        score=score,
                    )
                )

        ranked.sort(key=lambda item: (-item.score, item.capability_id))
        candidates = tuple(ranked[: self.MAX_CANDIDATES])

        if not candidates or candidates[0].score < self.MINIMUM_SCORE:
            return CapabilityDiscoveryResult(
                DiscoveryStatus.UNMATCHED, None, candidates
            )

        if (
            len(candidates) > 1
            and candidates[0].score - candidates[1].score
            < self.AMBIGUITY_MARGIN
        ):
            return CapabilityDiscoveryResult(
                DiscoveryStatus.AMBIGUOUS, None, candidates
            )

        return CapabilityDiscoveryResult(
            DiscoveryStatus.MATCHED, candidates[0], candidates
        )
