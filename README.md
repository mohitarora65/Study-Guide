# Grounded Mathematics Study Guide

A Streamlit study assistant for IIT Indore's Mathematics for AI/ML course. The approved Version 1 will answer only from teaching-assistant-managed PDFs, show document/page citations and refuse when the material is insufficient.

## Current State

V1.2 adds admin-only private PDF ingestion, page-linked embeddings, document status/retry/re-index/delete controls and a server-only retrieval function. V1.3 adds grounded student answers, page citations and private chat history. V1.4 evaluation and local hardening were signed off by the user on 2026-10-09. V1.5 deployment readiness and rollback documentation are complete at the mandatory pre-deployment checkpoint. No deployment has been performed or authorized.

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

The approved target is Streamlit Community Cloud with Python 3.12, a dedicated GitHub repository and `app.py` as the entrypoint. This project is not yet deployed. Do not publish the current home-directory Git root or commit `.streamlit/secrets.toml` or `pdfs/`. See [OPERATIONS.md](OPERATIONS.md) for the secure secrets checklist, Google OAuth callback, smoke checks, incident response and rollback.

## Database Migration

Apply the migrations in filename order only after confirming the target is a development Supabase project:

1. `supabase/migrations/001_initial.sql` creates the document, ingestion and chat tables.
2. `supabase/migrations/002_ingestion.sql` adds ingestion metrics, the private `course-pdfs` bucket, atomic activation/deletion functions and active-version vector search.

Both migrations enable or preserve the server-only boundary: browser roles cannot access the tables or ingestion functions, and the source-PDF bucket is private.

## PDF Ingestion

- Admins upload one `.pdf` at a time, up to 25 MiB.
- PDFs must be readable, unencrypted and text-based. OCR is not included.
- SHA-256 duplicate detection prevents the same bytes from creating another document.
- Text stays within its real 1-based PDF page and is split into chunks of up to 1,800 characters with up to 250 characters of overlap.
- Embeddings use `gemini-embedding-2` at 768 dimensions through the official Google SDK; LangChain is intentionally not used.
- A replacement version becomes searchable only after every chunk is stored. Failed replacement attempts leave the earlier ready version active.
- Delete first removes the document from retrieval, then removes the private object and derived database rows.

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
- Stored records use a keyed opaque identity, not the student's email.
- Browser roles have no direct table access; the Streamlit server owns protected database operations.
- Secrets and full identity claims must not be logged.

## Known Limits

- No OCR, multiple-file uploads, background queue or resumable upload.
- Larger course books have not been tested. The 25 MiB cap is provisional, and Supabase recommends resumable uploads above 6 MB.
- Synthetic AI STAR checks used no student identity or saved chat; the grounded-answer check sent bounded retrieved course excerpts. AI STAR retention terms are unknown and transmission is explicitly accepted by the user.
- V1.4 live evaluation and TA scoring are complete. A09 is a user-accepted known false refusal. Brave checks confirmed the sign-in flow and authenticated Admin/Study navigation; duplicate Streamlit page paths found during testing were fixed. In light theme, application body text and the sign-in button meet WCAG AA contrast; keyboard focus and 390-pixel width were checked on the signed-out page. Dark theme and a separate student-account browser session remain untested. A three-request synthetic concurrent burst completed with 6.28–7.10 second per-request latency and citations; it is not a capacity guarantee. An OSV scan covered 74 installed Python distributions, found local pip 26.1.2 affected by [GHSA-qwm4-qh6w-59xr](https://github.com/advisories/GHSA-qwm4-qh6w-59xr), and the local installer was updated to fixed version 26.2.0. The repeat scan found no advisories. No scanner package was installed.
- No deployment has been performed.
- Streamlit Community Cloud and Supabase free hosting do not guarantee capacity or uptime for simultaneous class-wide use.
# Study-Guide
