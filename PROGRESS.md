# Project Progress

**Project:** Grounded Mathematics Study Guide  
**Project root:** `/Users/mohitarora/New projects/Study Guide`  
**State:** New project  
**Mode:** Learning / Production with a tightly scoped Version 1  
**Last updated:** 2026-10-10

## Version 2 Change Gates — Adaptive Quiz Agent

| Gate | Status | Deliverables | Evidence / next action |
|---|---|---|---|
| V2-G0 — Change discovery | COMPLETE | User decisions recorded in `PROJECT_BRIEF.md` | MCQ-only; seven fresh questions; topic selected by student from admin-managed names; semantic retrieval; feedback after submission; rolling mastery; summary history; admin visibility by institutional email. |
| V2-G1 — Change brief | APPROVED | `PROJECT_BRIEF.md` — Version 2 proposal | User replied “yes” on 2026-10-09. |
| V2-G2 — Research and PRD update | APPROVED | `RESEARCH.md`, `PRD.md` | User replied “yes” on 2026-10-09, approving the requirements, mastery formula and manual course-end deletion policy. |
| V2-G3 — Stack decision update | APPROVED | `TECH_STACK_DECISION.md` | User selected Option C (“c”) on 2026-10-10: LangChain + LangGraph. |
| V2-G4 — Architecture and design update | APPROVED | `ARCHITECTURE.md`, `DESIGN.md` | User replied “approve” on 2026-10-10. |
| V2-G5 — Roadmap update | APPROVED | `ROADMAP.md` | User said “reduce tokens rest is fine” on 2026-10-10; live evaluation reduced to three quiz generations. |
| V2-G6 — Implementation phase | COMPLETE — USER APPROVED | `PHASE_PLAN_V2.1.md` | User replied “approve v2.1” on 2026-10-10. Implementation and migration signed off; full live quiz provider reliability remains in V2.2. |
| V2-G6 — Evaluation/release-readiness phase | PARTIAL — KEPT LOCAL BY USER | `PHASE_PLAN_V2.2.md` | All three capped generations hit the provider output-length limit; no follow-up generation was requested. The later deployment request is handled as a separate proposed phase in `DEPLOYMENT_PLAN_V2.md`. |
| V2-G7 — Controlled deployment | APPROVED — WAITING FOR USER PUSH | `DEPLOYMENT_PLAN_V2.md` | User approved the plan and confirmed production Supabase ref `kjxixskoeihbitcohhuo`; expected schema/security are already present, so migration was not re-run. Verify the Community Cloud source branch, then user reviews and pushes; Git operations remain user-controlled. |

## Approval Gates

| Gate | Status | Deliverables | Evidence / next action |
|---|---|---|---|
| G0 — Startup and discovery | APPROVED | Workspace inspection and discovery answers | Approved with G1 when user replied “yes” on 2026-10-09. |
| G1 — Discovery brief | APPROVED | `PROJECT_BRIEF.md` | User replied “yes” on 2026-10-09. |
| G2 — Research and PRD | APPROVED | `RESEARCH.md`, `PRD.md` | User replied “yes” on 2026-10-09. |
| G3 — Stack decision | APPROVED | `TECH_STACK_DECISION.md` | User said “the rest is fine” and confirmed existing paid API access on 2026-10-09. |
| G4 — Architecture and design | APPROVED | `ARCHITECTURE.md`, `DESIGN.md` | User replied “yes” on 2026-10-09. |
| G5 — Project roadmap | APPROVED | `ROADMAP.md` | User replied “yes” on 2026-10-09. |
| G6 — Development phases | V1.1–V1.4 APPROVED — COMPLETE; V1.5 APPROVED — PRE-DEPLOYMENT CHECKPOINT | `PHASE_PLAN_V1.1.md`, `PHASE_PLAN_V1.2.md`, `PHASE_PLAN_V1.3.md`, `PHASE_PLAN_V1.4.md`, `PHASE_PLAN_V1.5.md`, `OPERATIONS.md` | V1.5 readiness checks and operations/rollback documentation are complete. A dedicated GitHub repository and explicit public-deployment approval are required next; no external deployment change occurred. |

