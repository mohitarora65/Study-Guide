# Operations — Grounded Mathematics Study Guide

**Status:** V3 and the Voyage migration are deployed. The active document was successfully re-indexed with Voyage on 2026-10-12; retrieval/citation verification remains pending.
**Last updated:** 2026-10-12

## Deployment target

- Host: Streamlit Community Cloud.
- Source: a dedicated GitHub repository, branch selected by the user, entrypoint `app.py`.
- Python: select 3.12 in Streamlit advanced settings.
- Data: the existing Supabase project, using server-held service credentials.
- Identity: the existing Google OAuth client with an exact deployed callback.
- Retrieval after migration 005 and re-index: Voyage `voyage-4-lite`, 1,024 dimensions. The legacy Gemini vector column is retained for rollback.
- Generation: AI STAR `deepseek-v4-flash` at `https://ai.starimg.ru/v1`, with one `deepseek-v4.1-flash` attempt after a timeout, network failure, HTTP 429 or HTTP 5xx response.

The project has a dedicated Git repository. The user performs all Git mutations and should still review the exact project-scoped staged diff before pushing.

## Repository boundary

Include the application, tests, migrations and planning/operating documentation. Do not include:

- `.streamlit/secrets.toml`;
- `.venv/`, caches, bytecode or evaluation result files;
- `pdfs/` or any local course PDF—the approved corpus is already stored in private Supabase Storage;
- API keys, OAuth credentials, service-role keys, cookies, tokens or copied logs.

Before each push, inspect the exact project-scoped file list and staged diff. Never use an unscoped `git add -A` from `/Users/mohitarora`.

## Required Streamlit secrets

Enter these values directly in Streamlit Community Cloud app settings. Never commit or paste their real values into documentation or chat.

```toml
[auth]
redirect_uri = "https://<final-app-host>/oauth2callback"
cookie_secret = "<new-or-approved-strong-secret-at-least-32-characters>"
client_id = "<google-oauth-client-id>"
client_secret = "<google-oauth-client-secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[app]
allowed_domain = "iiti.ac.in"
admin_emails = ["<allowlisted-iiti-admin-address>"]
user_key_secret = "<approved-strong-secret-at-least-32-characters>"

[supabase]
url = "https://<project-ref>.supabase.co"
service_role_key = "<server-only-service-role-key>"

[voyage]
api_key = "<voyage-api-key>"

[ai_star]
api_key = "<ai-star-api-key>"
```

`user_key_secret` must remain stable after real chats begin. Changing it changes derived user identifiers and makes existing chat ownership records unreachable through the app. Rotating it therefore needs a separately approved migration/retention decision. The OAuth `cookie_secret` may invalidate sessions when rotated, which is acceptable during a planned maintenance window.

## Pre-deployment checklist

1. User selects or creates a dedicated GitHub repository and branch.
2. Confirm the proposed repository contains no secrets or local PDFs.
3. Run the full tests, compilation, `pip check`, OSV inventory scan and source secret scan.
4. Confirm `app.py` is the Streamlit entrypoint and choose Python 3.12.
5. Deploy once to obtain the final HTTPS app URL.
6. Set the Community Cloud secrets with the final URL plus `/oauth2callback`.
7. Add that exact URI to the existing Google OAuth client's Authorized redirect URIs.
8. Keep the Google consent application's existing audience/status unless a separate publication decision is required and approved.
9. Restart the app and perform the bounded smoke checks below.

Steps 5–8 change external state and require the mandatory pre-deployment approval recorded in `PHASE_PLAN_V1.5.md`.

## Deployed smoke checks

Record date, tester role, result and evidence without recording secrets, identity tokens, full student identities, full question text or course excerpts.

