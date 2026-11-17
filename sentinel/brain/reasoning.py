"""Evidence-grounded reasoning orchestration with a pluggable model provider.

The coordinator never executes capabilities. Provider output is treated as
untrusted data and validated before it is returned to the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReasoningEvidence:
    source: str
    content: str
    reference: str | None = None


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    answer: str
    steps: tuple[str, ...]
    assumptions: tuple[str, ...]
    evidence: tuple[ReasoningEvidence, ...]
    requires_confirmation: bool


class ReasoningProvider(ABC):
    @abstractmethod
    def generate(
        self, question: str, evidence: tuple[ReasoningEvidence, ...]
    ) -> dict[str, Any]:
        """Return structured output; implementations may use a local or remote LLM."""


class EvidenceGroundedReasoner:
    """Collect bounded local evidence and validate provider output."""

    def __init__(
        self,
        provider: ReasoningProvider,
        *,
        max_evidence: int = 12,
        max_chars_per_item: int = 2_000,
    ) -> None:
        if (
            isinstance(max_evidence, bool)
            or not isinstance(max_evidence, int)
            or max_evidence < 1
        ):
            raise ValueError("max_evidence must be a positive integer")
        if (
            isinstance(max_chars_per_item, bool)
            or not isinstance(max_chars_per_item, int)
            or max_chars_per_item < 1
        ):
            raise ValueError("max_chars_per_item must be a positive integer")
        self.provider = provider
        self.max_evidence = max_evidence
        self.max_chars_per_item = max_chars_per_item

    def reason(
        self,
        question: str,
        *,
        memories: list[Any] | None = None,
        knowledge: list[Any] | None = None,
    ) -> ReasoningResult:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be non-empty")
        evidence: list[ReasoningEvidence] = []
        for source, items in (
            ("memory", memories or []),
            ("knowledge", knowledge or []),
        ):
            for item in items:
                if len(evidence) >= self.max_evidence:
                    break
                content = (
                    item if isinstance(item, str) else getattr(item, "content", None)
                )
                if content is None and hasattr(item, "label"):
                    content = item.label
                if isinstance(content, (str, int, float, bool)):
                    reference = getattr(item, "id", None) or getattr(
                        item, "node_id", None
                    )
                    evidence.append(
                        ReasoningEvidence(
                            source,
                            str(content)[: self.max_chars_per_item],
                            str(reference) if reference is not None else None,
                        )
                    )
        raw = self.provider.generate(question.strip(), tuple(evidence))
        if not isinstance(raw, dict):
            raise TypeError("reasoning provider must return a dictionary")
        answer = raw.get("answer")
        steps = raw.get("steps", [])
        assumptions = raw.get("assumptions", [])
        confirmation = raw.get("requires_confirmation", False)
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("reasoning provider returned an invalid answer")
        if not isinstance(steps, list) or any(
            not isinstance(step, str) or not step.strip() for step in steps
        ):
            raise ValueError("reasoning steps must be a list of non-empty strings")
        if not isinstance(assumptions, list) or any(
            not isinstance(item, str) for item in assumptions
        ):
            raise ValueError("reasoning assumptions must be a list of strings")
        if not isinstance(confirmation, bool):
            raise ValueError("requires_confirmation must be a boolean")
        return ReasoningResult(
            answer.strip(),
            tuple(steps),
            tuple(assumptions),
            tuple(evidence),
            confirmation,
        )
