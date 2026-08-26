"""FastAPI application entrypoint for the Contract Clause Risk Analyzer."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import analyze, health
from app.config import get_settings
from app.core.pipeline import AnalysisPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create pipeline and optionally warm the classifier model."""
    settings = get_settings()
    pipeline = AnalysisPipeline(settings=settings)
    app.state.pipeline = pipeline
    app.state.settings = settings

    if not settings.skip_model_load:
        try:
            pipeline.ensure_models_loaded()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Model warm-up failed (keyword fallback active): %s",
                type(exc).__name__,
            )
    else:
        logger.info("Model warm-up skipped (SKIP_MODEL_LOAD=true)")

    logger.info(
        "App started version=%s llm_provider=%s llm_configured=%s",
        __version__,
        settings.llm_provider,
        settings.has_llm_key(),
    )
    yield
    # No persistent resources to tear down; contract data is request-scoped.


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title="Contract Clause Risk Analyzer",
        description=(
            "AI-powered contract clause risk detection and plain-English "
            "simplification for freelancers and SMEs. "
            "Output is legal information, not legal advice."
        ),
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(analyze.router, prefix="/api")
    return app


app = create_app()
