# Grounded Mathematics Study Guide

A deployed Streamlit study assistant for IIT Indore's Mathematics for AI/ML course. It answers only from teaching-assistant-managed PDFs and includes a source-reviewed adaptive-quiz workflow.

[Live application](https://iiti-mathematics-study-guide.streamlit.app/)

## Current State

V1.2–V1.4 provide private PDF ingestion, grounded answers, citations, chat history and local hardening. V2 adds admin-managed quiz topics, seven-question MCQs, deterministic grading, rolling topic mastery, student summaries and admin progress lookup/deletion. Quiz creation samples a bundled, source-checked bank instead of waiting for live model generation. V2 is deployed from `main`; the user confirmed the corrected authenticated quiz topic UI in production on 2026-10-11.

V3 is implemented locally and its additive schema migration is applied in production, but the application changes are not deployed. It classifies uploads as Theory or Questions, assigns Mid Sem / End Sem / Class Quiz coverage, scopes Study retrieval, extracts deterministic question drafts with page provenance, requires admin review, and prefers approved uploaded questions while retaining the bundled bank as fallback.

The bundled bank contains 11 questions for each approved topic—four easy, four medium and three hard—so every mastery mix can be assembled locally. Question and option order are randomized. Unsupported topics fail safely until source-checked questions are added. See `PHASE_PLAN_QUESTION_BANK.md`.

## Requirements

- Python 3.12 deployment target (the current local verification used Python 3.13)
- A Google OAuth web client for the `iiti.ac.in` Workspace domain
- A development Supabase project
- A Gemini API key with access to `gemini-embedding-2`
- An AI STAR API key for `deepseek-v4-flash` answer generation

## Local Setup

Create a virtual environment and install the pinned dependencies:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace every placeholder locally. Never paste credentials into chat or commit `secrets.toml`.

The Google OAuth client must allow this local redirect URI:

```text
http://localhost:8501/oauth2callback
```

Generate separate strong random values for `cookie_secret` and `user_key_secret`. The Supabase service-role key is server-only and must never be exposed to browser code.

Set the Gemini key only in the local `[gemini]` section and the AI STAR key only in `[ai_star]`. Both are used server-side and are never sent to Supabase or the browser. The AI STAR request contains the question, a bounded recent conversation and retrieved course excerpts; it does not contain the student's email or account identifier. The user accepts transmission although AI STAR storage/retention terms are unknown; the reported no-training claim is unverified. The gateway is reported to deduct 0.1 balance tokens per model token and stop requests at zero; dollar pricing/balance expiry are unknown.

Run the app:

```bash
.venv/bin/streamlit run app.py
```

Without a local secrets file, the app intentionally shows a safe configuration message instead of attempting login.

## Deployment

The app is deployed on Streamlit Community Cloud from the dedicated GitHub repository's `main` branch with `app.py` as the entrypoint. Production quiz topics were aligned with the reviewed bank while preserving legacy history. Do not publish `.serena/`, `.streamlit/secrets.toml` or `pdfs/`. See [OPERATIONS.md](OPERATIONS.md) for the secure secrets checklist, Google OAuth callback, smoke checks, incident response and rollback.

## Database Migration

Apply the migrations in filename order only after confirming the target is a development Supabase project:

1. `supabase/migrations/001_initial.sql` creates the document, ingestion and chat tables.
2. `supabase/migrations/002_ingestion.sql` adds ingestion metrics, the private `course-pdfs` bucket, atomic activation/deletion functions and active-version vector search.
3. `supabase/migrations/003_adaptive_quiz.sql` adds private quiz topics, profiles, mastery and summary attempts plus atomic completion/profile-deletion functions.
4. `supabase/migrations/004_study_modes_and_questions.sql` adds document classification, private question drafts and coverage-scoped retrieval. It is prepared locally and must not be applied to production without explicit approval and a backup/rollback check.

All migrations preserve the server-only boundary: browser roles cannot access protected tables/functions, and the source-PDF bucket is private.

## Adaptive Quiz

- Admins create, rename and activate topic names.
- A student selects a topic; the server samples source-checked questions for that exact topic without a live provider call.
- Every quiz contains exactly seven unique MCQs with four distinct options, the mastery-selected difficulty mix and citations to the approved PDF pages.
- The bundled bank currently covers Rank and fundamental subspaces, Eigenvalues and eigenvectors, and Singular value decomposition. Other topic names fail safely until reviewed content is added.
- Answers are graded locally. Supabase stores only attempt summaries and rolling mastery: `60%` latest score plus `40%` previous mastery after the first attempt.
- Students see only their own progress. Admins can filter progress by institutional email and delete that quiz profile and its summary history.
- Full questions are bundled with the application and remain transient per attempt; Supabase stores no questions or answers.

## PDF Ingestion

- Admins upload one `.pdf` at a time, up to 25 MiB.
- Each upload is classified as Theory or Questions and tagged for one or more of Mid Sem, End Sem and Class Quiz. Overall is their union.
- PDFs must be readable, unencrypted and text-based. OCR is not included.
- SHA-256 duplicate detection prevents the same bytes from creating another document.
- Text stays within its real 1-based PDF page and is split into chunks of up to 1,800 characters with up to 250 characters of overlap.
- Embeddings use `gemini-embedding-2` at 768 dimensions through the official Google SDK; LangChain is intentionally not used.
- A replacement version becomes searchable only after every chunk is stored. Failed replacement attempts leave the earlier ready version active.
- Delete first removes the document from retrieval, then removes the private object and derived database rows.
- Admins explicitly extract question drafts. Question uploads are scanned broadly; Theory uploads are scanned only on pages with an explicit Questions/Exercises/Problems heading. Drafts are never student-visible until completed and approved.

## Tests

```bash
.venv/bin/python -m pytest
```

Automated tests use dummy values and do not require real credentials. Real Google login and Supabase connectivity must be smoke-tested separately after development secrets are configured.

## V1.4 Grounding Evaluation

`evaluation/questions.json` contains 25 answerable and 15 unsupported questions based on the current notes. The user confirmed TA approval of all items as written on 2026-10-09; the dataset records the review role/date and item approvals.

Validate the approved dataset locally without provider calls:

```bash
.venv/bin/python evaluation/run_evaluation.py
```

The TA-approved live set was run on 2026-10-09; four errors were retried individually. The merged results are saved at `evaluation/results/20261009T121507Z.json` (ignored by Git), and the TA-reviewed results are at `evaluation/results/20261009T122132Z-ta-reviewed.json` (also ignored by Git). The reviewed set has 40 rows with no provider errors; validity among 46 citations, citation support, refusal recall and high-risk formula review all pass. One supported question (A09) was refused despite retrieval finding its definition on page 25; the user accepted this as a known limitation.

To repeat the full live test set, use configured Gemini, AI STAR and development Supabase credentials:

```bash
.venv/bin/python evaluation/run_evaluation.py --live
```

This sends each approved question and retrieved excerpts to the configured providers, does not create chat-history records or send student identity, and pauses between requests to respect the app's rate limit. Results are saved under the Git-ignored `evaluation/results/`; provider balance deduction is not independently known. To retry only errored questions from a full result file, use `--retry-errors <result.json>` with `--live`; the runner merges those rows while preserving successful results. In the result JSON, manually set `ta_citation_supported` for each answered supported question and `ta_formula_correct` for each high-risk formula answer, then run:

```bash
.venv/bin/python evaluation/run_evaluation.py --summarize evaluation/results/20261009T122132Z-ta-reviewed.json
```

A reviewed subset can be run with `--limit N`, but it is not a full-set release result.

## Security Boundary

- Only a verified email with the exact `iiti.ac.in` domain is accepted.
- Admin access requires an exact email in the server-side allowlist.
- Chat records use only a keyed opaque identity. Quiz profiles also store the normalized institutional email so an admin can find the requested student; it is not sent to either AI provider.
- Browser roles have no direct table access; the Streamlit server owns protected database operations.
- Secrets and full identity claims must not be logged.

## Known Limits

- No OCR, multiple-file uploads, background queue or resumable upload.
- Larger course books have not been tested. The 25 MiB cap is provisional, and Supabase recommends resumable uploads above 6 MB.
- Synthetic AI STAR checks used no student identity or saved chat; the grounded-answer check sent bounded retrieved course excerpts. AI STAR retention terms are unknown and transmission is explicitly accepted by the user.
- V1.4 live evaluation and TA scoring are complete. A09 is a user-accepted known false refusal. Brave checks confirmed the sign-in flow and authenticated Admin/Study navigation; duplicate Streamlit page paths found during testing were fixed. In light theme, application body text and the sign-in button meet WCAG AA contrast; keyboard focus and 390-pixel width were checked on the signed-out page. Dark theme and a separate student-account browser session remain untested. A three-request synthetic concurrent burst completed with 6.28–7.10 second per-request latency and citations; it is not a capacity guarantee. An OSV scan covered 74 installed Python distributions, found local pip 26.1.2 affected by [GHSA-qwm4-qh6w-59xr](https://github.com/advisories/GHSA-qwm4-qh6w-59xr), and the local installer was updated to fixed version 26.2.0. The repeat scan found no advisories. No scanner package was installed.
- V2 is deployed. The user confirmed the corrected authenticated topic UI; a complete production quiz submission and student/admin progress synchronization were not explicitly recorded.
- Streamlit Community Cloud and Supabase free hosting do not guarantee capacity or uptime for simultaneous class-wide use.
- Historical live-generation trials were unreliable, so the student path now uses the bundled bank. Automated checks and source review cover all 33 questions. Quiz keyboard/focus behavior and a fully recorded production submission/progress-sync flow remain pending. See `PHASE_PLAN_QUESTION_BANK.md` and `OPERATIONS.md`.
- V3 deterministic extraction recognizes numbered questions, A–D option lines and simple answer-key lines. It does not infer answers, OCR scans, or reliably reconstruct complex multi-column layouts; admins must complete and review every extracted MCQ. The production schema is migrated; application deployment, deliberate document reclassification and authenticated browser QA are pending.
# Study-Guide