Provider clarification approved on 2026-10-09: V1.2/V1.3 retrieval uses Google `gemini-embedding-2` at 768 dimensions. The user approved AI STAR `deepseek-v4-flash` at `https://ai.starimg.ru/v1`; user reports OpenAI-compatible chat completions/JSON output, a `×0.1` token-balance deduction, and request blocking at zero. The user confirmed that requests stop at zero. Dollar price, remaining balance/expiry, training claim, and storage/retention terms are not independently verified. User explicitly accepts sending student questions, bounded conversation, and retrieved excerpts despite unknown retention. Synthetic live compatibility and grounded-answer tests passed on 2026-10-09. Usage on the compatibility probe reported prompt 49/completion 61/total 169; exact balance deduction is unclear. The locally configured key was used for two approved synthetic API calls and was not printed or copied; we did not compare it with the earlier key pasted into chat, so whether it is the same credential is unknown.

## Confirmed Discovery

- Admin uploads all materials; students only ask questions.
- Approximately 120 students use individual accounts restricted to a college email domain.
- The approved college email domain is `iiti.ac.in`; the user's full address is not stored in project planning files.
- The college identity provider is Google Workspace.
- A separate AI STAR generation balance was reported as 10 million tokens. The user reports `deepseek-v4-flash`, an OpenAI-compatible chat/JSON API, ×0.1 balance deduction, and confirms requests stop at zero. Dollar price, remaining balance, expiration and retention are unknown; user accepts the retention uncertainty. No gateway secret is stored in project files.
- One Mathematics for AI/ML course and one shared PDF collection.
- Initial materials are notes plus one or two large, mostly text-searchable books.
- Answers must use only supplied material, cite document pages, use English and render LaTeX.
- When evidence is insufficient, the assistant must say so rather than answer from outside knowledge.
- Real-student deployment is intended as soon as practical with a free-tier budget.
- Python and Streamlit are familiar technologies; third-party AI processing is allowed.
- User confirmed permission to make the materials searchable for the class.

## Current Status

