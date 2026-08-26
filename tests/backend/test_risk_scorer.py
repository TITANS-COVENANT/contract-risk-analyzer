"""Unit tests for the risk scorer (Judge layer)."""

from __future__ import annotations

from app.core.risk_scorer import RiskScorer
from app.models.schemas import RiskLevel


def test_indemnification_unlimited_is_high() -> None:
    scorer = RiskScorer()
    text = (
        "The Contractor shall indemnify and hold harmless the Client from any "
        "and all claims, damages, and expenses, including attorney fees, "
        "arising out of any act or omission of the Contractor, with unlimited liability."
    )
    result = scorer.score("Indemnification", text)
    assert result.risk_level == RiskLevel.HIGH
    assert any("unlimited" in r for r in result.reasons)


def test_governing_law_is_low_by_default() -> None:
    scorer = RiskScorer()
    text = (
        "This agreement shall be governed by and construed in accordance with "
        "the laws of the State of Delaware."
    )
    result = scorer.score("Governing Law", text)
    assert result.risk_level == RiskLevel.LOW


def test_termination_for_convenience_escalates() -> None:
    scorer = RiskScorer()
    text = "Client may terminate this agreement for convenience upon written notice."
    result = scorer.score("Termination for Convenience", text)
    assert result.risk_level in {RiskLevel.HIGH, RiskLevel.MEDIUM}


def test_uncapped_liability_is_high() -> None:
    scorer = RiskScorer()
    text = "Contractor's liability under this Agreement shall be unlimited and shall not be subject to any cap."
    result = scorer.score("Uncapped Liability", text)
    assert result.risk_level == RiskLevel.HIGH


def test_cap_on_liability_is_low_by_default() -> None:
    scorer = RiskScorer()
    text = "Total liability under this agreement shall not exceed the fees paid in the twelve months preceding the claim."
    result = scorer.score("Cap on Liability", text)
    assert result.risk_level == RiskLevel.LOW
