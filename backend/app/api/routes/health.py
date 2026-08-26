"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app import __version__
from app.config import get_settings
from app.models.schemas import HealthResponse
from ml.labels import LABEL_NAMES

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Return service liveness and model/LLM configuration status."""
    settings = get_settings()
    pipeline = getattr(request.app.state, "pipeline", None)
    model_loaded = bool(
        pipeline is not None and pipeline.classifier.is_loaded
    )
    fine_tuned = bool(
        pipeline is not None and pipeline.classifier.is_fine_tuned
    )
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        fine_tuned=fine_tuned,
        classifier_labels=len(LABEL_NAMES),
        llm_configured=settings.has_llm_key(),
        llm_provider=settings.llm_provider,
        version=__version__,
    )
