"""Pydantic request and response models for the API."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Discrete risk levels returned by the Judge layer."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = "ok"
    model_loaded: bool = False
    fine_tuned: bool = False
    classifier_labels: int = 0
    llm_configured: bool = False
    llm_provider: str = "xai"
    version: str = "0.1.0"


class DocumentMetadata(BaseModel):
    """Document-level facts extracted from metadata-kind clause categories."""

    document_name: Optional[str] = None
    parties: Optional[str] = None
    agreement_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    governing_law: Optional[str] = None


class ClauseResult(BaseModel):
    """A single analyzed clause segment."""

    id: int
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    risk_reasons: List[str] = Field(default_factory=list)
    original_text: str
    plain_english: str = ""
    suggested_alternative: str = ""
    llm_available: bool = False


class AnalysisSummary(BaseModel):
    """Aggregate risk counts for a document."""

    total_clauses: int
    high: int
    medium: int
    low: int


class AnalysisResponse(BaseModel):
    """Full analysis response for an uploaded contract."""

    filename: str
    disclaimer: str
    summary: AnalysisSummary
    document_metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    clauses: List[ClauseResult]
    processing_notes: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
    code: Optional[str] = None