- Planning documents created: `PROJECT_BRIEF.md`, `RESEARCH.md`, `PRD.md`, `TECH_STACK_DECISION.md`, `ARCHITECTURE.md`, `DESIGN.md`, `ROADMAP.md`, `PHASE_PLAN.md`, `PROGRESS.md`.
- V2.1 adaptive quiz is implemented locally: admin topics, seven grounded MCQs, local grading, rolling mastery, summary-only history, student progress and admin email lookup/deletion. Migration `003_adaptive_quiz.sql` is applied to the confirmed development project. The feature is awaiting user sign-off and is not deployed.
- V1.1 application foundation, configuration boundary, authentication policy, initial schema, tests and README: implemented locally.
- Project-local `.venv`: created with installed Python 3.13 because Python 3.12 is not installed locally; code remains compatible with the approved Python 3.12 deployment target.
- External services and deployment: Google OAuth consent/login was verified. The approved additive migration was applied to Supabase project `kjxixskoeihbitcohhuo`; no provider configuration or deployment was performed.
- Current phase: V1.3 Grounded Student Assistant and Private History — **complete and user-approved** on 2026-10-09. V1.4 evaluation/security/release hardening — **complete and user-approved** on 2026-10-09. Local-only health check passed (HTTP 200, 2.2 ms; five concurrent probes ~1.0–1.2 ms); observed Streamlit Python RSS ~59 MB. Three concurrent synthetic answer calls completed in 6.28–7.10 seconds each with citations (small smoke test, not a capacity guarantee). Signed-out light-theme checks confirmed keyboard focus and no horizontal overflow at 390-pixel width; application text and button contrast passed WCAG AA. Authenticated Admin sign-in and Study/Documents navigation passed after fixing duplicate Streamlit page paths. OSV checked 74 installed Python distributions; after updating pip 26.1.2 to 26.2.0, the repeat scan found zero advisories. Dark theme and a separate student-account browser session remain untested. No schema or architecture changes. No deployment is authorized by phase close-out.
- Local secret configuration parses, is ignored by Git and has owner-only permissions (`0600`).
- The obsolete process occupying OAuth callback port `8501` was terminated with explicit approval. Study Guide now owns the port during the smoke test.
- Supabase project `kjxixskoeihbitcohhuo` was explicitly confirmed by the user as the intended development target and approved for migration. The dashboard labels its main branch `PRODUCTION`, which is Supabase's branch designation; the user confirmed this project is development-only for this application.
- Migration `supabase/migrations/001_initial.sql` completed successfully. All six tables are reachable through the server client and currently empty.
- V1.2 local implementation is complete: 53 tests pass; the supplied PDF parses as 80 pages, 81 page-bounded chunks and 50,568 extracted non-whitespace characters with no low-text pages.
- Migration `supabase/migrations/002_ingestion.sql` completed successfully on the confirmed development project. The `course-pdfs` bucket exists with private access, a 25 MiB limit and PDF-only MIME restriction.
- Generated-data live checks pass: private object upload/download/removal, atomic version activation, active-ready vector retrieval, immediate retrieval removal at delete start and final row cleanup. All generated temporary remote data was removed.
- The local Gemini key parses, remains hidden from settings representations, is ignored by Git and is protected by owner-only file permissions (`0600`). Its value was never printed or copied into project files.
- Live Gemini and Supabase checks pass: `gemini-embedding-2` returned finite 768-dimensional vectors; `pdfs/lA notes.pdf` is ready with one active version, 80 pages, 81 chunks and one private 626,231-byte source object.
- A known basis/dimension query retrieved the relevant section on PDF page 25 as the top match with 0.8687 cosine similarity and stored provenance. A duplicate ingestion created no extra document, version, run or chunks.
- The authenticated Admin page rendered the ready document, page/character/model metadata and enabled re-index/delete controls. Automated browser file selection was **NOT TESTED** because Brave requires broadening the ChatGPT extension's local-file permission; that permission was deliberately left unchanged. The same ingestion entry point passed end-to-end outside the browser.

## V2.1 Adaptive Quiz Execution Report — 2026-10-10

**Phase status:** COMPLETE — user approved on 2026-10-10. V2.2 remains the next planned phase for live quiz quality/reliability evaluation; no deployment was authorized.

- Added LangChain/LangGraph pins, normalized verified email identity, strict quiz-domain validation and a deterministic retrieve/generate/validate/one-repair graph with no graph persistence or model-controlled writes.
- Added private quiz topics/profiles/mastery/attempt-summary tables. Browser roles are revoked; atomic completion is idempotent and profile deletion cascades only quiz data.
- Synthetic development-Supabase lifecycle passed: first score `5/7` produced mastery `71`; second `7/7` produced `88`; replaying the second attempt did not increment the count; student/admin reads matched; cleanup removed the exact synthetic profile/topic.
- The first database lifecycle run exposed an ambiguous PL/pgSQL column reference. It was corrected with an explicit table alias, applied, regression-asserted and retested successfully.
- Three-call AI STAR cap respected: one small LangChain JSON compatibility call passed; two complete quiz attempts ended in the safe provider-error path after long waits. No identity was included. Evidence/output bounds were reduced for future attempts, but the cap prevented another live call.
- Deterministic tests cover exact mixes, scoring/mastery, fabricated citations, one repair, insufficient evidence, identity-free payloads, summary-only persistence and the full Streamlit generate/answer/submit/result flow.
- Verification: 91 tests pass; compileall and `pip check` pass; local Streamlit health returned HTTP 200 in 1.3 ms; signed-out page shows the quiz-email disclosure. Authenticated browser navigation and live full-quiz quality/latency remain unverified.
- No Git mutation or deployment occurred.

## V2.2 Evaluation Report — 2026-10-10

