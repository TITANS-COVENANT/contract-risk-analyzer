# Fine-Tuning Handoff — What You Need To Do

This is the one remaining piece I can't do myself: fine-tuning Legal-BERT needs a
GPU, and this machine only has a CPU (`torch` reports `cuda available: False`).
Training on CPU here would take many hours to over a day and tie up your laptop,
so instead I built you a **Google Colab notebook** that does it on a free GPU in
roughly 1-2 hours. You run it, send me back two things, and I wire it into the app.

Everything else in this rebuild is already done and verified — see the summary
at the end of this session's conversation for what changed. This document is
just your checklist.

## What you're running

**File:** `notebooks/finetune_legal_bert_cuad.ipynb`

It downloads the real CUAD dataset (verified live against
`github.com/The-Atticus-Project/cuad` while building this — 510 contracts,
41 categories, confirmed working), derives a 42-way classification dataset from
it (the 41 CUAD categories + an "Unknown" class), and fine-tunes
`nlpaueb/legal-bert-base-uncased` on it. I validated the trickiest part (the
question-to-category mapping) against the real dataset before finalizing the
notebook — every one of the 41 categories got real training examples with zero
mapping disagreements — so this should run cleanly.

## Step by step

1. **Open Colab:** go to https://colab.research.google.com, then
   **File → Upload notebook**, and select `notebooks/finetune_legal_bert_cuad.ipynb`
   from this project folder.
2. **Turn on a GPU:** in the Colab menu, **Runtime → Change runtime type →
   Hardware accelerator → T4 GPU** (the free tier's T4 is enough — no need to pay
   for Colab Pro).
3. **Run everything:** **Runtime → Run all**. Confirm any "run anyway" warning
   Colab shows for notebooks not authored by Google.
4. **Wait.** Expect roughly **1-2 hours**. You can close the laptop lid/tab and
   check back — Colab keeps running in the background for a while, but don't
   let the browser tab stay closed for too many hours or the session may
   disconnect and you'll need to re-run from the top.
5. **If a cell shows a red error box:** stop there, don't try to fix it — copy
   the full error text (and the cell just above it) and send it to me. The
   notebook is written to fail loudly with clear messages rather than silently
   produce a broken model, so an error is meant to be reported, not debugged by you.
6. **Near the end**, the notebook asks you to hand off the trained model. Pick
   **one** of these two paths:

   **Option A — Hugging Face Hub (recommended, easiest for me to use):**
   - Make a free account at https://huggingface.co/join if you don't have one.
   - Go to https://huggingface.co/settings/tokens → create a new token with
     **write** access.
   - Run the "Option A" cell, paste that token when prompted (input is hidden —
     that's normal, not frozen).
   - It prints a URL like `https://huggingface.co/your-username/legal-bert-cuad-clauses`.

   **Option B — manual download (skip if you did Option A):**
   - Run the "Option B" cell instead. It zips the model (~400-500MB) and
     downloads it through your browser.
   - Send it to me via Google Drive link, WeTransfer, or similar — it's too
     big to paste into chat.

7. **Copy the evaluation table** printed in the "Evaluate" step (or grab
   `cuad_classification_report.csv` from Colab's file browser on the left) —
   this is the accuracy/precision/recall/F1 table the project proposal's
   evaluation section needs. Send it along with the model.

## What to send back to me

- Either the Hugging Face model URL (Option A) **or** the downloaded zip file (Option B)
- The evaluation table from Step 9 of the notebook

## What I'll do once I have it

1. Set `FINE_TUNED_MODEL_PATH` in `.env` to your Hugging Face repo id (or the
   local path if you sent a zip), plus `HF_TOKEN` if the repo is private.
2. Restart the backend with `SKIP_MODEL_LOAD=false` and confirm
   `GET /api/health` reports `"fine_tuned": true`.
3. Re-run a couple of test contracts to confirm classification quality improved
   over the current keyword/prototype fallback.
4. Fold your evaluation table into the project's evaluation section.

## Two other things worth your attention (found while testing, not part of the fine-tuning task)

- **Your `.env`'s `XAI_API_KEY` got accidentally printed in this session's
  output earlier** (my mistake, a `sed` command misfired). It's no longer the
  active provider, but the value is still sitting in `.env` — treat it as
  exposed and rotate it at https://console.x.ai when convenient.
- **The app now uses Anthropic** (`LLM_PROVIDER=anthropic`,
  `LLM_MODEL=claude-opus-5`) with the key you gave me. Confirmed by calling
  the API directly: the key and model are both valid and correctly wired
  up, but live calls are currently failing with *"Your credit balance is
  too low to access the Anthropic API."* The app degrades gracefully
  (you'll see "Offline explanation" on clause cards instead of a crash) —
  add credits at https://console.anthropic.com/settings/billing for live
  plain-English explanations to work end to end.

## Optional: the other still-open item from before

Separate from fine-tuning, the proposal's evaluation section also expects a
small **user study** (Appendix A questionnaire, already in
`docs/evaluation-questionnaire.md`) with a few freelancers/SMEs actually using
the tool. Not needed for this handoff, but worth doing before final submission.
