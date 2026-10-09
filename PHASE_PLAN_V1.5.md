# Phase Plan V1.5 — Controlled Deployment, Final Audit and Pilot Release

**Status: APPROVED — user approved the whole phase on 2026-10-09. Readiness work may proceed; public deployment remains separately gated.**  
**Version:** V1  
**Depends on:** V1.1–V1.4 complete and user-approved  
**Prepared:** 2026-10-09

## User-visible outcome

Deploy the approved Study Guide to Streamlit Community Cloud, verify its real Google Workspace login and core student/admin flows against the existing Supabase project and AI providers, document rollback and operating limits, then request explicit pilot-release approval.

This phase authorizes deployment work only after its separate pre-deployment checkpoint. Approving this phase does not by itself authorize publishing the app, changing Google OAuth production status, spending money, or destructive database actions.

## In scope

- Prepare the minimum deployment configuration and operator checklist for the existing Streamlit application.
- Verify that deployment files contain no credentials and that local secrets remain ignored.
- Record exact Streamlit Community Cloud secrets required for Google OIDC, app policy, Supabase, Gemini embeddings and AI STAR generation, using placeholders only in project files.
- Require a dedicated GitHub repository or safely scoped existing repository. The user performs repository creation, staging, commits and pushes.
- At the pre-deployment checkpoint, show the user the expected public URL exposure, external services, privacy risks, cost/capacity limits, rollback method and required secret/configuration changes.
- After explicit deployment approval, guide or perform authorized Streamlit Community Cloud setup, update the Google OAuth redirect URI to the final HTTPS callback, and configure deployment secrets without exposing them in chat or source control.
- Run read-only and bounded deployed smoke tests for sign-in/out, domain/admin authorization, document visibility, supported/refused questions, citations and private history. Any test that creates data uses clearly labeled synthetic data and removes it only with separate confirmation if deletion is required through a browser.
- Complete the final requirement-to-evidence audit with `PASS`, `FAIL`, `NOT TESTED` or `N/A` for functionality, security/privacy, reliability, performance/capacity, accessibility, dependency health, operations, rollback and documentation.
- Update `README.md`, `PROGRESS.md` and a concise `OPERATIONS.md`; request final pilot-release approval.

## Out of scope

- Architecture, schema, provider or model changes.
- New product features, LangChain, OCR, analytics, background workers or Version 2 work.
- A guarantee of 120 simultaneous answer generations; the pilot remains constrained by Community Cloud and provider limits.
- Custom domain, paid Streamlit hosting, new paid services or institution-wide rollout without separate approval.
- Git staging, commits, branches, merges, tags or pushes by Codex.
- Interview PDFs; those begin only after the deployed release is audited and approved.

## Intended deliverables and files

- `PHASE_PLAN_V1.5.md` — this approved phase contract.
- `OPERATIONS.md` — deploy, secrets checklist, health/smoke checks, incident response and rollback.
- `.streamlit/secrets.toml.example` — retain placeholders; clarify local versus deployed redirect URI if needed.
- `README.md` — deployed URL only after verified deployment, setup/run/test instructions, status and limits.
- `PROGRESS.md` — approvals, deployment evidence, audit matrix and exact restart handoff.
- Minimal hosting/runtime configuration only if the real deployment requires it. No speculative CI, Docker or provider abstraction.

## Approach and checkpoints

### 1. Deployment readiness — no external mutation

- Re-run the full automated suite, compilation, dependency consistency and OSV inventory scan.
- Inspect the deployable repository contents and secret-ignore rules.
- Confirm the entrypoint is `app.py`, pinned runtime dependencies are sufficient, and Python 3.12 is selected in Streamlit advanced settings.
- Prepare `OPERATIONS.md` and the final audit matrix.
- Confirm the final repository/branch and expected Streamlit app URL pattern.

### 2. Mandatory pre-deployment checkpoint

Stop and request explicit permission immediately before the first public deployment or cloud configuration change. Present:

- the exact GitHub repository, branch and `app.py` entrypoint;
- the proposed public Streamlit URL;
- the Google OAuth callback `https://<app-host>/oauth2callback`;
- the services receiving data and the known AI STAR retention uncertainty;
- free-tier/paid-provider limits and the absence of a class-capacity guarantee;
- rollback: disable/delete the Streamlit app, remove the deployed OAuth callback if necessary, and leave Supabase data intact unless a separately approved cleanup is requested.

The user must also complete or explicitly authorize any required GitHub push and sensitive secret entry. Secrets must be entered directly into the service UI or another approved secure channel, never copied into planning documents or chat.

### 3. Authorized deployment and verification

- Deploy from the approved GitHub coordinates using Streamlit Community Cloud.
- Set deployment secrets and the final HTTPS Google redirect URI.
- Add the same callback to the existing Google OAuth client. Publishing the Google consent application beyond its current audience is a separate explicit decision.
- Verify deployed health, sign-in/out and exact `iiti.ac.in` enforcement.
- Verify the Student and Admin navigation with the approved account(s), without performing destructive document actions.
- Use a bounded synthetic supported question and unsupported question only after confirming provider calls are acceptable; verify citation and refusal behavior.
- Verify chat ownership/history behavior with synthetic data when an appropriate second authorized account is available; otherwise mark cross-account browser testing `NOT TESTED` and rely on existing authorization tests.
- Record latency and observable provider/quota failures without claiming production capacity.

### 4. Final audit and release decision

