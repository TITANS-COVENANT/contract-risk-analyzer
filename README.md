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

**Groq is the recommended free-tier provider.** No credit card required.

1. Sign up at https://console.groq.com
2. Go to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_...`)

```powershell
copy .env.example .env
```

Then open `.env` and set:

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=gsk_your_key_here
```

> **Optional alternatives** — xAI, OpenAI, and Anthropic are also supported.
> Set `LLM_PROVIDER=xai|openai|anthropic` and the matching key variable.
> These require paid accounts.

**HuggingFace token** (optional, speeds up first model download):

1. Sign up at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens → **New token** (read access is enough)
3. Add to `.env`: `HF_TOKEN=hf_your_token_here`

### 2. Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Health check: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

### 3. Frontend

```powershell
cd frontend
copy .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000  (change port if needed)
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



