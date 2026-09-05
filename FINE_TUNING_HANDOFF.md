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
   *(Re-upload the notebook each time you retry — always use the latest copy from this repo.)*
2. **Turn on a GPU:** in the Colab menu, **Runtime → Change runtime type →
   Hardware accelerator → T4 GPU** (the free tier's T4 is enough — no need to pay
   for Colab Pro).
3. **Run everything:** **Runtime → Run all**. Confirm any "run anyway" warning
   Colab shows for notebooks not authored by Google.
4. **Runtime restart may be required (read this):**  
   Colab pre-loads older package versions into memory. After the first cell
   installs fresh packages, the notebook checks whether the loaded version is
   new enough. If it prints a *"WARNING: transformers X.X is loaded but we need
   >= 4.4"* message, do exactly what it says:  
   - **Runtime → Restart runtime** (or Ctrl+M .)  
   - Then **Runtime → Run all** again  
   
   On most current Colab instances no restart is needed, but this handles the
   edge case where it is. Once you click "Run all" after the restart the
   notebook completes without interruption.
5. **Authorize Google Drive** when the Drive mount cell runs (cell 2b). It will
   open a browser popup — allow access. This saves all checkpoints and the final
   model to your Google Drive under `My Drive/legal-bert-cuad-training/` so they
   survive if the Colab session disconnects. **Do not skip this step.**
6. **Wait.** Expect roughly **1-2 hours**. You can close the laptop lid/tab and
   check back — Colab keeps running in the background for a while, but don't
   let the browser tab stay closed for too many hours or the session may
   disconnect. If it does disconnect, your files are safe in Drive.
7. **If a cell shows a red error box:** stop there, don't try to fix it — copy
   the full error text (and the cell just above it) and send it to me. The
   notebook is written to fail loudly with clear messages rather than silently
   produce a broken model, so an error is meant to be reported, not debugged by you.
8. **Near the end**, the notebook asks you to hand off the trained model. Pick
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

9. **Copy the evaluation table** printed in the "Evaluate" step (or grab
   `cuad_classification_report.csv` from Colab's file browser on the left) —
   this is the accuracy/precision/recall/F1 table the project proposal's
   evaluation section needs. Send it along with the model.

## Troubleshooting — known errors and their fixes

### Error: `TypeError: TrainingArguments.__init__() got an unexpected keyword argument 'warmup_ratio'`  
### Error: `TypeError: TrainingArguments.__init__() got an unexpected keyword argument 'evaluation_strategy'`

These are two sides of the same version problem:

| What failed | What it means |
|---|---|
| `warmup_ratio` | Colab runtime has **old** transformers (< 4.4) cached in-process |
| `evaluation_strategy` | Colab runtime has **new** transformers (>= 4.45+) where the old name was removed |

`eval_strategy` is the current correct name (added in 4.41). `evaluation_strategy` was the old name (removed later). `warmup_ratio` is available from 4.4 onward but not before.

**Fix (already applied in the current notebook):** The notebook now:
- Computes `warmup_steps` directly (equivalent to `warmup_ratio=0.06`, works in every version)
- Tries `eval_strategy="epoch"` first; if that raises `TypeError`, falls back to `evaluation_strategy="epoch"`
- Uses `AutoConfig.from_pretrained(...)` to silence the `num_labels=42` warning

If you still get this error it means you're running an old copy of the notebook.  
**Re-upload the latest `notebooks/finetune_legal_bert_cuad.ipynb` from this repo**, then follow step 4 (runtime restart if prompted).

### Error: `ValueError: Provided path '/content/...' is not a directory` (or `NameError: name 'model' is not defined`)

**What it means:** The Colab session disconnected and reset, wiping `/content/`. The model files are gone.

**Fix:** The current notebook mounts Google Drive in step 2b and saves all checkpoints + the final model to `My Drive/legal-bert-cuad-training/`. As long as you authorized Drive access, your files are still there. Re-upload the notebook, run from the top — Drive will remount and the push cell will upload from Drive directly. No retraining needed.

If you did not authorize Drive (ran an old copy of the notebook), you need to retrain. Re-upload the latest notebook and run again — this time authorize Drive when prompted.

---

### Warning: `You passed num_labels=42 which is incompatible to the id2label map of length 2`

**What it means:** The base `nlpaueb/legal-bert-base-uncased` model was
previously fine-tuned for a 2-class task. Its old classification head is
discarded and replaced with a new randomly-initialised 42-class head.

**This is not an error.** The LOAD REPORT lines saying `UNEXPECTED` (old head
keys) and `MISSING` (`classifier.bias`, `classifier.weight`) are expected
behavior for any model you're adapting to a new task. Training will proceed
correctly.

---

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
