# API Reference

Base URL (local): `http://localhost:8000`

## `GET /api/health`

Liveness and configuration status.

**Response**

```json
{
  "status": "ok",
  "model_loaded": true,
  "fine_tuned": false,
  "classifier_labels": 48,
  "llm_configured": false,
  "llm_provider": "xai",
  "version": "0.1.0"
}
```

`fine_tuned` is `true` only when `FINE_TUNED_MODEL_PATH` points to a loaded
sequence-classification checkpoint (see `FINE_TUNING_HANDOFF.md`).
`classifier_labels` is the size of the active taxonomy (48: 41 CUAD + 7 extensions).

## `POST /api/analyze`

Analyze a PDF contract.

**Request:** `multipart/form-data`  
- `file`: PDF file (max size from `MAX_UPLOAD_MB`, default 15)

**Success (200):** `AnalysisResponse`:

```json
{
  "filename": "contract.pdf",
  "disclaimer": "...",
  "summary": { "total_clauses": 12, "high": 3, "medium": 5, "low": 4 },
  "document_metadata": {
    "document_name": "...", "parties": "...", "agreement_date": "...",
    "effective_date": "...", "expiration_date": "...", "governing_law": "..."
  },
  "clauses": [ /* ClauseResult[] — id, category, confidence, risk_level,
                  risk_reasons, original_text, plain_english,
                  suggested_alternative, llm_available */ ],
  "processing_notes": []
}
```

`document_metadata` fields are `null` when not found; the frontend only renders
a Contract Overview panel when at least one field is present.

**Errors**

| Status | Meaning |
|--------|---------|
| 400 | Not a PDF, empty file, or unreadable PDF |
| 413 | File too large |
| 422 | Request validation failure (e.g. missing `file` field) |
| 500 | Internal analysis failure |

Interactive docs: http://localhost:8000/docs
