"""Classifier tests using keyword fallback (no model download)."""

from __future__ import annotations

from app.config import Settings
from app.core.classifier import ClauseClassifier


def test_keyword_indemnification() -> None:
    settings = Settings(skip_model_load=True)
    clf = ClauseClassifier(settings=settings)
    text = (
        "The Contractor shall indemnify and hold harmless the Client from any "
        "and all claims and attorney fees arising out of the Contractor's work."
    )
    result = clf.classify(text)
    assert result.category == "Indemnification"
    assert result.confidence >= 0.35


def test_empty_text_unknown() -> None:
    settings = Settings(skip_model_load=True)
    clf = ClauseClassifier(settings=settings)
    result = clf.classify("   ")
    assert result.category == "Unknown"
