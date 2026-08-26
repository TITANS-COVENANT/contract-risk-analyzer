# Contract Clause Risk Analyzer

AI-powered contract clause risk detection and plain-English simplification for freelancers and SMEs.

**Academic project** (Ghana Communication Technology University — BSc Computer Science).  
Based on `Project Proposal.pdf`.

> **Disclaimer:** This tool provides *legal information*, not professional *legal advice*.

## Features

- Upload PDF contracts (English, text-based)
- Classify clauses across all 48 categories — the 41 official CUAD categories
  plus 7 freelancer-relevant additions (Legal-BERT hybrid + keywords; supports
  a fine-tuned checkpoint, see [`FINE_TUNING_HANDOFF.md`](./FINE_TUNING_HANDOFF.md))
- Automatic **Contract Overview** extraction (document name, parties, dates, governing law)
- Risk scoring: High / Medium / Low with reasons
- Risk distribution and category-breakdown charts
- Plain-English explanations + suggested alternatives (LLM)
- Editorial-minimal light/dark UI (huge display type, monochrome chrome, functional risk color only) with a theme toggle
- No persistent storage of contract content

## Architecture

See **[BUILD.md](./BUILD.md)** for the living architecture, stage tracker, and **API key setup instructions**.

```
PDF → Parser → Classifier (Sieve) → Risk Scorer (Judge) → LLM Simplifier (Translator) → UI
```

## Quick start

### 1. API keys (for full LLM explanations)

```powershell
copy .env.example .env
# Edit .env and set XAI_API_KEY (recommended) or OPENAI_API_KEY / ANTHROPIC_API_KEY
```

Details: [BUILD.md § API keys](./BUILD.md#-api-keys--what-you-must-provide)

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Tests

```powershell
cd backend
$env:SKIP_MODEL_LOAD="true"
.\.venv\Scripts\pytest.exe -q
```

## License

MIT — see [LICENSE](./LICENSE).



