"""API integration tests with model loading skipped and LLM offline."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

# Ensure skip model load before app import side effects in tests.
import os

os.environ["SKIP_MODEL_LOAD"] = "true"
os.environ["LLM_PROVIDER"] = "xai"
os.environ["XAI_API_KEY"] = ""

from app.config import get_settings
from app.main import create_app

get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "SERVICE AGREEMENT\n\n"
        "Indemnification. Contractor shall indemnify and hold harmless Client from any "
        "and all claims and attorney fees with unlimited liability for Contractor acts.\n\n"
        "Payment Terms. Invoices are due net 30. Late fees may apply.\n\n"
        "Governing Law. This agreement is governed by the laws of Ghana.\n"
    )
    page.insert_text((72, 72), text * 3, fontsize=11)
    doc.save(path)
    doc.close()
    return path


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["llm_configured"] is False
    assert data["fine_tuned"] is False
    assert data["classifier_labels"] == 48


def test_analyze_pdf(client: TestClient, sample_pdf: Path) -> None:
    with sample_pdf.open("rb") as handle:
        response = client.post(
            "/api/analyze",
            files={"file": ("sample.pdf", handle, "application/pdf")},
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"]["total_clauses"] >= 1
    assert "disclaimer" in data
    assert "document_metadata" in data
    assert len(data["clauses"]) >= 1
    assert data["clauses"][0]["risk_level"] in {"HIGH", "MEDIUM", "LOW"}
    assert all(
        clause["category"] != "Document Name" and clause["category"] != "Parties"
        for clause in data["clauses"]
    )


def test_reject_non_pdf(client: TestClient) -> None:
    response = client.post(
        "/api/analyze",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
