"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of backend/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for the Contract Clause Risk Analyzer backend."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", Path(".env"), Path("../.env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: Literal["xai", "openai", "anthropic", "groq"] = "xai"
    llm_model: str = "grok-4.5"
    xai_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # Models
    model_path: str = "nlpaueb/legal-bert-base-uncased"
    fine_tuned_model_path: str = ""
    hf_token: str = ""
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    max_segments: int = Field(default=100, ge=1, le=500)
    max_upload_mb: int = Field(default=15, ge=1, le=50)

    # App
    frontend_url: str = "http://localhost:3000"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    skip_model_load: bool = False

    @property
    def max_upload_bytes(self) -> int:
        """Maximum accepted upload size in bytes."""
        return self.max_upload_mb * 1024 * 1024

    def llm_api_key(self) -> str:
        """Return the API key for the configured LLM provider."""
        if self.llm_provider == "xai":
            return self.xai_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "groq":
            return self.groq_api_key
        return self.anthropic_api_key

    def has_llm_key(self) -> bool:
        """Return True when an LLM API key is configured."""
        return bool(self.llm_api_key().strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