**Status:** PARTIAL — KEPT LOCAL BY USER. The three-call phase cap was respected, but provider truncation prevented every approved quiz set from completing. The user declined a follow-up provider test. A later deployment request is recorded separately in proposed `DEPLOYMENT_PLAN_V2.md`.

- All three AI STAR responses ended in `LengthFinishReasonError` with HTTP 200 at the configured output-token limit (1,800 at evaluation time); latencies were 11.85 s, 13.27 s and 10.32 s. No retry or repair call was made. The limit was raised to 3,500 and covered by tests, but that fix is not live-verified.
- The three-question matrix produced zero complete sets; no question-quality review or release-readiness claim is possible. Failure metadata is in ignored `evaluation/quiz_results/v22_20261010.json`.
- 97 tests pass; compilation, `pip check`, `git diff --check` and local Streamlit health check pass. Streamlit UI tests cover student-only navigation, student quiz submission, student mastery/history, admin email filtering and topic creation. Deprecated quiz table sizing arguments were updated. Synthetic database idempotency/admin lookup/mastery and exact-data cleanup passed.
- The real browser showed the signed-out page; authenticated browser flows and quiz-specific accessibility remain untested. No V2 deployment or Git operation occurred; do not deploy V2 based on this evaluation.

The user later requested deployment. This request does not change V2.2's partial evaluation result; deployment prerequisites and separate production migration approval are tracked in `DEPLOYMENT_PLAN_V2.md`.

## V1.2 Execution Report

**Phase / Version / Result:** V1.2 / Version 1 / **PASS WITH ONE UI-AUTOMATION LIMITATION — USER APPROVED 2026-10-09**.

### Completed

- Admin-only PDF validation, private upload, page extraction, low-text warnings and page-bounded chunking.
- Direct `gemini-embedding-2` calls at 768 dimensions with bounded transient retry; no LangChain or provider abstraction.
- Private `course-pdfs` bucket, atomic active-version transition, active-ready pgvector search and deletion-first unavailability.
- Duplicate detection, failed-run retry, re-index orchestration, safe deletion and safe operator-facing errors.
- Admin library/status/actions UI and secret-safe optional Gemini configuration.
- Provider-role planning clarification: Gemini embeddings are approved for V1.2/V1.3 retrieval; the user approved AI STAR `deepseek-v4-flash` generation. Live synthetic compatibility and grounded-answer smoke tests passed using the configured local key.

### Verification Executed

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 53 tests in 1.24 seconds. |
| `.venv/bin/python -m compileall -q app.py study_guide tests` | PASS. |
| `.venv/bin/pip check` | PASS — no broken requirements. |
| Real PDF preparation | PASS — 80 pages, 81 chunks, 50,568 non-whitespace characters, no low-text pages. |
| Gemini smoke test | PASS — `gemini-embedding-2`, one finite 768-dimensional vector. |
| Full development ingestion | PASS — ready in 12.48 seconds; three embedding requests; 66,515 submitted characters including retrieval instructions. |
| Supabase final state | PASS — 1 document, 1 ready active version, 81 chunks, 1 ready run, no safe error. |
| Private Storage | PASS — private bucket, 25 MiB limit, one 626,231-byte source object. |
| Semantic retrieval | PASS — basis/dimension query returned page 25 first at 0.8687 similarity. |
| Duplicate ingestion | PASS — no additional document, version, run, chunks or Gemini call. |
| Generated lifecycle test | PASS — activation made content searchable; delete start hid it; temporary rows/object removed. |
| Authenticated Admin page | PASS — ready status and metadata visible; re-index/delete enabled. |
| Browser-driven file selection | NOT TESTED — requires widening Brave extension local-file access; permission was not changed. |

### Cost and Storage Evidence

- Google currently lists standard `gemini-embedding-2` text input at $0.20 per million tokens. Exact billed tokens/charge were not exposed by the current wrapper; no duplicate full-corpus embedding was made solely for telemetry.
- Three standard embedding requests carried 66,515 characters for the corpus; expected cost remains under one US cent.
- Raw float32 vector values occupy approximately 248,832 bytes (243 KiB), excluding PostgreSQL/HNSW/text overhead.
- The temporary local review server was stopped after testing.

