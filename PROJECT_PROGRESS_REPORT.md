# Contract Clause Risk Analyzer Progress Report

## How to open and test in a browser

1. Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:SKIP_MODEL_LOAD="true"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend in a second terminal:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

3. Open these URLs in your browser:
- `http://localhost:3000` for the main app
- `http://localhost:3000/analyze` for the upload and analysis screen
- `http://localhost:8000/docs` for the FastAPI interactive API docs
- `http://localhost:8000/api/health` to confirm the backend is running

## Overall progress estimate

**Estimated completion: 80%**

This project is beyond a prototype skeleton: the backend pipeline, API routes, frontend UI, tests, documentation, and a living build log are already implemented. However, the proposal also points toward legal-domain model adaptation and evaluation, and those parts are not fully finished yet. What remains is mainly project-completion work rather than basic app construction: actual fine-tuning or training evidence, stronger model quality, real evaluation with users, and final polishing for submission.

## What is already done

### 1. Project scope and documentation
- The proposal is present in `Project Proposal.pdf`.
- The repository includes `README.md`, `BUILD.md`, `docs/architecture.md`, `docs/user-guide.md`, `docs/api-reference.md`, and `docs/evaluation-questionnaire.md`.
- The docs clearly describe the target workflow: upload PDF, classify clauses, score risk, and simplify legal text.

### 1a. Legal-BERT fine-tuning intent
- The proposal discusses Legal-BERT as the legal NLP backbone and notes that legal-specific fine-tuning improves performance.
- The codebase supports loading a fine-tuned checkpoint through `backend/app/core/classifier.py` and `backend/app/config.py`.
- The repository does not currently include the actual training or fine-tuning script, training dataset pipeline, or a committed fine-tuned checkpoint.
- In practice, the current implementation uses base Legal-BERT embeddings plus keyword/prototype matching, with fallback keyword classification if the model is unavailable.

### 2. Backend application
- FastAPI app entrypoint exists in `backend/app/main.py`.
- Health and analysis routes exist in `backend/app/api/routes/health.py` and `backend/app/api/routes/analyze.py`.
- The end-to-end pipeline exists in `backend/app/core/pipeline.py`.
- PDF parsing, clause classification, risk scoring, and simplification modules are present.
- Request/response schemas are defined in `backend/app/models/schemas.py`.

### 3. Frontend application
- Next.js frontend exists in `frontend/app/page.tsx` and `frontend/app/analyze/page.tsx`.
- UI components for upload, loading state, risk summary, disclaimer, and clause cards are present.
- The frontend is wired to the backend API via `NEXT_PUBLIC_API_URL`.

### 4. Testing and verification
- Backend tests pass: `10 passed`.
- Test coverage includes API health, PDF analysis, parser behavior, risk scoring, and keyword classification behavior.
- There is a sample contract PDF in `tests/fixtures/sample_contract.pdf`.

## What the proposal asks for

From the proposal, the main intended deliverables are:
- A web-based contract analysis tool for freelancers and SMEs.
- Clause classification using Legal-BERT and CUAD-style categories.
- Risk scoring for high / medium / low risk clauses.
- Plain-English simplification and suggested alternatives using an LLM.
- Evaluation with technical metrics and user feedback.
- A privacy-safe workflow with no persistent storage of contract content.

## What is still missing or incomplete

### 1. Full model quality is still conditional
The project supports a classifier and LLM simplifier, but the high-quality mode depends on configuration:
- If `SKIP_MODEL_LOAD=true`, the system uses fallback keyword behavior instead of fully warming the neural model.
- If no LLM key is configured, the simplifier falls back to deterministic text instead of live model output.

### 2. Formal evaluation and fine-tuning are not yet demonstrated in code
The proposal expects evaluation using:
- technical metrics like accuracy, precision, and recall
- user testing with freelancers and SMEs

The repo includes the questionnaire and consent template, but it does not yet show a completed evaluation dataset, results table, analysis write-up, or a reproducible fine-tuning workflow for Legal-BERT.

### 3. Submission-hardened polish is still needed
The app is usable, but final submission work usually still includes:
- a full demo run with the real LLM key configured
- confirmation that the frontend and backend are running together cleanly
- final screenshots or a demo recording
- a short results section with limits and future work

## What needs to be done to finish it

### Priority 1: Validate the full live workflow
- Add a real API key in `.env` so the simplifier can use a live LLM.
- Run the backend without `SKIP_MODEL_LOAD=true` if you want the heavier model path enabled.
- Upload a few sample contracts and confirm the output is stable across multiple clauses.
- Check that the browser UI shows the health status, summary cards, and clause details correctly.

### Priority 2: Complete evaluation evidence
- Run the tool on a test set of contracts or contract excerpts.
- Record basic metrics such as how many clauses are detected, how many are marked high risk, and whether the outputs are sensible.
- If user testing is part of the submission, collect questionnaire responses and summarize them.
- Add a short evaluation section to the docs or final report with findings and limitations.

### Priority 3: Improve output quality
- Review the fallback simplifier text and compare it against live LLM responses.
- Tune clause categories and risk rules for the most common contract clauses in the project scope.
- Make sure the plain-English alternative is clear, short, and legally cautious.

### Priority 4: Final project packaging
- Clean up docs so the final submission story is easy to follow.
- Capture screenshots of the frontend and example analysis results.
- Ensure installation and run instructions are complete for a fresh machine.
- Verify the final report mentions limitations, ethics, and privacy clearly.

## Practical run checklist

1. Create `.env` from `.env.example`.
2. Put the required LLM key in `.env` if you want full simplification quality.
3. Start the backend on port `8000`.
4. Start the frontend on port `3000`.
5. Open `http://localhost:3000/analyze` in a browser.
6. Upload a text-based PDF contract and review the results.

## Notes on current status

- The project is not just a mockup; the core pipeline is implemented and tested.
- The remaining work includes the missing Legal-BERT fine-tuning or training pipeline, evaluation evidence, and submission polish.
- Based on the repo contents and tests, the project is roughly **80% complete**.

## Evidence used for this report

- `README.md`
- `BUILD.md`
- `Project Proposal.pdf`
- `backend/app/main.py`
- `backend/app/core/pipeline.py`
- `backend/app/api/routes/analyze.py`
- `frontend/app/page.tsx`
- `frontend/app/analyze/page.tsx`
- `docs/architecture.md`
- `docs/user-guide.md`
- `docs/api-reference.md`
- `docs/evaluation-questionnaire.md`
- `tests/backend/test_api.py`

## Quick conclusion

You can already open the app in a browser and test it locally. The project’s core engineering work is done, but the final completion depends on live configuration, formal evaluation evidence, and submission-quality polish.
