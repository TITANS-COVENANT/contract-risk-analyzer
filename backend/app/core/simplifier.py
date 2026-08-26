"""LLM-based plain-English simplification (Translator layer).

Supports:
- xAI / SpaceXAI (OpenAI-compatible API at https://api.x.ai/v1) — default
- OpenAI
- Anthropic

Never logs clause text (treated as sensitive).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a legal literacy assistant for freelancers and small businesses.
Your job is to explain contract clauses in plain English and suggest fairer alternatives.

Rules:
1. Be accurate. Do not invent obligations that are not in the clause.
2. Use short sentences a non-lawyer can understand.
3. Flag one-sided or predatory terms clearly.
4. Suggest a neutral alternative clause when the original is risky.
5. You provide legal INFORMATION, not legal advice. Never say "you should sign" or "this is fine".
6. Respond ONLY with valid JSON of the form:
{"plain_english":"...","suggested_alternative":"..."}
"""


@dataclass(frozen=True)
class SimplificationResult:
    """Plain-English explanation and optional alternative language."""

    plain_english: str
    suggested_alternative: str
    available: bool
    error: Optional[str] = None


class ClauseSimplifier:
    """Translate legalese into layman terms via an LLM provider."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize simplifier with application settings."""
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        """Return True when an API key is present for the selected provider."""
        return self.settings.has_llm_key()

    def simplify(
        self,
        text: str,
        category: str,
        risk_level: str,
    ) -> SimplificationResult:
        """Generate plain English and a suggested alternative for one clause.

        Args:
            text: Original clause text.
            category: Predicted category label.
            risk_level: HIGH | MEDIUM | LOW.

        Returns:
            SimplificationResult. On missing key or API failure, returns a
            deterministic fallback explanation so the UI still works.
        """
        if not self.is_configured:
            return self._fallback(
                text,
                category,
                risk_level,
                available=False,
                error="LLM API key not configured",
            )

        user_prompt = (
            f"Category: {category}\n"
            f"Risk level: {risk_level}\n"
            f"Clause text:\n{text[:4000]}\n\n"
            "Explain what this means for a freelancer or small business owner, "
            "and suggest a more balanced alternative clause."
        )

        try:
            raw = self._call_provider(user_prompt)
            parsed = self._parse_json_response(raw)
            return SimplificationResult(
                plain_english=parsed.get("plain_english", "").strip()
                or self._fallback_plain(category, risk_level),
                suggested_alternative=parsed.get("suggested_alternative", "").strip(),
                available=True,
            )
        except Exception as exc:  # noqa: BLE001 — degrade gracefully
            logger.warning("LLM simplification failed: %s", type(exc).__name__)
            return self._fallback(
                text,
                category,
                risk_level,
                available=False,
                error=type(exc).__name__,
            )

    def _call_provider(self, user_prompt: str) -> str:
        """Dispatch to the configured LLM provider and return raw text."""
        provider = self.settings.llm_provider
        if provider == "xai":
            return self._call_openai_compatible(
                api_key=self.settings.xai_api_key,
                base_url="https://api.x.ai/v1",
                model=self.settings.llm_model,
                user_prompt=user_prompt,
            )
        if provider == "openai":
            return self._call_openai_compatible(
                api_key=self.settings.openai_api_key,
                base_url="https://api.openai.com/v1",
                model=self.settings.llm_model,
                user_prompt=user_prompt,
            )
        if provider == "anthropic":
            return self._call_anthropic(user_prompt)
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def _call_openai_compatible(
        self,
        api_key: str,
        base_url: str,
        model: str,
        user_prompt: str,
    ) -> str:
        """Call an OpenAI-compatible chat completions endpoint."""
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        # Prefer chat.completions for broad provider compatibility.
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Empty LLM response")
        return content

    def _call_anthropic(self, user_prompt: str) -> str:
        """Call Anthropic Messages API."""
        from anthropic import Anthropic

        client = Anthropic(api_key=self.settings.anthropic_api_key)
        message = client.messages.create(
            model=self.settings.llm_model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = []
        for block in message.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        if not parts:
            raise RuntimeError("Empty Anthropic response")
        return "\n".join(parts)

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        """Extract JSON object from model output."""
        stripped = raw.strip()
        # Strip markdown fences if present.
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
        if fenced:
            stripped = fenced.group(1)
        else:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                stripped = stripped[start : end + 1]
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("LLM JSON was not an object")
        return data

    def _fallback(
        self,
        text: str,
        category: str,
        risk_level: str,
        available: bool,
        error: Optional[str],
    ) -> SimplificationResult:
        """Deterministic explanation when LLM is unavailable."""
        plain = self._fallback_plain(category, risk_level)
        snippet = " ".join(text.split()[:40])
        if snippet:
            plain = f"{plain} Excerpt begins: “{snippet}…”"
        alternative = (
            "Each party shall be responsible for its own acts and omissions. "
            "Any liability under this agreement shall be limited to the total "
            "fees paid under the agreement in the twelve (12) months preceding the claim."
            if risk_level in {"HIGH", "MEDIUM"}
            else ""
        )
        return SimplificationResult(
            plain_english=plain,
            suggested_alternative=alternative,
            available=available,
            error=error,
        )

    @staticmethod
    def _fallback_plain(category: str, risk_level: str) -> str:
        """Template plain-English text without calling an LLM."""
        return (
            f"This section appears related to “{category}” and was scored "
            f"{risk_level} risk. An automated plain-English rewrite is unavailable "
            f"until an LLM API key is configured. Review this clause carefully "
            f"or consult a lawyer if unsure."
        )