## V1.1 Execution Report

**Phase / Version / Result:** V1.1 / Version 1 / **PASS — USER APPROVED 2026-10-09**.

### Completed

- `app.py`: safe unconfigured state, Google sign-in entry, fail-closed authenticated boundary and role-aware navigation.
- `study_guide/config.py`: strict Google/domain/admin/Supabase configuration validation with secret-safe representations.
- `study_guide/auth.py`: verified exact-domain policy, server-side admin allowlist and stable HMAC-based opaque user key.
- `study_guide/database.py`: server-only Supabase client and safe development connection check.
- `supabase/migrations/001_initial.sql`: document/version/chunk/ingestion/thread/message schema, 768-dimension pgvector index, ownership fields, RLS and browser-role revocation.
- `.streamlit/secrets.toml.example`, `.gitignore`, pinned `requirements.txt` and `README.md`.
- Focused AppTest, authentication, configuration, database-error and schema tests.

### Verification Executed

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 32 tests in 0.81 seconds, including isolation from real local secrets. |
| `.venv/bin/pip check` | PASS — no broken requirements. |
| `.venv/bin/python -m compileall -q app.py study_guide tests` | PASS. |
| Streamlit start + `/_stcore/health` | PASS — returned `ok`; review server was stopped after V1.1 sign-off. |
| Secret-pattern scan outside `.venv` | PASS — no matching API keys/private-key blocks. |
| Local secrets validation | PASS — configuration parses; secret file is ignored by Git and restricted to owner access (`0600`). |
| Configured sign-in page | PASS — real browser rendered the title, exact-domain notice and Google sign-in button on configured port `8501`. |
| Real Google Workspace login | PASS — the configured IIT Indore account completed Google consent/callback and reached the Study page with Admin navigation. |
| Wrong-domain real-provider login | NOT TESTED — no non-IIT account was submitted to the app; pure claim rejection tests pass. |
| Apply migration to development Supabase | PASS — user confirmed project `kjxixskoeihbitcohhuo` and approved the write; SQL Editor reported `Success. No rows returned`. |
| Development Supabase connection | PASS — server client read all six migrated tables; each is reachable and contains zero rows. The authenticated Admin page also reports the database is reachable. |

### Tools and Usage

- Context7: current Streamlit OIDC/navigation/AppTest and Supabase Python client documentation.
- PyPI metadata: verified and pinned `streamlit 1.65.0`, `Authlib 1.8.0`, `supabase 2.32.0`, and `pytest 9.1.1`.
- pytest, Streamlit AppTest, dependency check, compilation and localhost health check.
- Playwright CLI was attempted but its Chrome distribution is not installed. The available Brave browser integration provided equivalent visible-page evidence without installing software.
- Serena was skipped because the codebase remains small.
- Exact Codex serving model, reasoning effort, tokens and five-hour allowance were not exposed. Work used the current session; no measurable provider usage value is available.

### Git State

The Git root resolves to `/Users/mohitarora`, above the project, and this whole project directory is currently untracked. No Git mutation was performed. Any future staging command must name this project explicitly and avoid unrelated home-directory files.

## Latest V1.4 Hardening Update — 2026-10-09

- Replaced low-contrast caption styling in `app.py`; light-theme body copy/button contrast was checked in Brave. Authenticated IIT Admin login exposed duplicate inferred `<lambda>` page paths; `study` and `documents` paths are now explicit and covered by a regression test.
- Read-only authenticated Study and Documents navigation rendered successfully. No question was sent; no Supabase write was made.
- Three concurrent synthetic answer requests completed in 6.28, 6.59 and 7.10 seconds, each with citations. This is only a small burst test, not representative class capacity.
- OSV batch audit covered 74 installed Python distributions. It found pip 26.1.2 affected by GHSA-qwm4-qh6w-59xr / PYSEC-2026-3721. After the user's approval, local pip was updated to 26.2.0; the repeat scan found zero advisories. No audit package was installed.
- Verification after the routing fix: 81 tests passed; compileall and pip check passed. Local app server stopped after the check. No deployment, Supabase write, schema change, install, or Git operation occurred.
- Known limitations at approved close-out: dark-theme contrast and separate student-account browser flow are not tested; the three-request burst is not a class-capacity guarantee. No deployment is authorized.

