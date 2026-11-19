import pytest

from sentinel.brain.reasoning import EvidenceGroundedReasoner, ReasoningProvider


class FakeProvider(ReasoningProvider):
    def generate(self, question, evidence):
        return {
            "answer": f"Answer: {question}",
            "steps": ["Check evidence", "Explain result"],
            "assumptions": [],
            "requires_confirmation": True,
        }


def test_reasoner_passes_bounded_evidence_and_returns_structured_plan():
    reasoner = EvidenceGroundedReasoner(
        FakeProvider(), max_evidence=1, max_chars_per_item=4
    )
    result = reasoner.reason(
        "What next?", memories=["remembered"], knowledge=["ignored"]
    )
    assert result.answer == "Answer: What next?"
    assert result.steps == ("Check evidence", "Explain result")
    assert result.evidence[0].content == "reme"
    assert result.requires_confirmation


def test_reasoner_rejects_malformed_provider_output():
    class BadProvider(ReasoningProvider):
        def generate(self, question, evidence):
            return {"answer": "ok", "steps": "not a list"}

    with pytest.raises(ValueError, match="steps"):
        EvidenceGroundedReasoner(BadProvider()).reason("test")
