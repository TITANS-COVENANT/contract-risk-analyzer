"""End-to-end analysis pipeline orchestration."""

from __future__ import annotations

import logging
from typing import List, Optional

from app.config import Settings, get_settings
from app.core.classifier import ClauseClassifier
from app.core.pdf_parser import PDFParseError, PDFParser
from app.core.risk_scorer import RiskScorer
from app.core.simplifier import ClauseSimplifier
from app.models.schemas import (
    AnalysisResponse,
    AnalysisSummary,
    ClauseResult,
    DocumentMetadata,
    RiskLevel,
)
from ml.labels import DISCLAIMER, METADATA_LABEL_NAMES

# Map metadata clause categories to DocumentMetadata field names.
_METADATA_FIELD_MAP = {
    "Document Name": "document_name",
    "Parties": "parties",
    "Agreement Date": "agreement_date",
    "Effective Date": "effective_date",
    "Expiration Date": "expiration_date",
    "Governing Law": "governing_law",
}

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrate parse → classify → score → simplify."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        classifier: Optional[ClauseClassifier] = None,
        simplifier: Optional[ClauseSimplifier] = None,
        parser: Optional[PDFParser] = None,
        scorer: Optional[RiskScorer] = None,
    ) -> None:
        """Wire pipeline components (injectable for tests)."""
        self.settings = settings or get_settings()
        self.parser = parser or PDFParser()
        self.classifier = classifier or ClauseClassifier(self.settings)
        self.scorer = scorer or RiskScorer()
        self.simplifier = simplifier or ClauseSimplifier(self.settings)

    def ensure_models_loaded(self) -> None:
        """Load heavy models if not already loaded."""
        if not self.classifier.is_loaded and not self.settings.skip_model_load:
            self.classifier.load()

    def analyze(self, pdf_bytes: bytes, filename: str) -> AnalysisResponse:
        """Run full analysis for an uploaded PDF.

        Args:
            pdf_bytes: Raw PDF content (held only for this call).
            filename: Original upload filename for the response.

        Returns:
            AnalysisResponse ready for the API.

        Raises:
            PDFParseError: If the PDF cannot be parsed.
            ValueError: If validation fails (empty file, etc.).
        """
        if not pdf_bytes:
            raise ValueError("Uploaded file is empty.")

        notes: List[str] = []
        segments = self.parser.parse(pdf_bytes)
        if len(segments) > self.settings.max_segments:
            notes.append(
                f"Document truncated to first {self.settings.max_segments} segments "
                f"(found {len(segments)})."
            )
            segments = segments[: self.settings.max_segments]

        logger.info(
            "analysis_started segments=%d filename_len=%d",
            len(segments),
            len(filename or ""),
        )

        classifications = self.classifier.classify_many(segments)
        clauses: List[ClauseResult] = []
        metadata_candidates: dict[str, tuple[float, str]] = {}

        for index, (segment, classification) in enumerate(
            zip(segments, classifications),
            start=1,
        ):
            field_name = _METADATA_FIELD_MAP.get(classification.category)
            if field_name is not None:
                best = metadata_candidates.get(field_name)
                if best is None or classification.confidence > best[0]:
                    metadata_candidates[field_name] = (classification.confidence, segment)

            # Pure metadata categories (Document Name, Parties, dates) never
            # become risk clause cards — they only feed document_metadata.
            if classification.category in METADATA_LABEL_NAMES:
                continue

            assessment = self.scorer.score(classification.category, segment)
            # Always produce an explanation; the simplifier uses offline
            # fallbacks when no LLM key is configured or the call fails.
            simplification = self.simplifier.simplify(
                text=segment,
                category=classification.category,
                risk_level=assessment.risk_level.value,
            )

            clauses.append(
                ClauseResult(
                    id=index,
                    category=classification.category,
                    confidence=round(classification.confidence, 4),
                    risk_level=assessment.risk_level,
                    risk_reasons=assessment.reasons,
                    original_text=segment,
                    plain_english=simplification.plain_english,
                    suggested_alternative=simplification.suggested_alternative,
                    llm_available=simplification.available,
                )
            )

        document_metadata = DocumentMetadata(
            **{
                field: _truncate_metadata_value(value)
                for field, (_, value) in metadata_candidates.items()
            }
        )

        high = sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH)
        medium = sum(1 for c in clauses if c.risk_level == RiskLevel.MEDIUM)
        low = sum(1 for c in clauses if c.risk_level == RiskLevel.LOW)

        if not self.simplifier.is_configured:
            notes.append(
                "LLM key not configured — plain-English text uses offline fallbacks. "
                "Add XAI_API_KEY (or OPENAI_API_KEY / ANTHROPIC_API_KEY) to .env."
            )
        if not self.classifier.is_loaded:
            notes.append(
                "Legal-BERT model not loaded — classification uses keyword fallback. "
                f"{('Load error: ' + self.classifier.load_error) if self.classifier.load_error else ''}".strip()
            )

        logger.info(
            "analysis_completed clauses=%d high=%d medium=%d low=%d",
            len(clauses),
            high,
            medium,
            low,
        )

        return AnalysisResponse(
            filename=filename or "contract.pdf",
            disclaimer=DISCLAIMER,
            summary=AnalysisSummary(
                total_clauses=len(clauses),
                high=high,
                medium=medium,
                low=low,
            ),
            document_metadata=document_metadata,
            clauses=clauses,
            processing_notes=notes,
        )


def _truncate_metadata_value(text: str, max_chars: int = 240) -> str:
    """Keep Contract Overview fields short; full text stays in the clause list."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"