## V1.5 Pre-deployment Checkpoint — 2026-10-09

- User approved the whole V1.5 phase. Public deployment, Git push, Google OAuth changes, consent publication, secret transmission and paid-service changes remain separately gated.
- Added `OPERATIONS.md` with repository boundaries, secure secret-entry checklist, final callback configuration, deployed smoke checks, incident response, rollback and a final audit matrix.
- Added `pdfs/` to `.gitignore`; the local course PDF, secrets, evaluation results, environment and caches are excluded. The indexed course source remains in private Supabase Storage.
- Deployment configuration validation passed without exposing values. `.streamlit/secrets.toml` remains owner-only (`0600`), and a source scan found no credential-shaped values outside it.
- Release checks: 81 tests passed in 1.43 seconds; compileall and `pip check` passed; OSV scanned 74 distributions with zero advisories; local Streamlit health returned HTTP 200 in 1.4 ms. The local server was stopped.
- Current blocker/checkpoint: Streamlit Community Cloud requires GitHub coordinates. This project remains untracked inside the broader `/Users/mohitarora` Git root. The user must create/select a dedicated repository and perform all Git operations before the public deployment decision can be made.
- No Git mutation, GitHub change, Streamlit deployment, Google configuration change, Supabase write, provider change or public exposure occurred.

## Restart Handoff (historical snapshot; the latest hardening update above supersedes its pending-check list)

V1.1, V1.2 and V1.3 are signed off. V1.4 is user-approved and PARTIAL. The user confirmed TA approval of all 40 questions as written on 2026-10-09; `evaluation/questions.json` records 25 supported and 15 unsupported questions as approved. Full live evaluation plus four targeted retries are merged at `evaluation/results/20261009T121507Z.json`; the user confirmed the 24 generated supported answers/citations and 11 high-risk formula answers are correct, recorded in `evaluation/results/20261009T122132Z-ta-reviewed.json` (both Git-ignored). Final summary: zero provider errors, 100% validity among 46 citations, 100% citation support, 100% refusal recall, 0% unsupported answers, zero formula errors; all five automated thresholds pass. A09 remains a supported-question refusal; user accepted it as a known limitation on 2026-10-09. PDF page 25 explicitly defines a basis as independent vectors spanning the space; one retrieval-only diagnostic returned that page at 0.836 similarity. It used Gemini embedding and Supabase read, no answer generation or database write. Median answer/retrieval duration was 12.04 s and maximum 41.132 s. Full suite: 80 passed; `compileall` and `pip check` passed. Local-only Streamlit health returned HTTP 200 in 2.2 ms; five concurrent health probes returned 200 in ~1.0–1.2 ms; the server process used ~59 MB RSS. These are not answer-generation or deployed load measurements. A signed-out Brave browser check confirmed sign-in keyboard reachability and visible focus, plus no horizontal overflow at 390-pixel width; contrast and authenticated flows remain untested. Playwright CLI has no Chromium binary; no browser was installed. A targeted direct-advisory review found pinned pypdf 6.19.0 is at the patched floor for three recent advisories and Streamlit 1.65.0 exceeds the fixed version for a Windows-only advisory; this is not a full or transitive dependency audit. No Supabase writes, deployment, schema changes or Git mutations occurred in V1.4. Earlier approved synthetic calls used the configured AI STAR key; it was not printed/copied, and whether it matches the earlier pasted key is unknown. Next: finish contrast/authenticated browser checks, representative capacity measurements and full dependency audit.