1. Public URL returns the signed-out page over HTTPS.
2. An authorized `iiti.ac.in` account signs in and out.
3. Exact-domain rejection remains covered by automated tests; use a real wrong-domain account only if the user authorizes that account for testing.
4. Admin sees Documents and the ready PDF metadata. Do not upload, re-index or delete content during an ordinary release smoke test.
5. Student Study page renders and an approved synthetic supported question returns a validated page citation.
6. An approved synthetic unsupported question returns the standard insufficient-material response.
7. Synthetic chat history can be revisited. Deletion is tested only with an explicitly disposable synthetic thread and action-time confirmation when performed through a browser.
8. A second authorized account verifies cross-user isolation if available; otherwise record browser-level cross-account testing as `NOT TESTED` and cite the existing automated ownership tests.
9. Record response latency and any provider/quota errors. Do not extrapolate the three-request development burst into class-capacity claims.
10. Admin creates or activates one approved topic; student generates exactly seven MCQs, submits all answers and sees cited feedback.
11. Student progress shows only summary attempts and rolling mastery; admin lookup by institutional email shows the same mastery.
12. Profile deletion is tested only with an explicitly disposable synthetic quiz profile and must remove its mastery/attempt summaries.

## Routine operation

- Check Streamlit logs for safe error categories only; do not add full questions, answers, emails, tokens or course excerpts to logs.
- Check Supabase project availability/storage and provider dashboards when answer or ingestion flows fail.
- AI STAR generation stops when its balance reaches zero according to the provider/user report; the app must display its existing safe generation error.
- Study answers use the primary AI STAR model first. Only timeout/network, HTTP 429 and HTTP 5xx failures receive the single fallback attempt; authentication, request-validation and malformed-output failures remain non-retryable.
- Voyage embedding failures affect new ingestion and question retrieval. Document indexing uses six-chunk batches with 21 seconds between calls; HTTP 429 waits 61 seconds before its single bounded retry. Do not click re-index again while a run is still active.
- Do not re-index or delete the ready course document as a health check.
- Student quiz creation is local and does not consume provider balance.
- V2.2's three approved synthetic generations reached the provider's output-length limit. V2.3's Rank set and V2.5's Eigenvalues set passed manual source review. V2.8's raw SVD diagnostic stopped normally at 4,761/5,000 completion tokens and passed structural validation, but V2.9's normal application path still truncated at 6,000. The runtime cap was restored to 5,000. This variability makes further cap increases a poor reliability strategy. Do not make another call, change reasoning behavior, switch providers/models or redesign the workflow without approval; authenticated quiz browser/accessibility checks remain not tested.
- The approved redesign samples from the bundled bank. Add or change questions only after checking the answer, distractors, difficulty and cited PDF page. Unsupported topic names intentionally fail safely.
- Quiz questions are transient. Only score, mastery, difficulty mix, topic, email-linked profile and timestamps are stored.
- Apply migrations only in filename order and only after separately confirming the target project and reviewing the SQL. Future migrations require a separately approved phase.

## Voyage cutover verification

Use this only for an explicitly approved migration/cutover, not routine health checking.

1. Re-index only the currently active ready document and allow the paced run to finish without starting another attempt.
2. Confirm the Documents page shows a ready active version using `voyage-4-lite`; if indexing fails, confirm the previous Gemini version is still active.
3. Ask one approved supported Study question and verify that the answer cites the expected PDF page.
4. Ask one approved unsupported question and verify the standard insufficient-material response.
5. Verify the deployed `0.46` similarity threshold with grounded citation evidence. It is the midpoint of the observed `0.4280–0.4925` unsupported/supported gap; do not change it without repeating the approved calibration.

## Incident triage

