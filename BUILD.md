# BUILD.md — Contract Clause Risk Analyzer

Living build log. **Updated after every stage.**  
Project: AI-Powered Contract Clause Risk Analyzer (GCTU BSc CS proposal).

---

## Current status

| Stage | Name | Status |
|-------|------|--------|
| 0 | Workspace sync + living docs | ✅ Done |
| 1 | Config, schemas, FastAPI shell | ✅ Done |
| 2 | PDF parser wired + tests | ✅ Done |
| 3 | Risk scorer (Judge) | ✅ Done |
| 4 | Legal-BERT classifier (Sieve) | ✅ Done (hybrid + keyword fallback) |
| 5 | LLM simplifier (Translator) | ✅ Done (needs your API key for live LLM) |
| 6 | Pipeline + `POST /api/analyze` | ✅ Done |
| 7 | Next.js frontend | ✅ Done |
| 8 | Evaluation questionnaire | ✅ Done (docs) |
| 9 | Polish & handoff | ✅ Baseline complete |
| 10 | Full 41-category CUAD taxonomy + Contract Overview | ✅ Done |
| 11 | Fine-tuning notebook (Colab handoff) | ✅ Done — model at `ClauseGuard/legal-bert-cuad-clauses`, wired into `.env` |
| 12 | Editorial-minimal light/dark redesign (hedgia.net-inspired, dataviz charts, motion) | ✅ Done |

**Last updated:** 2026-09-04  
**Tests:** `12 passed` (`SKIP_MODEL_LOAD=true`)  
**Verified live:** backend + frontend run together, full upload → analyze → dashboard flow checked in a real browser in both themes, no console errors.

---

## What this project is

A web app that:

1. Accepts a **PDF contract** upload  
2. **Segments** text (PDF parser)  
3. **Classifies** clauses (Legal-BERT + keyword hybrid — “Sieve”)  
4. **Scores risk** High/Medium/Low (“Judge”)  
5. **Explains** in plain English + suggests alternatives via LLM (“Translator”)  
6. Shows results in a browser UI with a clear **legal information ≠ legal advice** disclaimer  

Contract text is **never stored** beyond the request.

---

## Architecture (quick map)

```
Browser (Next.js)  --POST PDF-->  FastAPI
                                    │
                         PDFParser → ClauseClassifier → RiskScorer → ClauseSimplifier
                                    │
                                 JSON clauses + summary
```

| Layer | Module | Role |
|-------|--------|------|
| Sieve prep | `backend/app/core/pdf_parser.py` | Extract & segment PDF text |
| Sieve | `backend/app/core/classifier.py` | Category + confidence |
| Judge | `backend/app/core/risk_scorer.py` | Risk level + reasons |
| Translator | `backend/app/core/simplifier.py` | Plain English + alternative |
| Orchestrator | `backend/app/core/pipeline.py` | End-to-end |
| API | `backend/app/api/routes/*` | `/api/health`, `/api/analyze` |
| Labels | `backend/ml/labels.py` | CUAD-oriented categories |

Full proposal: `Project Proposal.pdf`.

---

## 🔑 API keys — what you must provide

### You need keys for

| Variable | When | Get it from |
|----------|------|-------------|
| **`XAI_API_KEY`** | Default (`LLM_PROVIDER=xai`) | https://console.x.ai (account: https://accounts.x.ai) |
| `OPENAI_API_KEY` | If `LLM_PROVIDER=openai` | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | If `LLM_PROVIDER=anthropic` | https://console.anthropic.com/ |
| `HF_TOKEN` (optional) | Rate-limited / private HF models | https://huggingface.co/settings/tokens |

### Stages that work **without** any key

- Backend health, PDF parse, classify (keyword or Legal-BERT), risk scoring  
- Frontend UI shell  
- Offline plain-English **fallback** text (lower quality)

### Stages that need a key for **full** quality

- Live LLM plain-English + suggested alternatives (Stage 5+)

### How to give keys to the agent (safe)

