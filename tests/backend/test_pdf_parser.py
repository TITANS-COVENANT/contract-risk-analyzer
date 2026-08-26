"""PDF parser tests using a generated fixture."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.core.pdf_parser import PDFParseError, PDFParser

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_contract.pdf"


def _ensure_fixture() -> Path:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    if FIXTURE.exists():
        return FIXTURE

    doc = fitz.open()
    page = doc.new_page()
    body = (
        "FREELANCE SERVICES AGREEMENT\n\n"
        "1. Indemnification. The Contractor shall indemnify and hold harmless the Client "
        "from any and all claims, damages, and expenses, including attorney fees, arising "
        "out of any act or omission of the Contractor in connection with the services "
        "provided under this Agreement. This obligation is unlimited and shall survive "
        "termination of this Agreement.\n\n"
        "2. Payment. Client shall pay Contractor within thirty (30) days of invoice. "
        "Late payments accrue interest at the maximum rate permitted by law.\n\n"
        "3. Confidentiality. Each party agrees to keep confidential information secret "
        "and not disclose it to third parties without prior written consent of the other party.\n\n"
        "4. Governing Law. This Agreement shall be governed by the laws of the State of Delaware.\n\n"
        "5. Intellectual Property. All work product created under this Agreement shall be "
        "the exclusive property of the Client as a work made for hire. Contractor hereby "
        "assigns all right, title, and interest in such work product to Client.\n\n"
        "6. Termination. Client may terminate this Agreement for convenience upon fifteen "
        "(15) days written notice without further obligation except for fees already earned.\n\n"
        "7. Non-Compete. During the term and for twelve (12) months thereafter, Contractor "
        "shall not engage in any competing business within the geographic markets served "
        "by Client.\n\n"
        "8. Limitation of Liability. In no event shall Client be liable for indirect, "
        "incidental, special, or consequential damages. Contractor's remedies are limited.\n"
    )
    # Repeat to approach segment word targets
    page.insert_text((50, 50), body * 2, fontsize=10)
    doc.save(FIXTURE)
    doc.close()
    return FIXTURE


def test_parse_sample_contract() -> None:
    path = _ensure_fixture()
    parser = PDFParser()
    segments = parser.parse(path.read_bytes())
    assert len(segments) >= 1
    joined = " ".join(segments).casefold()
    assert "indemnif" in joined


def test_empty_pdf_raises() -> None:
    parser = PDFParser()
    with pytest.raises(PDFParseError):
        parser.parse(b"not-a-pdf")
