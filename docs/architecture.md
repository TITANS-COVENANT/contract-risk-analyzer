# System Architecture

## Overview

The Contract Clause Risk Analyzer is a web prototype that helps freelancers and SMEs identify and understand risky clauses in commercial contracts. It follows the three-layer design from the project proposal:

1. **Sieve** — segment + classify clauses  
2. **Judge** — score risk  
3. **Translator** — plain-English explanations via LLM  

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, React, recharts, framer-motion |
| Backend | FastAPI, Pydantic, Uvicorn |
| PDF | PyMuPDF |
| NLP | Legal-BERT (`nlpaueb/legal-bert-base-uncased`), optionally fine-tuned, + keyword hybrid |
| LLM | xAI (default), OpenAI, or Anthropic |

## Clause taxonomy

`backend/ml/labels.py` defines 48 categories:

- **41 official CUAD categories** (Hendrycks et al., 2021 — the exact list verified
  against `github.com/The-Atticus-Project/cuad`). These are the categories the
  fine-tuned classifier (see `notebooks/finetune_legal_bert_cuad.ipynb`) is trained on.
- **7 practical extensions** — Indemnification, Confidentiality, Limitation of
  Liability, Payment Terms, Dispute Resolution, Force Majeure, General — clauses
  that are common and high-stakes in freelancer/SME contracts but are not part of
  CUAD's own category list. These have no gold training data, so they are served
  by the keyword/prototype layer only; the classifier's existing confidence-based
  tie-break already lets keyword matches win here even when a fine-tuned checkpoint
  is loaded.

Each category also carries a `kind`: `metadata` (Document Name, Parties, Agreement
Date, Effective Date, Expiration Date) is routed to the Contract Overview panel
instead of a risk clause card; everything else (`risk`) is scored and shown as a
clause card. Governing Law is `risk`-kind but is also lifted into the overview
panel as a convenience field.

## Request flow

1. Browser uploads PDF to `POST /api/analyze`  
2. Bytes stay in memory for the request only  
3. `PDFParser` extracts and segments text (200-400 word segments)
4. `ClauseClassifier` assigns one of 48 categories + confidence (fine-tuned model
   if `FINE_TUNED_MODEL_PATH` is set, else Legal-BERT prototype similarity, else
   keyword-only — see `classifier.py`)
5. `RiskScorer` assigns HIGH / MEDIUM / LOW + reasons; on a scoring tie between
   categories, the higher-risk category wins (safety-first default)
6. `ClauseSimplifier` produces plain English + alternative (LLM, with an offline
   fallback if no key is configured or the call fails)
7. `AnalysisPipeline` splits `metadata`-kind clauses into `document_metadata`;
   `risk`-kind clauses become the `clauses` list
8. JSON returned to the UI; upload discarded

## Fine-tuning

The base classifier ships without a fine-tuned checkpoint (CPU-only training is
impractical for this project — see `FINE_TUNING_HANDOFF.md`). Set
`FINE_TUNED_MODEL_PATH` in `.env` to a local path or Hugging Face Hub repo id
produced by `notebooks/finetune_legal_bert_cuad.ipynb` to enable it; `/api/health`
reports `fine_tuned: true` once active.  

## Privacy

- No database of contracts  
- Logs exclude clause text  
- Disclaimer on every response and page  

## Related docs

- Living build log: [`BUILD.md`](../BUILD.md)  
- API: [`api-reference.md`](./api-reference.md)  
- User guide: [`user-guide.md`](./user-guide.md)  
