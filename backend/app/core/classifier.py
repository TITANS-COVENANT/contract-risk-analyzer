"""Clause classification (Sieve layer).

Model card / expected input:
- Base model: Legal-BERT (Chalkidis et al., 2020) — `nlpaueb/legal-bert-base-uncased`
  https://huggingface.co/nlpaueb/legal-bert-base-uncased
- Input: English legal clause text segments (typically 200–400 words).
- Output: best-matching CUAD-oriented category + confidence in [0, 1].

MVP strategy:
1. If FINE_TUNED_MODEL_PATH points to a sequence-classification checkpoint, use it.
2. Else embed the clause with Legal-BERT and score cosine similarity against
   hand-crafted category prototype phrases (plus keyword boosts).
3. If model loading is skipped or fails, fall back to keyword-only classification
   so the rest of the pipeline remains usable for demos and tests.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from app.config import Settings, get_settings
from ml.labels import CLAUSE_LABELS, LABEL_NAMES, UNKNOWN_LABEL

logger = logging.getLogger(__name__)

_RISK_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


@dataclass(frozen=True)
class ClassificationResult:
    """Output of the Sieve layer for one segment."""

    category: str
    confidence: float
    method: str


class ClauseClassifier:
    """Classify contract segments into legal clause categories."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize classifier; optionally load Legal-BERT.

        Args:
            settings: Application settings. Defaults to cached global settings.
        """
        self.settings = settings or get_settings()
        self._model = None
        self._tokenizer = None
        self._torch = None
        self._prototype_embeddings: Optional[Dict[str, object]] = None
        self._fine_tuned = False
        self._loaded = False
        self._load_error: Optional[str] = None

    @property
    def is_loaded(self) -> bool:
        """Return True when a neural model is ready for inference."""
        return self._loaded

    @property
    def is_fine_tuned(self) -> bool:
        """Return True when a fine-tuned sequence-classification checkpoint is active."""
        return self._loaded and self._fine_tuned

    @property
    def load_error(self) -> Optional[str]:
        """Return the last model load error message, if any."""
        return self._load_error

    def load(self) -> None:
        """Load Legal-BERT or a fine-tuned checkpoint into memory."""
        if self.settings.skip_model_load:
            logger.info("Skipping model load (SKIP_MODEL_LOAD=true)")
            self._loaded = False
            return

        try:
            import os
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._torch = torch
            model_id = (
                self.settings.fine_tuned_model_path.strip()
                or self.settings.model_path
            )
            token = self.settings.hf_token or None
            # Set env var so huggingface_hub uses auth for ALL requests
            # (metadata HEAD + CDN download), not just from_pretrained calls.
            if token:
                os.environ["HF_TOKEN"] = token
            logger.info("Loading classification model: %s", model_id)

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                token=token,
            )
            # Only use a classification head when an explicit fine-tuned checkpoint
            # is configured. Base Legal-BERT is a masked LM — loading it via
            # AutoModelForSequenceClassification invents a random head and would
            # silently produce garbage labels.
            use_fine_tuned = bool(self.settings.fine_tuned_model_path.strip())
            if use_fine_tuned:
                from transformers import AutoModelForSequenceClassification

                self._model = AutoModelForSequenceClassification.from_pretrained(
                    model_id,
                    token=token,
                )
                self._fine_tuned = True
            else:
                self._model = AutoModel.from_pretrained(model_id, token=token)
                self._fine_tuned = False

            self._model.eval()
            if not self._fine_tuned:
                self._prototype_embeddings = self._build_prototype_embeddings()

            self._loaded = True
            self._load_error = None
            logger.info(
                "Classifier ready (fine_tuned=%s)",
                self._fine_tuned,
            )
        except Exception as exc:  # noqa: BLE001 — surface load failure, keep app up
            self._loaded = False
            self._load_error = str(exc)
            logger.warning(
                "Classifier model failed to load; using keyword fallback: %s",
                type(exc).__name__,
            )

    def classify(self, text: str) -> ClassificationResult:
        """Classify a single text segment.

        Args:
            text: Clause segment text.

        Returns:
            ClassificationResult with category, confidence, and method used.
        """
        cleaned = text.strip()
        if not cleaned:
            return ClassificationResult(UNKNOWN_LABEL, 0.0, "empty")

        keyword_cat, keyword_score = self._keyword_classify(cleaned)

        if self._loaded and self._fine_tuned and self._model is not None:
            neural = self._classify_fine_tuned(cleaned)
            if neural.confidence >= keyword_score:
                return neural
            if keyword_score >= self.settings.confidence_threshold:
                return ClassificationResult(
                    keyword_cat,
                    keyword_score,
                    "keyword+ft-tiebreak",
                )
            return neural

        if self._loaded and self._prototype_embeddings is not None:
            neural = self._classify_prototype(cleaned)
            # Blend keyword boost into neural score when categories agree.
            if keyword_cat == neural.category:
                conf = min(1.0, 0.65 * neural.confidence + 0.35 * keyword_score)
                return ClassificationResult(neural.category, conf, "legalbert+keyword")
            if keyword_score >= max(neural.confidence, self.settings.confidence_threshold):
                return ClassificationResult(keyword_cat, keyword_score, "keyword")
            return neural

        if keyword_score < self.settings.confidence_threshold:
            return ClassificationResult(UNKNOWN_LABEL, keyword_score, "keyword-low")
        return ClassificationResult(keyword_cat, keyword_score, "keyword")

    def classify_many(self, segments: Sequence[str]) -> List[ClassificationResult]:
        """Classify multiple segments sequentially.

        Args:
            segments: List of clause texts.

        Returns:
            One ClassificationResult per input segment.
        """
        return [self.classify(segment) for segment in segments]

    def _keyword_classify(self, text: str) -> Tuple[str, float]:
        """Score categories by keyword hits.

        A segment can legitimately contain keywords for several categories
        at once (e.g. a merged 200-400 word chunk spanning two short clauses,
        or a contract that packs indemnification and governing-law language
        into one paragraph). Scores are capped at 0.95, so ties across
        categories are common. On a tie, prefer the higher base-risk
        category — under-flagging a real risk is worse than over-flagging a
        boilerplate one for a risk-analysis tool.
        """
        lowered = text.casefold()
        best_label = UNKNOWN_LABEL
        best_score = 0.0
        best_risk_rank = -1

        for label, meta in CLAUSE_LABELS.items():
            hits = 0
            for keyword in meta["keywords"]:
                if keyword.casefold() in lowered:
                    hits += 1
            if hits == 0:
                continue
            # Softmax-like normalization against keyword count.
            score = min(0.95, 0.35 + 0.2 * hits)
            risk_rank = _RISK_RANK.get(meta["base_risk"], 0)
            if score > best_score or (
                score == best_score and risk_rank > best_risk_rank
            ):
                best_score = score
                best_label = label
                best_risk_rank = risk_rank

        return best_label, best_score

    def _build_prototype_embeddings(self) -> Dict[str, object]:
        """Encode prototype phrases for each label."""
        assert self._model is not None and self._tokenizer is not None
        embeddings: Dict[str, object] = {}
        for label, meta in CLAUSE_LABELS.items():
            vectors = [self._embed(proto) for proto in meta["prototypes"]]
            stacked = self._torch.stack(vectors, dim=0)
            embeddings[label] = self._torch.nn.functional.normalize(
                stacked.mean(dim=0),
                dim=0,
            )
        return embeddings

    def _embed(self, text: str):
        """Return L2-normalized mean-pooled Legal-BERT embedding."""
        assert self._model is not None and self._tokenizer is not None and self._torch is not None
        encoded = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        with self._torch.no_grad():
            outputs = self._model(**encoded)
            # Mean pool last hidden state, ignoring pad tokens.
            hidden = outputs.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
            summed = (hidden * mask).sum(dim=1)
            counts = mask.sum(dim=1).clamp(min=1e-9)
            mean_pooled = summed / counts
            return self._torch.nn.functional.normalize(mean_pooled.squeeze(0), dim=0)

    def _classify_prototype(self, text: str) -> ClassificationResult:
        """Classify via cosine similarity to prototype embeddings."""
        assert self._prototype_embeddings is not None and self._torch is not None
        query = self._embed(text)
        best_label = UNKNOWN_LABEL
        best_score = 0.0
        for label, proto_vec in self._prototype_embeddings.items():
            score = float(self._torch.dot(query, proto_vec).item())
            # Cosine similarity in [-1, 1] → map roughly into [0, 1]
            conf = max(0.0, min(1.0, (score + 1.0) / 2.0))
            # Stretch mid-range similarities for UI friendliness.
            conf = max(0.0, min(1.0, (conf - 0.45) / 0.45))
            if conf > best_score:
                best_score = conf
                best_label = label

        if best_score < self.settings.confidence_threshold:
            return ClassificationResult(UNKNOWN_LABEL, best_score, "legalbert-low")
        return ClassificationResult(best_label, best_score, "legalbert")

    def _classify_fine_tuned(self, text: str) -> ClassificationResult:
        """Classify with a sequence-classification head if labels align."""
        assert self._model is not None and self._tokenizer is not None and self._torch is not None
        encoded = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        with self._torch.no_grad():
            logits = self._model(**encoded).logits
            probs = self._torch.softmax(logits, dim=-1).squeeze(0)
            idx = int(self._torch.argmax(probs).item())
            conf = float(probs[idx].item())

        id2label = getattr(self._model.config, "id2label", {}) or {}
        raw_label = id2label.get(idx, id2label.get(str(idx), f"LABEL_{idx}"))
        category = self._normalize_label(str(raw_label))
        if conf < self.settings.confidence_threshold:
            return ClassificationResult(UNKNOWN_LABEL, conf, "fine-tuned-low")
        return ClassificationResult(category, conf, "fine-tuned")

    @staticmethod
    def _normalize_label(raw: str) -> str:
        """Map model label strings onto our CLAUSE_LABELS keys when possible."""
        cleaned = re.sub(r"[_\\-]+", " ", raw).strip()
        for name in LABEL_NAMES:
            if name.casefold() == cleaned.casefold():
                return name
            if name.casefold() in cleaned.casefold() or cleaned.casefold() in name.casefold():
                return name
        return cleaned if cleaned else UNKNOWN_LABEL
