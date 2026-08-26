"""Risk scoring engine (Judge layer).

Combines category base risk with lexical red-flag patterns that freelancers
and SMEs commonly encounter in commercial contracts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from app.models.schemas import RiskLevel
from ml.labels import CLAUSE_LABELS, UNKNOWN_LABEL

# Patterns that escalate risk when present in clause text.
_HIGH_RISK_PATTERNS: Sequence[Tuple[str, str]] = (
    (r"\bunlimited\b", "unlimited liability language"),
    (r"\bindefinite(ly)?\b", "indefinite duration"),
    (r"\bperpetual(ly)?\b", "perpetual obligation"),
    (r"\bsole discretion\b", "one-sided sole discretion"),
    (r"\bwithout cause\b", "termination without cause"),
    (r"\bfor convenience\b", "termination for convenience"),
    (r"\battorney['’]?s? fees\b", "attorney fee shifting"),
    (r"\bhold harmless\b", "hold-harmless obligation"),
    (r"\bany and all claims\b", "broad claim coverage"),
    (r"\bwaive[sd]?\b.*\b(jury|class action)\b", "rights waiver"),
    (r"\bnon[- ]?compete\b", "non-compete restriction"),
    (r"\bexclusive(ly)?\b", "exclusivity restriction"),
    (r"\bwork made for hire\b|\bwork for hire\b", "IP assignment as work for hire"),
    (r"\bas is\b", "as-is disclaimer of warranties"),
    (r"\bno liability\b|\bshall not be liable\b", "broad liability exclusion"),
    (r"\bliquidated damages\b", "liquidated damages"),
    (r"\bautomatic renewal\b|\bauto[- ]renew", "automatic renewal"),
    (r"\bmost favored (nation|customer)\b", "most-favored-nation pricing constraint"),
    (r"\birrevocable\b.*\bperpetual\b|\bperpetual\b.*\birrevocable\b", "irrevocable and perpetual grant"),
    (r"\bnever to sue\b|\bcovenant not to sue\b|\bwaives? .*\bright to (sue|bring)\b", "waiver of right to sue"),
    (r"\bliquidated damages\b.*\bnot as a penalty\b|\bpenalty of\b", "liquidated damages penalty"),
    (r"\bchange of control\b", "change-of-control trigger"),
)

_MEDIUM_RISK_PATTERNS: Sequence[Tuple[str, str]] = (
    (r"\bnet\s*\d+\b", "payment timing terms"),
    (r"\blate fee\b|\binterest\b", "late payment penalties"),
    (r"\barbitration\b", "mandatory arbitration"),
    (r"\bconfidential\b", "confidentiality obligations"),
    (r"\binsurance\b", "insurance requirements"),
    (r"\baudit\b", "audit rights"),
    (r"\bassign(ment|s|able)?\b", "assignment restrictions"),
    (r"\bnotice of\b", "notice requirements"),
    (r"\bthirty\s*\(?\s*30\s*\)?\s*days\b|\b30 days\b", "short notice period"),
    (r"\bright of first refusal\b|\bright of first offer\b|rofr|rofo|rofn", "right of first refusal/offer"),
    (r"\bminimum (commitment|purchase|spend|order)\b", "minimum commitment obligation"),
    (r"\bunlimited use\b|\ball[- ]you[- ]can[- ]eat\b", "unlimited-use license grant"),
)

_RISK_RANK = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
_RANK_TO_RISK = {0: RiskLevel.LOW, 1: RiskLevel.MEDIUM, 2: RiskLevel.HIGH}


@dataclass(frozen=True)
class RiskAssessment:
    """Structured output of the risk scorer."""

    risk_level: RiskLevel
    reasons: List[str]


class RiskScorer:
    """Evaluate classified clauses against predefined risk parameters."""

    def score(self, category: str, text: str) -> RiskAssessment:
        """Score a clause given its category and original text.

        Args:
            category: Predicted clause category label.
            text: Original clause text.

        Returns:
            RiskAssessment with level and human-readable reasons.
        """
        reasons: List[str] = []
        base = self._base_risk(category)
        score = _RISK_RANK[base]
        reasons.append(f"category baseline: {category} → {base.value}")

        lowered = text.casefold()
        high_hits = self._match_patterns(lowered, _HIGH_RISK_PATTERNS)
        medium_hits = self._match_patterns(lowered, _MEDIUM_RISK_PATTERNS)

        if high_hits:
            score = max(score, _RISK_RANK[RiskLevel.HIGH])
            reasons.extend(high_hits)
        elif medium_hits and score < _RISK_RANK[RiskLevel.MEDIUM]:
            score = _RISK_RANK[RiskLevel.MEDIUM]
            reasons.extend(medium_hits)
        elif medium_hits:
            reasons.extend(medium_hits)

        # One-sided indemnity without mutual language is especially risky.
        if re.search(r"\bindemnif", lowered) and not re.search(
            r"\beach party shall|mutual(ly)? indemnif", lowered
        ):
            score = max(score, _RISK_RANK[RiskLevel.HIGH])
            if "one-sided indemnification" not in reasons:
                reasons.append("one-sided indemnification")

        # Cap reason list for UI readability.
        unique_reasons = list(dict.fromkeys(reasons))[:8]
        return RiskAssessment(
            risk_level=_RANK_TO_RISK[score],
            reasons=unique_reasons,
        )

    @staticmethod
    def _base_risk(category: str) -> RiskLevel:
        """Map category to base risk prior."""
        if category == UNKNOWN_LABEL or category not in CLAUSE_LABELS:
            return RiskLevel.LOW
        raw = CLAUSE_LABELS[category]["base_risk"]
        return RiskLevel(raw)

    @staticmethod
    def _match_patterns(
        text: str,
        patterns: Sequence[Tuple[str, str]],
    ) -> List[str]:
        """Return reason strings for matching patterns."""
        hits: List[str] = []
        for pattern, reason in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(reason)
        return hits
