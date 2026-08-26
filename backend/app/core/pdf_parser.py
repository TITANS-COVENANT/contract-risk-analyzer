"""PDF parsing utilities for contract analysis."""

from __future__ import annotations

import logging
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import List, Sequence

import fitz

logger = logging.getLogger(__name__)

MIN_SEGMENT_WORDS = 200
MAX_SEGMENT_WORDS = 400
TARGET_SEGMENT_WORDS = 300
HEADER_FOOTER_MAX_WORDS = 10
HEADER_FOOTER_MAX_CHARS = 80
HEADER_FOOTER_MIN_OCCURRENCES = 2

_PUNCTUATION_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u2032": "'",
        "\u2035": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u2022": "-",
        "\u00b7": "-",
        "\u2043": "-",
        "\u00a0": " ",
        "\u2007": " ",
        "\u202f": " ",
    }
)


class PDFParseError(Exception):
    """Raised when a PDF cannot be parsed into extractable contract text."""


class PDFParser:
    """Extract paragraph-preserving text segments from PDF bytes."""

    __slots__ = ()

    def parse(self, pdf_bytes: bytes) -> List[str]:
        """Parse PDF bytes into cleaned text segments.

        The parser preserves paragraph text, removes page numbers and repeating
        short headers or footers, and groups the result into segments that are
        intended to stay within a 200 to 400 word window.

        Args:
            pdf_bytes: Raw PDF file bytes.

        Returns:
            A list of cleaned text segments.

        Raises:
            PDFParseError: If the PDF is encrypted, corrupted, or contains no
                extractable text.
        """
        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
        except (fitz.EmptyFileError, fitz.FileDataError, ValueError, RuntimeError) as exc:
            raise PDFParseError("PDF is corrupted or invalid.") from exc

        try:
            if document.page_count == 0:
                raise PDFParseError("PDF is corrupted or invalid.")

            if getattr(document, "is_encrypted", False) or getattr(document, "needs_pass", False):
                raise PDFParseError("PDF is encrypted or password-protected.")

            page_lines: List[List[str]] = []
            for page_index in range(document.page_count):
                try:
                    page = document.load_page(page_index)
                    page_text = page.get_text("text")
                except (fitz.FileDataError, ValueError, RuntimeError) as exc:
                    raise PDFParseError("PDF is corrupted or invalid.") from exc

                lines = self._extract_lines(page_text)
                page_lines.append(lines)

            header_footer_lines = self._detect_repeating_header_footer_lines(page_lines)

            paragraphs = self._extract_paragraphs(page_lines, header_footer_lines)
            if not paragraphs:
                raise PDFParseError("PDF has no extractable text.")

            segments = self._segment_paragraphs(paragraphs)
            if not segments:
                raise PDFParseError("PDF has no extractable text.")

            return segments
        finally:
            document.close()

    @staticmethod
    def _extract_lines(page_text: str) -> List[str]:
        """Normalize raw page text into non-empty lines."""
        normalized_text = PDFParser._normalize_unicode(page_text)
        lines = []
        for line in normalized_text.splitlines():
            cleaned = PDFParser._normalize_whitespace(line)
            if cleaned:
                lines.append(cleaned)
        return lines

    @staticmethod
    def _normalize_unicode(text: str) -> str:
        """Replace common Unicode punctuation with ASCII equivalents."""
        normalized = unicodedata.normalize("NFKC", text)
        return normalized.translate(_PUNCTUATION_TRANSLATION)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Collapse excessive whitespace into single spaces."""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        """Normalize text for header and footer matching."""
        return PDFParser._normalize_whitespace(PDFParser._normalize_unicode(text)).casefold()

    @staticmethod
    def _is_page_number_line(line: str) -> bool:
        """Return True when a line contains only a page number."""
        return bool(re.fullmatch(r"\d+", line))

    @staticmethod
    def _is_header_footer_candidate(line: str) -> bool:
        """Return True when a line is short enough to be considered a header or footer."""
        return len(line.split()) <= HEADER_FOOTER_MAX_WORDS and len(line) <= HEADER_FOOTER_MAX_CHARS

    def _detect_repeating_header_footer_lines(self, page_lines: Sequence[Sequence[str]]) -> set[str]:
        """Find repeated short lines that appear near the top or bottom of pages."""
        top_counts: Counter[str] = Counter()
        bottom_counts: Counter[str] = Counter()

        for lines in page_lines:
            content_lines = [
                line
                for line in lines
                if not self._is_page_number_line(line)
            ]
            if not content_lines:
                continue

            top_slice = content_lines[:2]
            bottom_slice = content_lines[-2:] if len(content_lines) > 1 else content_lines

            for line in top_slice:
                normalized = self._normalize_for_match(line)
                if self._is_header_footer_candidate(normalized):
                    top_counts[normalized] += 1

            for line in bottom_slice:
                normalized = self._normalize_for_match(line)
                if self._is_header_footer_candidate(normalized):
                    bottom_counts[normalized] += 1

        repeated = {
            line
            for line, count in top_counts.items()
            if count >= HEADER_FOOTER_MIN_OCCURRENCES
        }
        repeated.update(
            {
                line
                for line, count in bottom_counts.items()
                if count >= HEADER_FOOTER_MIN_OCCURRENCES
            }
        )
        return repeated

    def _extract_paragraphs(
        self,
        page_lines: Sequence[Sequence[str]],
        repeated_lines: set[str],
    ) -> List[str]:
        """Remove page scaffolding and return cleaned paragraph text."""
        paragraphs: List[str] = []

        for page_index, lines in enumerate(page_lines):
            cleaned_lines = [
                line
                for line in lines
                if not self._is_page_number_line(line)
            ]

            while cleaned_lines and self._normalize_for_match(cleaned_lines[0]) in repeated_lines:
                cleaned_lines.pop(0)

            while cleaned_lines and self._normalize_for_match(cleaned_lines[-1]) in repeated_lines:
                cleaned_lines.pop()

            if not cleaned_lines:
                logger.warning(
                    "No extractable text found on page %d after cleanup",
                    page_index + 1,
                )
                continue

            cleaned_text = "\n".join(cleaned_lines)
            for paragraph in re.split(r"\n\s*\n+", cleaned_text):
                normalized_paragraph = self._normalize_whitespace(
                    self._normalize_unicode(paragraph)
                )
                if normalized_paragraph:
                    paragraphs.append(normalized_paragraph)

        return paragraphs

    def _segment_paragraphs(self, paragraphs: Sequence[str]) -> List[str]:
        """Group paragraphs into paragraph-boundary segments."""
        segment_groups: List[List[str]] = []
        current_group: List[str] = []
        current_word_count = 0

        for paragraph in paragraphs:
            paragraph_word_count = len(paragraph.split())
            if not paragraph_word_count:
                continue

            if (
                current_group
                and current_word_count >= MIN_SEGMENT_WORDS
                and current_word_count + paragraph_word_count > MAX_SEGMENT_WORDS
            ):
                segment_groups.append(current_group)
                current_group = []
                current_word_count = 0

            current_group.append(paragraph)
            current_word_count += paragraph_word_count

        if current_group:
            segment_groups.append(current_group)

        self._merge_underfilled_segments(segment_groups)

        return [
            "\n\n".join(group).strip()
            for group in segment_groups
            if group
        ]

    def _merge_underfilled_segments(self, segment_groups: List[List[str]]) -> None:
        """Merge nearby short segments when that keeps the result within range."""
        index = 0
        while index < len(segment_groups):
            word_count = self._count_group_words(segment_groups[index])
            if word_count >= MIN_SEGMENT_WORDS or len(segment_groups) == 1:
                index += 1
                continue

            merge_prev = False
            merge_next = False
            prev_words = None
            next_words = None

            if index > 0:
                prev_words = self._count_group_words(segment_groups[index - 1])
                merge_prev = prev_words + word_count <= MAX_SEGMENT_WORDS

            if index + 1 < len(segment_groups):
                next_words = self._count_group_words(segment_groups[index + 1])
                merge_next = word_count + next_words <= MAX_SEGMENT_WORDS

            if merge_prev and merge_next:
                if abs((prev_words + word_count) - TARGET_SEGMENT_WORDS) <= abs((word_count + next_words) - TARGET_SEGMENT_WORDS):
                    segment_groups[index - 1].extend(segment_groups[index])
                    del segment_groups[index]
                    index = max(index - 1, 0)
                else:
                    segment_groups[index].extend(segment_groups[index + 1])
                    del segment_groups[index + 1]
                continue

            if merge_prev:
                segment_groups[index - 1].extend(segment_groups[index])
                del segment_groups[index]
                index = max(index - 1, 0)
                continue

            if merge_next:
                segment_groups[index].extend(segment_groups[index + 1])
                del segment_groups[index + 1]
                continue

            index += 1

    @staticmethod
    def _count_group_words(group: Sequence[str]) -> int:
        """Count words in a paragraph group."""
        return sum(len(paragraph.split()) for paragraph in group)


if __name__ == "__main__":
    sample_pdf = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "sample_contract.pdf"
    if not sample_pdf.exists():
        raise FileNotFoundError(f"Sample PDF not found: {sample_pdf}")

    parser = PDFParser()
    first_three_segments = parser.parse(sample_pdf.read_bytes())[:3]

    for segment in first_three_segments:
        print(segment)
        print()
