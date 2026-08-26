"""Contract analysis endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.config import get_settings
from app.core.pdf_parser import PDFParseError
from app.models.schemas import AnalysisResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analyze"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def analyze_contract(
    request: Request,
    file: UploadFile = File(..., description="PDF contract to analyze"),
) -> AnalysisResponse:
    """Upload a PDF contract and return clause risk analysis.

    Contract bytes are processed in memory only for this request and are not
    persisted to disk or a database.
    """
    settings = get_settings()
    filename = file.filename or "contract.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        # Some browsers send empty or generic types; only hard-fail clear mismatches.
        if "pdf" not in content_type and content_type not in {
            "application/octet-stream",
            "",
        }:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type: {content_type}",
            )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(pdf_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File exceeds maximum size of {settings.max_upload_mb} MB."
            ),
        )

    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=500,
            detail="Analysis pipeline is not initialized.",
        )

    try:
        # Ensure models are loaded (no-op if already loaded or skipped).
        pipeline.ensure_models_loaded()
        result = pipeline.analyze(pdf_bytes, filename)
    except PDFParseError as exc:
        logger.info("pdf_parse_failed reason=%s", type(exc).__name__)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("analysis_failed error_type=%s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Analysis failed due to an internal error.",
        ) from exc
    finally:
        # Drop reference promptly; GC will reclaim request-scoped bytes.
        pdf_bytes = b""

    return result