1. In the project root (`C:\Users\LENOVO\contract-risk-analyzer`):

```powershell
copy .env.example .env
notepad .env
```

2. Set at least:

```env
LLM_PROVIDER=xai
LLM_MODEL=grok-4.5
XAI_API_KEY=xai-your-real-key-here
```

3. Save the file.  
4. Tell the agent in chat: **“.env is ready with XAI_API_KEY”**  
5. **Do not paste the key into chat.**  
6. `.env` is gitignored — never commit it.

### Frontend env (no secrets)

```powershell
cd frontend
copy .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## How to run (local)

### Backend

```powershell
cd C:\Users\LENOVO\contract-risk-analyzer\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional: skip heavy model download during first smoke test
$env:SKIP_MODEL_LOAD="true"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/api/health  
- Docs: http://localhost:8000/docs  

### Frontend (after Stage 7)

```powershell
cd C:\Users\LENOVO\contract-risk-analyzer\frontend
npm install
npm run dev
```

Open http://localhost:3000

### Tests

```powershell
cd C:\Users\LENOVO\contract-risk-analyzer\backend
$env:SKIP_MODEL_LOAD="true"
.\.venv\Scripts\pytest.exe -q
```

---

## Stage log

### Stage 0 — Sync + docs ✅
- Synced Desktop project (proposal, scaffold, `pdf_parser.py`) into workspace  
- Created this `BUILD.md` and expanded `.env.example`  

### Stages 1–6 — Backend core ✅
- `config.py` — pydantic-settings from `.env`  
- `schemas.py` — API models  
- `main.py` — FastAPI + CORS + lifespan  
- `health.py` / `analyze.py` — endpoints  
- `classifier.py` — Legal-BERT prototype similarity + keyword hybrid  
- `risk_scorer.py` — rule engine  
- `simplifier.py` — xAI / OpenAI / Anthropic + offline fallback  
- `pipeline.py` — orchestration  
- `ml/labels.py` — freelancer-relevant CUAD-style labels  
- Tests under `tests/backend/`  
- Fixture: `tests/fixtures/sample_contract.pdf`  

### Stage 7 — Frontend ✅
- Next.js 14 App Router + TypeScript  
- Pages: `/` landing, `/analyze` upload + results  
- Components: dropzone, risk summary, clause cards, disclaimer, loading  
- Env: `frontend/.env.local.example` → `NEXT_PUBLIC_API_URL`

### Stage 8 — Evaluation ✅ (docs)
- `docs/evaluation-questionnaire.md` (Appendix A Likert form)

### Stage 9 — Polish ✅ (baseline)
- README, architecture, API, user guide filled  
- Sample PDF: `tests/fixtures/sample_contract.pdf`  
- Backend deps installed in `backend/.venv`; frontend `npm install` done  

### Your action for full LLM quality
1. `copy .env.example .env`  
2. Put `XAI_API_KEY=...` (or OpenAI/Anthropic)  
3. Restart backend without needing to paste keys in chat  
4. Optionally set `SKIP_MODEL_LOAD=false` and install `torch` + `transformers` for Legal-BERT neural mode  

```powershell
cd backend
.\.venv\Scripts\pip.exe install torch transformers safetensors sentencepiece
```

---

## Known limitations (proposal-aligned)

- English, text PDFs only (no OCR)  
- Commercial / service / NDA focus — not criminal, family, real estate  
- Classifier is hybrid (keyword/prototype) until a fine-tuned checkpoint from
  `notebooks/finetune_legal_bert_cuad.ipynb` is wired in via `FINE_TUNED_MODEL_PATH`
- Contract Overview extraction needs the title/parties text to form its own
  ~200+ word segment to reliably win classification over surrounding clause
  text — realistic for most real contract title pages, not guaranteed on very
  terse ones
- Output is **not** a substitute for a lawyer  

---

## Change checklist (agent)

After each stage:

1. Update the status table above  
2. Append stage log notes  
3. Note any new env vars or keys  
4. Record how to verify (command or URL)