| Symptom | First checks | Safe response |
|---|---|---|
| App unavailable | Streamlit app status/logs and recent deployment | Reboot the app; if a release caused it, roll back to the last known-good commit/deployment. |
| Login loop/failure | Final app URL, Streamlit `auth.redirect_uri`, Google authorized redirect URI | Make the URIs identical, including HTTPS and `/oauth2callback`; do not weaken domain checks. |
| All questions fail before generation | Active embedding model, Voyage allowance/rate limit/key and Supabase availability | Keep safe error output; verify the Voyage re-index completed and do not bypass retrieval or answer from model knowledge. |
| Generation fails | Primary and fallback AI STAR outcomes, balance/status/key | Keep safe error output; do not add retries or switch providers without a new approval. |
| Quiz creation fails | Exact topic name and bank capacity for the mastery mix | Add source-checked bank content or deactivate the unsupported topic; do not save an attempt. |
| Incorrect or missing citations | Retrieval/evaluation evidence and active document version | Pause pilot use if systemic; do not lower citation validation. |
| Suspected secret exposure | Affected service and repository/log surface | Disable the app if needed, rotate the specific credential, inspect exposure scope and record the incident. Never paste the credential into chat. |
| Suspected cross-user access | Owner filters, logs without content, automated isolation tests | Disable the app immediately and investigate before restoring access. |

## Rollback

1. Stop or disable the Streamlit app to end public access.
2. Redeploy the last known-good user-selected commit if the issue is code-only.
3. Remove the deployed Google OAuth redirect URI if the deployment is abandoned; preserve the local callback if local development continues.
4. Rotate only credentials that may have been exposed. Keep `user_key_secret` stable unless a migration/data-access consequence is explicitly approved.
5. Leave Supabase documents and chat data intact by default. Data deletion is separate, destructive work requiring exact targets and approval.
6. Verify the disabled/rolled-back URL and record the result in `PROGRESS.md`.

## Cost, privacy and capacity limits

- Voyage embeddings are metered; the advertised free allowance is an external policy and exact deployed usage/cost is not available from the app.
- AI STAR consumes the purchased balance with a user-reported ×0.1 multiplier and stop-at-zero behavior. Dollar pricing, expiry and storage/retention remain unverified.
- Questions go to Voyage for embedding. Questions, bounded recent conversation and retrieved excerpts go to AI STAR for generation. Names, email addresses and identity tokens are not intentionally sent.
- Starting a quiz sends no topic, course excerpt, identity or quiz content to Voyage or AI STAR.
- Streamlit Community Cloud and Supabase free services have no class-wide uptime or concurrency guarantee.
- The measured three-concurrent-request burst completed successfully, but it is not evidence for 120 simultaneous generations.

## Final audit status before deployment

| Category | Status | Evidence / remaining deployment check |
|---|---|---|
| Approved scope and planning | PASS | G0–G5 and V1.1–V1.5 phase files exist; V1.1–V1.4 are signed off and V1.5 is approved. |
| Core local functionality | PASS | V1.4 evaluation thresholds passed; current full regression must pass again before deployment. |
| Authentication/authorization | PASS locally | Google Admin login and automated domain/ownership tests passed; deployed callback and optional real wrong-domain flow remain. |
| Grounding/citations/refusal | PASS locally | TA-reviewed 40-question result passed all five PRD thresholds; A09 false refusal is accepted. |
| Security/privacy | PASS with known provider risk | Server-held secrets, private Storage, exact-domain/admin checks and prompt/citation validation exist. AI STAR retention remains unknown and accepted. |
| Dependencies | PASS locally | Latest V1.4 OSV scan covered 74 installed distributions with zero advisories after pip remediation; rerun before deployment. |
| Accessibility | PASS with limits | Light-theme contrast, keyboard focus and 390-pixel width passed. Dark theme and a separate student-account browser session were not tested. |
| Performance/capacity | PARTIAL | Health/latency/memory and a three-request answer burst were measured. Class-wide capacity is not established. |
| Deployment | PASS with pending retrieval evidence | The app is deployed from dedicated `main` and the Voyage re-index succeeded; retrieval/citation verification remains pending. |
| Rollback/operations | PASS as procedure | This document defines response and rollback; real execution remains untested until deployment. |

Final release status cannot exceed **controlled pilot candidate** until the real URL and deployed critical paths pass and the user explicitly approves release.