- Trace every Must-have PRD requirement to code and executed evidence.
- Record deployment, rollback, privacy, secret handling, failure behavior, dependency, accessibility and capacity results.
- Fix only in-scope defects, rerun affected checks and the full regression suite.
- Label the result no higher than the evidence supports: development deployment, pilot candidate, or controlled pilot.
- Request explicit final pilot-release approval. No real-student invitation is implied before that approval.

## Acceptance evidence

- A real HTTPS Streamlit URL responds and the exact deployment coordinates are recorded.
- No secret is present in repository files, browser output, logs or documentation.
- Google login/logout succeeds at the deployed callback; wrong-domain access still fails closed through automated evidence, and through a real account only if an authorized test account is available.
- Admin navigation and the existing ready PDF are visible only to the allowlisted account.
- A bounded supported question returns validated page citations and an unsupported question returns the standard refusal, with no identity sent to AI providers.
- Private history is verified without exposing another user's data; unavailable real-account coverage is explicitly marked.
- Rollback steps are documented and understandable without deleting Supabase data.
- Full local regression, dependency and final audit results are recorded.
- The user explicitly approves or rejects the controlled pilot release after reviewing the evidence.

## External risks and permissions

- Streamlit Community Cloud requires a GitHub repository. The current project directory is untracked inside the broader `/Users/mohitarora` Git root, so deployment must not use that home-level repository accidentally. The user must choose/create a dedicated repository and perform all Git mutations.
- The deployed app URL becomes publicly reachable, although protected application content requires Google login and exact-domain authorization.
- Deployment sends student questions to Gemini for embeddings and sends questions, bounded chat context and retrieved course excerpts to AI STAR for generation. AI STAR retention remains unknown and was previously accepted; this risk remains visible at release.
- Gemini is paid and AI STAR consumes the purchased balance. Existing request/context/output limits remain; unexpected material cost requires a new approval.
- Streamlit Community Cloud and Supabase free services provide no class-wide uptime or concurrency guarantee. The V1.4 three-request burst is only a smoke test.
- Google OAuth callback changes, consent publishing, Streamlit deployment/secrets, paid-service changes, destructive cleanup and any public release each require explicit action-time approval where applicable.

## Current official guidance used

Streamlit documentation says Community Cloud deploys from GitHub coordinates and supports a selected Python version in advanced settings. For Google OIDC, the deployed `redirect_uri` and Google Authorized redirect URI must both use the final app URL plus `/oauth2callback`; secrets belong in Community Cloud app settings rather than the repository. Python-version replacement may require deleting and redeploying an app, so the initial deployment should select Python 3.12.

## Tools and fallback

- Use the existing pytest, compile and dependency checks.
- Use the existing Brave browser integration for authorized deployed critical-path checks; Playwright CLI still lacks its own browser and no browser package will be installed without approval.
- Use Context7/official Streamlit documentation for current deployment behavior.
- Use OSV's public API for a no-install dependency inventory scan.
- Skip Serena because this remains a small codebase; use `rg` and targeted reads.

## Model and effort forecast

- Recommended Codex route: current general coding model, medium effort; raise effort only for final security/audit findings.
- Estimated work: 5–9 human-equivalent hours plus user-controlled Git/deployment steps; approximately 2–3 context sessions and 1–2 five-hour usage windows. Exact Codex token and allowance telemetry is unavailable.
- Provider calls will be bounded to the minimum deployed smoke tests. Exact Gemini billing and AI STAR balance deduction remain unavailable from the application.

## Git checkpoint

Codex will not stage, commit, branch, merge, tag or push. Before deployment, the user must create/select a dedicated repository and review the exact file set. Suggested commands will be provided only after the repository target is known and will be scoped to this project, avoiding the current home-directory Git root.

## Approval request

Approve this whole V1.5 phase for readiness work and end-to-end execution, subject to the mandatory pre-deployment checkpoint above. Actual public deployment and cloud configuration will still pause for explicit permission after the repository, URL, risks, secrets and rollback plan are concrete.

## Approval record

The user approved the whole V1.5 phase on 2026-10-09 by replying “approve.” This authorizes the readiness work and final-audit preparation in this plan. It does not authorize a Git push, public deployment, Google OAuth configuration change, consent-screen publication, secret transmission or paid-service change.

## Readiness execution evidence

- Added `OPERATIONS.md` with the repository boundary, deployment secret placeholders, Google callback steps, deployed smoke checks, incident response, rollback and pre-deployment audit matrix.
- Added `pdfs/` to `.gitignore`; the local course PDF is not needed by the deployed app because the approved corpus is stored in private Supabase Storage. Existing ignores protect local secrets, evaluation results, the virtual environment and caches.
- `.streamlit/secrets.toml.example` now distinguishes the local callback from the final deployed HTTPS callback without containing credentials.
- Configuration validation passed without printing secrets: exact domain, HTTPS Supabase URL, and both AI provider configurations are present; the local secrets file remains owner-only (`0600`).
- Source credential-pattern scan found no credential-shaped values outside the ignored local secrets file. The deployable tree is still untracked inside the home-directory Git root, so a dedicated repository remains mandatory.
- Verification passed: 81 tests, Python compilation, `pip check`, and local Streamlit health (`HTTP 200`, about 1.4 ms). The local server was stopped afterward.
- OSV rescanned all 74 installed Python distributions and returned zero advisories.
- Readiness work is complete at the mandatory pre-deployment checkpoint. No Git operation, GitHub repository change, Google configuration change, Streamlit deployment, provider change, Supabase write or public exposure occurred.
