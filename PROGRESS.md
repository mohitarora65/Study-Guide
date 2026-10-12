# Project Progress

**Project:** Grounded Mathematics Study Guide  
**Project root:** `/Users/mohitarora/New projects/Study Guide`  
**State:** Completed deployed MVP
**Mode:** Learning / Production with a tightly scoped Version 1  
**Last updated:** 2026-10-12

## Ingestion Failure Investigation — 2026-10-12

**Structural chunking follow-up — LOCAL PASS / USER_REVIEW_PENDING:** after reviewing alternatives, the user said “ok lets do this then” and then `approve` for `PHASE_PLAN_STRUCTURAL_CHUNKING.md`. Fixed 1,800-character windows were replaced locally with standard-library page-bounded structural splitting: paragraph, numbered/bulleted-list and sentence boundaries; greedy packing up to 2,400 characters; complete trailing-unit overlap up to 250 characters; and deterministic non-overlapping hard splits for oversized units. PDF page, per-page order, SHA-256 hash, embedding, storage and retrieval contracts remain unchanged. README and focused tests were updated. Verification passed: 22 ingestion tests in 0.30 seconds, 135 full tests in 2.33 seconds, assert-based empty/short/unpunctuated/paragraph/list samples, compilation, `pip check`, and `git diff --check`. User-reported difficulty: fixed chunking was considered as an alternative after chunks could not be created. Agent-observed difficulties: the first test assumed only one repeated sentence although two fit the overlap budget; the assertion now verifies the bounded complete-unit shared suffix/prefix. An ad hoc uniqueness check was invalid because repeated source passages may legitimately share content hashes; database identity remains version/page/order. Lesson: test semantic invariants, not an incidental number of overlapping units or unique source text. Existing active chunks are unchanged; adoption requires a separately authorized re-index after Gemini quota is available. No provider request, production/database write, quota/billing change, dependency installation, deployment or Git mutation occurred in this phase.

**Initial diagnosis — COMPLETE:** the user reported that the website could not create chunks. Read-only production metadata verified one failed document with `EMBEDDING_FAILED`, zero stored chunks, and a failed run with zero processed pages/chunks. The existing ready document remains healthy with 80 pages and 81 chunks using `gemini-embedding-2` at 768 dimensions. Code tracing confirms chunk text is prepared before embedding and persisted only afterward, so the observed run failed at the embedding boundary before `insert_chunks` or activation. Current official Google documentation still lists `gemini-embedding-2` and the configured dimensionality field. The user replied `approve` on 2026-10-12, approving `PHASE_PLAN_INGESTION_REPAIR.md` and exactly one tiny synthetic embedding request using the existing configuration. That request contained no course material, failed locally in 0.03 seconds with a plain `RuntimeError`, and produced no HTTP/provider status; it therefore did not verify quota, authentication, model access, or rate limiting. Offline SDK request construction succeeds. Git history verifies the embedding model, batch size, and request path are unchanged since the healthy production ingestion. Focused verification passed: 19 ingestion tests in 0.35 seconds, compilation, `pip check`, and `git diff --check`. User-reported difficulty: chunks were not created. Agent-observed difficulty: the approved diagnostic failed in the local execution environment before a provider response, while production retained only a safe error code. No production write, real-document provider call, deployment, installation, application-code change, or Git mutation occurred during this initial diagnostic.

**Approved retry result — BLOCKED BY EXTERNAL QUOTA:** the user replied `approve` and authorized retrying the one production document marked `EMBEDDING_FAILED`. The retry loaded and extracted the private PDF and reached Gemini; Gemini returned HTTP 429 `RESOURCE_EXHAUSTED`, explicitly reporting that the configured project exceeded its current quota. Postflight verified safe rollback state: document/version/run are `failed`, `safe_error=EMBEDDING_FAILED`, zero chunks, zero processed pages/chunks, and no active version. No partial index became searchable. PDF extraction also emitted missing-`fontTools` and high Form XObject warnings, but it reached embedding; these warnings are not the verified failure cause, and no package was installed. The smallest local correction maps provider status/code 429 to `EMBEDDING_QUOTA_EXCEEDED`, retains the bounded retry, hides private provider detail, and gives actionable UI guidance to retry after quota resets or is increased. This correction is local and not deployed. Verification: 20 focused ingestion tests passed in 0.34 seconds; full suite 133 passed in 2.93 seconds; compilation, `pip check`, and `git diff --check` passed. User-reported difficulty: chunks were not created. Agent-observed cause: exhausted Gemini quota. Fix/lesson: distinguish safe operational causes instead of collapsing every provider failure, while keeping atomic failure state. Remaining blocker: the account owner must wait for quota reset or increase/restore Gemini quota, then authorize or perform another retry. No billing/quota/account change, provider/model change, dependency installation, deployment, or Git mutation occurred.

## Project Closed — 2026-10-11

**Status:** COMPLETE — deployed MVP accepted by the user. The user said “done, lets end this project.”

- Git checkpoint: local `main` and `origin/main` both point to `fae56c0` (`polish study and quiz UI`). Codex performed no Git mutation.
- Final local verification: 132 tests passed in 2.84 seconds; compilation, `pip check` and `git diff --check` passed.
- Final production smoke: the authenticated Streamlit app rendered “Let’s resolve your doubt,” the course-material question placeholder and chat rename control; Quiz rendered “Let’s test” with Quick Quiz and Create Custom Quiz; Documents displayed the 25 MB uploader limit.
- No form was submitted and no provider call, database write, upload, deletion, configuration change or deployment action was performed during close-out.
- Known limits remain documented in `README.md`: no fresh end-to-end custom-quiz submission was made during this close-out; class-wide capacity, dark theme, OCR and complex extraction layouts remain outside verified scope.
- Difficulties: user-reported none. Agent-observed: the browser text wait timed out before Streamlit finished rendering, but fresh page-state inspection confirmed each deployed control; no product defect was observed.

## Final Interview Preparation — 2026-10-11

**Choice:** BOTH — user selected PPT and revision pack.

- Revision notes: `docs/interview/PROJECT_REVISION_NOTES.md` — complete.
- Question bank: `docs/interview/PROJECT_INTERVIEW_200_QA.tex` and compiled PDF — complete; exactly 200 distinct answered questions, with Q001–Q150 technical and Q151–Q200 decision/reflection.
- Presentation: user selected design 3, Coral Minimal. `docs/interview/PROJECT_INTERVIEW_PRESENTATION.tex` and its compiled PDF are complete.
- Verification: the final 16:9 presentation compiles without warnings to 20 slides. Every slide was rendered and inspected individually, followed by a full-deck contact-sheet review; no clipping, overlap, missing glyph, or broken layout was observed. The interview bank compiles to a 25-page Letter PDF with a table of contents and page numbers, and all 200 question labels and numbers were validated.
- Difficulties: user-reported none. Agent-observed: Beamer overlays initially doubled preview page counts, one long question heading exceeded the line width, and justified table columns created uneven spacing. Static preview lists, tolerant paragraph wrapping, and ragged-right table columns fixed the issues; recompilation and render review passed.

## Final UI and Project Close-out — 2026-10-11

**Status:** COMPLETE / DEPLOYED. The user approved `PHASE_PLAN_FINAL_UI.md`, committed and pushed the result, and accepted project close-out.

- Study now uses “Let’s resolve your doubt” and “Ask a question from your course material…”. New chats accept an optional 80-character name and otherwise use the first question; saved chats can be renamed through an owner-scoped database update.
- Quiz now uses “Let’s test”. The existing seven-question Quick Quiz still persists its summary and mastery. Create Custom Quiz selects one or more reviewed topics, 5/7/10 questions and one or more difficulties, displays all questions together, and keeps its result session-only without calling the attempt/mastery write.
- Both quiz modes now show score, correct/incorrect totals, per-difficulty results, explanations and citations; Quick Quiz also shows updated mastery.
- Streamlit's displayed upload limit is now 25 MB, matching the existing 25 MiB application/storage boundary.
- Verification: 132 tests passed in 2.47 seconds; compilation, `pip check` and `git diff --check` passed. A temporary Streamlit server returned `ok` on port 8514 and was stopped. The Playwright CLI could not launch because Google Chrome is absent; the connected Brave browser rendered the local signed-out page instead. Authenticated UI behavior is covered by synthetic AppTests, not a fresh real-account browser run.
- Difficulties: user-reported none. Agent-observed: the new Quiz Type radio changed an older UI control count; the assertion was corrected to count answer radios only. The local port 8514 did not match the configured OAuth callback origin, so no login was attempted. No provider request, production/database write, installation, Git mutation or deployment occurred.
- Close-out smoke testing confirmed the deployed controls listed above. No additional project phase is planned.

## Version 3 Discovery — Structured Study Modes and Question Extraction

**Status:** DEPLOYED; PRODUCTION MIGRATION PASS — `DELEGATED_DECISION`, 2026-10-11. The user requested separate Theory/Questions uploads, question extraction that prioritizes question material while also using explicit question sections in theory, and Mid Sem, End Sem, Quiz and Overall study modes. `PHASE_PLAN_V3.md` records the bounded design. Commit `2f8c4be` contains the V3 application and is included in deployed `main` commit `6608c79`.

**V3 decision 1 — USER_APPROVED, 2026-10-11:** the user replied “approve” to the mandatory review recommendation. Every extracted question must remain non-student-visible until an admin explicitly approves it. This is a product decision only; no implementation or external change occurred.

**V3 autopilot — AUTOPILOT_ACTIVE / DELEGATED_DECISION, 2026-10-11:** direct trigger `bhai tu sambhal ab`. Locally implement deterministic extraction, complete-MCQ-only approval, multi-tag coverage, “Class Quiz” wording, Overall as union and reviewed-bank fallback. No new provider or dependency. Queue migration application, production classification, deployment and all Git mutations separately.

**V3.1–V3.4 — LOCAL PASS / USER_REVIEW_PENDING, 2026-10-11:** implemented document type/coverage metadata, Overall-default shared mode selection, coverage-scoped Study retrieval, deterministic numbered-question/A–D/inline-answer extraction, private source-linked drafts, explicit admin extraction, draft edit/approve/reject UI, and approved-upload-first quiz sampling with the 33-question bank as fallback. New uploaded-only topics become available when approved questions exist. Migration `004` was subsequently applied as recorded below; the application changes remain local.

**V3 verification:** `.venv/bin/python -m pytest -q` PASS — 126 tests in 2.30s; `compileall` PASS; `pip check` PASS; `git diff --check` PASS after one Markdown EOF fix; temporary Streamlit server health returned `ok` on port 8513 and was stopped. No provider request, database read/write, migration, deployment or Git mutation occurred.

**V3 difficulties:** user-reported: none during this phase. Agent-observed: the first localhost bind was denied by the filesystem/network sandbox; the approved scoped Streamlit command started successfully and health passed. An initial navigation regression expected six admin routes; the new review route caused the sole test failure (115 passed, 1 failed), and updating the intended route contract produced a full pass. SQL was reviewed and asserted as text but not executed against PostgreSQL, so runtime migration compatibility remains unverified.

**V3 pending actions:** (1) user reviews, stages, commits and pushes the V3 work; (2) Streamlit deploys that pushed revision; (3) run an authenticated extraction/review/quiz smoke test; (4) deliberately reclassify existing documents only if desired. Deployment and production data changes remain HIGH effects requiring specific approval; all Git staging/commit/push remains user-only.

**V3 production migration — USER_APPROVED / PASS, 2026-10-11:** user replied `approve` to the specific request to apply `004_study_modes_and_questions.sql` to the current Supabase production project. Preflight found the V3 table, columns and RPC absent. The migration ran in an explicit transaction; Supabase reported success. Postflight verified the table/RPC exist, RLS is enabled, browser roles have neither table SELECT nor RPC EXECUTE, and `service_role` has the intended table/RPC access. The one existing document safely defaulted to `theory` with Mid Sem, End Sem and Class Quiz tags; `question_candidates` is empty. No document content, chat, quiz attempt, mastery, auth setting, storage object or provider state was changed. A malformed read-only verification caused by stale SQL-editor content failed before execution; the same check in a fresh tab passed. Rollback was not run because it would remove the newly created schema. Remaining HIGH/user-controlled sequence: user Git commit/push, Streamlit deployment triggered by that push, then authenticated V3 smoke testing and deliberate reclassification of existing documents if desired.

**V3 pre-deployment refresh — PASS / USER GIT ACTION REQUIRED, 2026-10-11:** corrected stale documentation that still described migration `004` as unapplied. Fresh local verification passed: 126 tests in 2.74 seconds, compilation, `pip check` and `git diff --check`. A source scan found no credential-shaped values outside ignored secrets/artifacts. The worktree contains the V3 implementation plus earlier uncommitted V2 plans/evaluation helpers and user-owned contract changes, so the user must review the complete staged set before committing. No Git mutation, deployment, browser login, provider call or production read/write occurred. Agent-observed difficulty: documentation had diverged from the completed migration state; the fix was limited to status text and verified by the checks above. User-reported difficulty: none in this continuation. Next: user-controlled review/stage/commit/push, then deployed authenticated V3 smoke testing.

**V3 deployment — USER_APPROVED / USER GIT ACTION REQUIRED, 2026-10-11:** the user replied `approve` after the verified pre-deployment handoff. This authorizes the V3 Streamlit deployment and post-deploy smoke testing, but does not override the project rule that all Git mutations are user-run. No deployment occurred from this approval alone. Next: the user reviews, stages, commits and pushes the intended worktree changes; Streamlit can then deploy the pushed `main` revision.

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
| V2-G6 — Bounded reliability follow-up | COMPLETE — LOCAL; BROWSER QA NOT TESTED | `PHASE_PLAN_V2.3.md` | User approved on 2026-10-10. One quiz set passed manual review after a prompt fix; 98 tests pass. Two AI STAR calls and one Gemini embedding used. Authenticated browser/accessibility checks remain untested; no production, Git, migration or deployment actions. |
| V2-G6 — Remaining topic and local UI QA | PARTIAL — PROVIDER FAILURES | `PHASE_PLAN_V2.4.md` | Two AI STAR calls used (one per topic), both returned safe temporary-unavailable errors; zero embeddings. 98 tests pass. No topic content was validated; V2 is not release-ready. |
| V2-G6 — Provider reliability and quiz UI QA | PARTIAL — SVD OUTPUT TRUNCATED | `PHASE_PLAN_V2.5.md` | Two AI STAR calls used: Eigenvalues passed structural and manual source review; SVD returned `LengthFinishReasonError` at HTTP 200. 98 tests pass; zero embeddings/database access. Browser auth remains untested. |
| V2-G6 — Compact quiz output and SVD retest | PARTIAL — OUTPUT STILL TRUNCATED | `PHASE_PLAN_V2.6.md` | Concision instruction and regression assertion added; one SVD call still returned `LengthFinishReasonError` at HTTP 200. 98 tests pass. No retry or database/production/Git action. |
| V2-G6 — Higher-cap SVD verification | PARTIAL — STILL TRUNCATED | `PHASE_PLAN_V2.7.md` | Cap raised to 5,000; the one SVD call still returned `LengthFinishReasonError` at HTTP 200. 98 tests pass. No retry, DB/browser/production, Git or deployment. |
| V2-G6 — Raw SVD provider diagnostic | COMPLETE — STRUCTURE PASS; LOW HEADROOM | `PHASE_PLAN_V2.8.md` | One raw SVD call stopped normally at 4,761/5,000 completion tokens; 1,743-character content parsed and passed quiz validation. Content was not stored, so mathematical quality remains unreviewed. 98 tests pass. |
| V2-G6 — Reviewed SVD verification | PARTIAL — NORMAL PATH TRUNCATED | `PHASE_PLAN_V2.9.md` | One normal-path SVD call at 6,000 tokens still returned `LengthFinishReasonError`; no set could be reviewed. Runtime cap restored to 5,000. 98 tests pass; no retry or external state change. |
| V2-G6 — Low-effort SVD reliability check | PARTIAL — VALIDATION FAILURE | `PHASE_PLAN_V2.10.md` | One actual provider request returned content without truncation, but validation failed and the capped runner blocked repair. The low-effort runtime change was removed; SVD remains unverified. |
| V2-G6 — Quiz-model reliability check | PARTIAL — MEDIUM BATCH TIMED OUT | `PHASE_PLAN_QUIZ_MODEL.md` | User approved `gpt-5.6-luna` from AI STAR's live catalog for one bounded SVD evaluation. Easy passed in 6.40s; medium timed out at 30.01s; hard was skipped. The existing quiz model was restored. |
| V2-G6 — Reviewed question-bank redesign | SOURCE REVIEW COMPLETE — USER SIGN-OFF PENDING | `PHASE_PLAN_QUESTION_BANK.md` | User approved the content-review pass. All 33 answers, explanations and cited pages were visually checked; one Rank question was clarified to use pivot columns from the original matrix. All mastery mixes and 116 tests pass locally; owner/TA sign-off and authenticated browser QA remain. |
| V2-G7 — Controlled deployment | APPROVED — BLOCKED; NO PUSH | `DEPLOYMENT_PLAN_V2.md` | Production schema/security passed read-only checks. V2.9 still truncated at 6,000; SVD content review and authenticated quiz-flow evidence are missing. Runtime cap restored to 5,000. Git remains user-controlled. |

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

## Autopilot Handoff — 2026-10-10

- **Mode:** `AUTOPILOT_ACTIVE`, triggered directly by the user with “bhai tu sambhal ab” on 2026-10-10. Scope: continue safe local V2 readiness work, research, documentation and verification. Preserve existing worktree changes. No unattended work continues outside an active session.
- **DELEGATED_DECISION:** Prefer a read-only check of current official provider/API behavior before proposing another SVD test. Rationale: repeated output-cap increases failed, and a provider reasoning control may address the measured token variance without changing the model or workflow. This decision was within local/read-only scope.
- **Observed finding:** Current official DeepSeek Chat Completions docs describe reasoning effort `low`/`high`/`max`, with default `high`, plus JSON output and `max_tokens`. LangChain `ChatOpenAI` supports provider-specific parameters. This does not establish AI STAR relay support. Research references: [DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/), [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/), and [LangChain ChatOpenAI reference](https://reference.langchain.com/python/langchain-openai/chat_models/base/BaseChatOpenAI/extra_body).
- **Relay documentation check:** A targeted public search did not surface official AI STAR API documentation for this parameter. This is inconclusive; only an approved request through the relay can verify pass-through.
- **Bounded phase prepared and executed:** `PHASE_PLAN_V2.10.md` records the approved low-effort SVD request at the current 5,000-token cap and its validation failure.
- **Safe verification during this session:** `.venv/bin/python -m pytest -q` — PASS, 98 tests in 2.93s; `.venv/bin/python -m compileall -q app.py study_guide tests` — PASS; `.venv/bin/pip check` — PASS, no broken requirements. Pip cache warning only: the user cache directory is not writable, so cache was disabled. No code change was made.
- **Authorization granted:** user replied “approve” on 2026-10-10 for the request-parameter behavior change and at most one AI STAR generation request (up to 5,000 output tokens; balance/dollar charge unknown) to test relay compatibility and review SVD.
- **Still blocked:** authenticated quiz browser-flow evidence has no authorized test-safe account/data target. V2 deployment remains blocked; no push or production change is authorized here. User-only Git actions remain user-run.
- **Difficulties:** no new user-reported difficulty. Agent-observed: upstream completion truncation persists at a 6,000-token cap; official DeepSeek reasoning controls are documented, but their support through AI STAR is unverified. No fix or provider verification is claimed yet.
- **V2.10 result:** the sandboxed attempt failed locally in 0.06 seconds and did not reach the provider. The approved network attempt returned content after 54.29 seconds with no length/rejected-parameter exception, then failed existing quiz validation and requested repair. The one-call cap blocked repair. Zero embeddings/database calls; no questions were retained. The low-effort runtime change was removed because a usable SVD set was not verified.
- **V2.10 verification:** focused quiz tests passed (7). After restoring the prior runtime request settings, the full suite passed (98 tests in 2.46s); `compileall`, `pip check` and `git diff --check` passed. Pip emitted only the known non-writable user-cache warning and reported no broken requirements.

### V2.11 result — 2026-10-10

User replied “approve” for the proposed two-call maximum. One low-effort SVD request produced seven structurally valid questions in 15.44 seconds with the required 1/3/3 labels. No repair, embedding or database call occurred. Manual source review failed Q6: two distinct options are algebraically equivalent because scalar multiplication commutes. Other keyed answers/citations are source-supported; hard labels mostly cover recall. The temporary request change was removed because the set did not pass source review. Artifact: ignored `evaluation/quiz_results/v211_svd_review.json`. Agent-observed lesson: text uniqueness does not guarantee mathematically distinct options. No new user-reported difficulty. V2 deployment remains blocked.

### Pending authorizations

**Deployment continuation — USER_APPROVED / USER GIT ACTION REQUIRED, 2026-10-10:** after receiving the source-review result and next-gate explanation, the user directed “thik hai ab aage ka kaam kro and jaldi deploy kro.” This authorizes the controlled deployment direction, but does not override the project rule that all Git mutations are user-run. Pre-deploy local evidence: 116 tests passed in 2.66 seconds; compilation, `pip check` and `git diff --check` passed; the source secret-pattern scan returned no matches outside explicitly excluded secrets/artifacts; local Streamlit health returned `ok` on ports 8501 and 8502; the public URL returned Streamlit's authentication redirect. Added `graphify-out/` and `.serena/` to `.gitignore` to prevent accidental publication of local tooling artifacts. Browser automation was unavailable, so authenticated quiz/browser QA remains NOT TESTED. No production database write, credential/OAuth change, Git mutation or deployment was performed by Codex. Next action is the user-controlled review/stage/commit/push checkpoint, followed by deployed smoke testing.

**Git checkpoint completed by user / remote verified, 2026-10-10:** after the user reported “done,” read-only local and remote checks confirmed `main` and `feature/adaptive-quiz-v2` both point to `f14b88f` (`deploy reviewed adaptive quiz question bank`). The public Streamlit endpoint remains reachable and returns its expected authentication redirect, but the protected endpoint exposes no commit identifier and redirects `/_stcore/health` as well. Therefore build completion and the authenticated quiz flow remain NOT TESTED rather than assumed. Codex made no Git mutation or production write.

**Production quiz-topic correction — USER_APPROVED / PASS, 2026-10-11:** the user reported that the deployed quiz function was not working and explicitly approved the proposed production topic update. Read-only diagnosis found three active legacy topic names (`basis`, `linear combination`, `svd`) that did not exactly match any bundled-bank key, so the application correctly filtered all of them. Aggregate checks found one attempt and one mastery row attached to `basis`, so the legacy rows were preserved and deactivated rather than renamed. Created and activated `Rank and fundamental subspaces`, `Eigenvalues and eigenvectors`, and `Singular value decomposition`. Post-write verification found exactly three active topics, all three recognized by the reviewed bank, and each generated seven local questions. The legacy `basis` history remains one attempt and one mastery row; the other legacy topics remain at zero. No student identity/content was read, no history was changed or deleted, and no migration, provider request, deployment or Git mutation occurred. Lesson: admin-managed identifiers used as content-bank keys require exact-name validation or a visible reviewed-content status before release.

**User production confirmation, 2026-10-11:** after a hard refresh, the user reported “looks good now.” This confirms the corrected production topic/UI visibility from the user's authenticated session. A complete seven-answer submission and resulting student/admin progress synchronization were not explicitly reported in that message and remain unverified rather than inferred.

**Resume-ready snapshot, 2026-10-11:** the user chose to present the current project on their resume. Added `RESUME_PROJECT.md` with a recommended four-bullet entry, compact two-bullet version, one-line description and honest interview limits grounded in verified project evidence. Updated the public README to reflect the V2 deployment and corrected production topic UI. No capacity or full production E2E claim was added. Documentation formatting passed `git diff --check`; no application code, external service, database or Git state was changed in this step.

**Question-bank redesign — USER_APPROVED / SOURCE REVIEW COMPLETE, 2026-10-10:** user replied “approve all” to the proposed pre-generated, reviewed question-bank redesign and later approved the content-review pass. Added 11 questions per approved topic (4 easy, 4 medium, 3 hard) with citations to `lA notes.pdf`; student quiz creation now makes zero AI STAR, Gemini, retrieval or database-content calls before submission. All 33 keyed answers, explanations and citation pages were visually checked against the PDF. One Rank medium question was clarified to select the matching pivot columns of the original matrix rather than columns of rref(A). Questions and option order are randomized, and unsupported topics are hidden/fail safely. Summary-only attempt persistence is unchanged. Focused tests: 24 passed. Full suite after review: 116 passed in 2.10s; compilation, `pip check` and `git diff --check` passed. No migration, production write, external provider request, deployment or Git mutation. Agent-observed difficulties: the existing Graphify map was stale around old repair logic, an old unsupported test topic was correctly filtered, and the Rank elimination wording was ambiguous; direct caller inspection, a regression test and the wording correction resolved them. No new user-reported difficulty. Owner/TA sign-off and authenticated browser QA remain release gates.

**Quiz-model trial — USER_APPROVED / PARTIAL, 2026-10-10:** user said “ok do it” to the proposed provider-supported setup and one bounded end-to-end SVD evaluation, then reaffirmed autopilot with “bhai tu sambhal ab.” An authenticated read-only catalog request listed 41 AI STAR models; `gpt-5.6-luna` was selected for quiz generation only while the general answer model remained unchanged. Easy validated in 6.40s; the medium batch timed out after 30.01s (`OpenAITimeoutError`); exactly two generation calls, zero retries/repairs, hard skipped. No complete set or source review. The candidate was removed and `deepseek-v4-flash` restored. Artifact: ignored `evaluation/quiz_results/gpt56_luna_batched_svd.json`. No database, embeddings, student data, deployment or Git mutation. Agent-observed cause remains unknown; no new user-reported difficulty.

**Quiz-model phase close-out:** full suite passed (103 tests in 2.55s); compilation, `pip check` and `git diff --check` passed. The only pip output was the known non-writable cache warning. The live-call authorization is consumed. Further provider calls, another model switch, or a quiz workflow redesign require a new concrete approval; V2 deployment remains blocked.

**Non-thinking trial close-out:** after restoration, 12 focused tests passed in 0.69s; compilation and `git diff --check` passed. Corrected the evaluation diagnostic gap: future batch responses are retained bounded by `MAX_RAW_RESPONSE_CHARS` only in ignored synthetic artifacts, with raw text omitted from console summaries. The discarded response from this trial is unrecoverable locally; no additional call was made to obtain it. Lesson: persist rejected synthetic output before validation so another experiment is not needed solely to discover the validation cause.

**Non-thinking trial — USER_APPROVED / PARTIAL, 2026-10-10:** user said “approve both” for the temporary mode change and one bounded SVD evaluation. First easy batch returned invalid JSON in 24.09s; exactly one call, zero retry/repair, medium/hard batches skipped. Metadata: ignored `evaluation/quiz_results/nonthinking_batched_svd.json`. No complete set for source review. Invalid raw content was not retained by the runner; precise formatting defect and whether AI STAR honored the thinking toggle remain unknown. Restored prior thinking behavior; kept the verified `max_tokens` wire correction and batching. No embeddings/database access, production change, deployment or Git mutation. Agent-observed malformed JSON despite requested JSON mode is unresolved; no new user-reported difficulty. The trial authorization is consumed/completed and does not grant new calls.

**AUTOPILOT reaffirmed, 2026-10-10:** user repeated “bhai tu sambhal ab”; existing bounded autonomy remains active without authorizing paid calls or provider/model switches.

**DELEGATED_DECISION — token-cap compatibility correction:** installed `langchain-openai==1.7.0` converts its `max_tokens` constructor field to `max_completion_tokens` in `ChatOpenAI._get_request_payload`. Official DeepSeek Chat Completions docs specify `max_tokens`; AI STAR's handling of the rewritten field is unknown. Preserve the already approved 2,000-token cap under the provider-documented name using `extra_body` (no additional token allowance, model change, thinking control or live request). A local HTTP mock checks the actual serialized request and JSON mode without network access. This discrepancy is observed; its role in prior failures is unverified. Next live experiment remains queued for HIGH authorization.

**Next experiment prepared:** `PHASE_PLAN_NONTHINKING_QUIZ.md` proposes the existing model with `thinking.type=disabled`, documented `max_tokens=2000`, three batch calls maximum and 30-second transport timeout each. An offline mock verified both fields reach the serialized request with JSON mode; no network/provider call was made. AI STAR forwarding/honoring the toggle remains unknown. Paid trial and temporary mode change await explicit authorization.

**Compatibility phase verification:** 12 focused tests passed in 0.70s; full suite 103 passed in 2.39s; compilation and `git diff --check` passed. No new live request, deployment or Git mutation. Agent-observed lesson: assert serialized provider payload at the HTTP boundary; constructor kwargs alone missed LangChain's token-field renaming. No new user-reported difficulty.

**Bounded batch strategy — USER_APPROVED, 2026-10-10:** user said “approve do it” for three calls maximum, 2,000 output tokens and 30 seconds per call, immediate batch validation, no repair/retry, one complete synthetic SVD evaluation. Saved plan: `PHASE_PLAN_BATCHED_QUIZ.md`. Implemented batching for all approved mastery mixes; final UI/grading/persistence still receives seven questions. Full suite: 102 tests pass in 2.60s. The authorized live evaluation is complete; result follows.

**Bounded batch result — PARTIAL:** easy batch validated in 13.90s; medium batch hit `LengthFinishReasonError` in 22.10s. Exactly two provider calls; hard batch skipped. Total 36.01s, no retries/repairs, embeddings, database access, partial quiz display, Git mutation or deployment. Metadata: ignored `evaluation/quiz_results/batched_svd.json`. No full set existed for source review. Batching implementation remains local; reliability acceptance failed. Agent-observed lesson: smaller requests still truncate at the approved 2,000-token cap, so the current reasoning/provider behavior needs a consequential decision before further live work. Underlying token allocation is unverified; no new user-reported difficulty. Deployment stays blocked.

**Batch phase final checks:** full suite 102 passed in 2.60s; compilation, dependency consistency and `git diff --check` passed. Updated architecture, PRD, README, roadmap and operations to describe the approved batch/no-repair behavior. No extra dependency or speculative mathematical-expression parser was introduced.

Minimal-diagnostic local checks: compilation and `git diff --check` passed. Invoking the runner again hit its existing-artifact guard before configuration or networking; no second provider request occurred.

**DELEGATED_DECISION — local MCQ-quality adjustment, 2026-10-10:** user said “continue” after the proposed prompt fix. Scope: strengthen the shared generation/repair prompt to require exactly one mathematically correct option, prohibit equivalent mathematical distractors (including reordered scalar factors), and define easy as recall, medium as application, hard as reasoning/calculation supported by evidence. No provider call, new dependency or validator relaxation is authorized by this local step. Expected affected paths: `study_guide/quizzing.py`; both graph calls already reuse `_prompt_messages`. Verification: focused quiz tests and compilation. Live effectiveness remains unverified until a separately approved evaluation. Agent-observed cause: V2.11 offered equivalent scalar-factor expressions as different answers; plain string uniqueness cannot establish mathematical uniqueness.

**Local adjustment verification:** PASS — 7 focused quiz tests in 0.60s, compilation and `git diff --check`. No claim is made that these checks establish generated-question quality.

**Next bounded evaluation plan — PROPOSED:** temporarily use low reasoning effort with the strengthened prompt, make exactly one SVD request at the existing 5,000-token cap using local pages 49–51 and synthetic citations, disable repair/retry for this evaluation, retain the bounded synthetic result in the ignored artifact directory, and review all answers, mathematical option equivalence, citations and difficulty against the source. No embeddings, database access, browser login, deployment or Git changes. Keep low effort only if source review passes; otherwise restore it. Approval is required for this specific provider-behavior trial and one balance-backed request; exact charge is unknown.

**V2.12 approval — USER_APPROVED:** user replied “approve” to the exact single-call plan above on 2026-10-10. That bounded evaluation is complete; authorization does not extend to additional calls or deployment.

**V2.12 result — PARTIAL, 2026-10-10:** exactly one AI STAR SVD request with low reasoning effort and the strengthened MCQ prompt timed out after 90.49 seconds (`OpenAITimeoutError`). No quiz content, repair/retry, embeddings or database access occurred. Safe metadata is retained under ignored `evaluation/quiz_results/v212_svd_review.json`. The temporary low-effort setting was removed because source review could not pass; the local prompt quality improvement remains. Agent-observed difficulty: provider response time exceeded the existing 90-second boundary; underlying cause is unknown. No new user-reported difficulty. Further blind retesting is not recommended; provider reliability and authenticated quiz browser evidence remain open, and deployment is blocked.

**V2.12 local verification:** 7 focused quiz tests passed in 0.62 seconds; compilation and `git diff --check` passed after restoration. No deployment or Git mutation occurred.

**Provider reliability investigation — 2026-10-10:** user replied “approve” to investigating reliability. Local evaluation records distinguish three failure modes: provider `finish_reason=length`, generated-question quality failures, and one transport timeout. Low-effort SVD attempts took 54.29s (validation failure), 15.44s (structural pass, source-review failure), and 90.49s (timeout); these are individual observations, not a statistical reliability estimate. The adapter has zero transport retries and a 90-second timeout. An unauthenticated GET to `https://ai.starimg.ru/v1/models` returned the expected HTTP 401 in 1.288s (DNS 0.254s, TCP 0.475s, TLS 0.971s), confirming current gateway reachability without credentials, generation or balance use. It does not verify authenticated model inference. Queueing, relay/upstream stalls and reasoning behavior remain unproven causes; no timeout increase or successful reliability fix is claimed.

**Concrete next diagnostic — PROPOSED:** one AI STAR request using the existing model and synthetic instruction to return only `{"ok":true}`, low reasoning effort, a 1,000-output-token cap, a 30-second timeout and zero retries. Record only served model, finish reason, safe usage counters, latency, JSON success and transport exception/cause classes; no course/student content or database access. This tests basic authenticated generation, not SVD quality or class capacity. A new balance-backed call needs specific approval under the project contract; exact charge is unknown. A successful minimal diagnostic alone does not justify deployment.

**Minimal diagnostic — USER_APPROVED / PASS, 2026-10-10:** user replied “approve” to this exact one-call scope. `evaluation/run_provider_reliability_diagnostic.py` made one request with zero retries and returned the expected `{"ok":true}` in 5.51s, served model `DeepSeek-V4-Flash-0731`, finish reason `stop`. Provider usage reports prompt 10, completion 5, total 74; counts are retained as reported and are not arithmetically reconciled or treated as billed usage. Metadata-only artifact: ignored `evaluation/quiz_results/provider_reliability_diagnostic.json`. No course/student content, embeddings or database access. The runner refuses to run again once its artifact exists. Basic authenticated generation works; SVD timeout cause, task-level reliability and question quality remain unverified. No new user-reported difficulty and no new transport failure during this diagnostic. Next: use these results to choose a bounded quiz-specific strategy rather than treating a tiny successful request as release evidence; provider/model/workflow changes and additional calls remain separately gated.

V2.11 final verification: 98 tests passed in 2.36 seconds; compilation, dependency consistency and `git diff --check` passed. The evaluation runner now records each call's validation category and refuses to reuse an existing result file. No deployment or Git mutation occurred.

| ID | Proposed action | Reason / dependency | Impact / cost / security risk | Exact permission needed | Safe alternative | Status |
|---|---|---|---|---|---|---|
| P-1 | Owner/teaching-assistant sign-off on the 33-question bundled bank | Agent source review and automated contract tests cannot replace owner content sign-off | Incorrect wording or difficulty could affect students | Approve the reviewed bank before release | Keep V2 local | PENDING; 33/33 source-reviewed |
| P-2 | Authenticated local quiz browser QA with a test-safe account and data target | Real authenticated quiz navigation/accessibility remains unverified | May expose account identity and create attempt data depending on the target | Identify and approve a test-safe account plus local/development data target | Rely on mocked AppTests and keep the browser-evidence limitation | PENDING |
| P-3 | Publish V2 through the configured GitHub/Streamlit branch | Deployment requires user-controlled Git push after readiness is cleared | Public application change; push may trigger production deployment | User reviews/stages/commits/pushes after blockers clear | Keep current V1 deployment | BLOCKED; USER-ONLY |

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
- V2.1 adaptive quiz is implemented and user-approved: admin topics, seven grounded MCQs, local grading, rolling mastery, summary-only history, student progress and admin email lookup/deletion. Migration `003_adaptive_quiz.sql` is applied to the development project. V2.3 and V2.5 each verified one synthetic quiz set locally; V2.2, V2.4–V2.7 and V2.9–V2.10 remain partial, and V2 is not deployed.
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

**Phase status:** COMPLETE — user approved on 2026-10-10. The later V2.2 evaluation remains partial; the V2.3 bounded follow-up is recorded below. No deployment was authorized.

- Added LangChain/LangGraph pins, normalized verified email identity, strict quiz-domain validation and a deterministic retrieve/generate/validate/one-repair graph with no graph persistence or model-controlled writes.
- Added private quiz topics/profiles/mastery/attempt-summary tables. Browser roles are revoked; atomic completion is idempotent and profile deletion cascades only quiz data.
- Synthetic development-Supabase lifecycle passed: first score `5/7` produced mastery `71`; second `7/7` produced `88`; replaying the second attempt did not increment the count; student/admin reads matched; cleanup removed the exact synthetic profile/topic.
- The first database lifecycle run exposed an ambiguous PL/pgSQL column reference. It was corrected with an explicit table alias, applied, regression-asserted and retested successfully.
- Three-call AI STAR cap respected: one small LangChain JSON compatibility call passed; two complete quiz attempts ended in the safe provider-error path after long waits. No identity was included. Evidence/output bounds were reduced for future attempts, but the cap prevented another live call.
- Deterministic tests cover exact mixes, scoring/mastery, fabricated citations, one repair, insufficient evidence, identity-free payloads, summary-only persistence and the full Streamlit generate/answer/submit/result flow.
- Verification: 91 tests pass; compileall and `pip check` pass; local Streamlit health returned HTTP 200 in 1.3 ms; signed-out page shows the quiz-email disclosure. Authenticated browser navigation and live full-quiz quality/latency remain unverified.
- No Git mutation or deployment occurred.

## V2.4 Remaining Topic and Local UI QA — 2026-10-10

**Status:** PARTIAL — both capped topic generations failed safely. V2 remains not release-ready.

- Evaluated Eigenvalues and eigenvectors (mastery 60; local course pages 43–44) and Singular value decomposition (mastery 85; pages 49–51) using only local PDF evidence and synthetic citation IDs.
- Exactly two AI STAR calls were made, one per topic; both returned the app's safe “temporarily unavailable” error. No retry/repair or provider switch was attempted. Zero Gemini embedding calls and zero database access. Safe outcomes and counts are recorded in ignored `evaluation/quiz_results/v24_followup.json`.
- Neither topic produced a quiz set, so question quality, answer/explanation correctness, citations and difficulty mixes could not be manually reviewed. The successful V2.3 set remains the only manually reviewed V2 set.
- Full local suite (including synthetic student/admin AppTests): 98 passed in 2.49s. `compileall`, `pip check` and `git diff --check` passed.
- Browser authenticated quiz/focus checks remain not tested because available sessions were production V1 or signed out/stale. No production data access/write, real attempt, migration, Git mutation or deployment occurred.
- Next: the V2.5 read-only provider check and capped generation evaluation, plus the V2.6 concise-output SVD retest, are complete. SVD remains unverified due output truncation; no V2 deployment until representative generation and quiz-path evidence are complete.
- Read-only follow-up on 2026-10-10: authenticated AI STAR `/models` GET returned HTTP 200 and listed `deepseek-v4-flash` (41 models). This confirms endpoint/key access only, not chat generation health.

## V2.5 Provider Reliability and Quiz UI QA — 2026-10-10

**Status:** PARTIAL — Eigenvalues passed review; SVD generation was truncated. V2 remains not release-ready.

- Used exactly two AI STAR calls, one per remaining topic, with local PDF pages 43–44 and 49–51 and synthetic citation IDs. Zero Gemini embeddings, database access, retries or graph repairs. Evidence: ignored `evaluation/quiz_results/v25_followup.json`.
- Eigenvalues and eigenvectors generated seven distinct questions with the expected 2/4/1 difficulty mix. Structural validation passed; manual review confirmed every answer, explanation and page citation against pages 43–44.
- SVD returned `LengthFinishReasonError` with HTTP 200 at the 3,500-token output cap. The configured key/model can call chat generation, but the current output budget is insufficient for this set. No retry was made.
- The full suite passed: 98 tests in 2.53s; compileall, `pip check` and `git diff --check` passed. Browser auth/focus QA remains not tested; no authorized safe browser account/target was available.
- No app code change, production access/write, real attempt, migration, Git action or deployment occurred. Next step needs a separate phase approval for a concise-output adjustment and one SVD retest, plus explicit test-account/data-target approval for browser QA.

## V2.6 Compact Quiz Output and SVD Retest — 2026-10-10

**Status:** PARTIAL — SVD still truncates at the configured output cap. V2 remains not release-ready.

- Added a concise generation instruction and regression assertion. Existing token cap (3,500), response schema and validation limits remain unchanged.
- The single synthetic SVD call used local PDF pages 49–51 and synthetic citations; it returned `LengthFinishReasonError` with HTTP 200. No repair/retry, embeddings or DB access. See ignored `evaluation/quiz_results/v26_svd_retest.json`.
- Targeted quiz tests: 7 passed. Full suite: 98 passed in 2.45s; compileall, `pip check` and `git diff --check` passed.
- No production/browser login, database operation, migration, real attempt, Git action or deployment occurred. Raising the output cap or making another call requires separate approval; authenticated browser QA still needs an authorized test-safe account/data target.

## V2.7 Higher-Cap SVD Verification — 2026-10-10

**Status:** PARTIAL — SVD still truncates at 5,000 output tokens. V2 remains not release-ready.

- Raised the quiz output cap from 3,500 to 5,000; the existing adapter test verifies the configured value reaches `ChatOpenAI`.
- The single approved SVD call used local pages 49–51 and synthetic citations. It returned `LengthFinishReasonError` with HTTP 200 after 21.83 seconds. No completed set, retry/repair, embedding or database access. Evidence: ignored `evaluation/quiz_results/v27_svd_retest.json`.
- Targeted quiz tests: 7 passed. Full suite: 98 passed in 2.47s; compileall, `pip check` and `git diff --check` passed.
- No production/browser login, database operation, migration, real attempt, Git action or deployment occurred. Further blind cap increases are not recommended without provider-specific diagnostics; authenticated browser QA still needs a test-safe account/target.
- Read-only inspection of the installed OpenAI client confirmed `LengthFinishReasonError` is raised only when the provider choice reports `finish_reason="length"`; this is upstream truncation before application quiz validation, not a local JSON validator defect.

## V2.8 Raw SVD Provider Diagnostic — 2026-10-10

**Status:** COMPLETE — raw structure passed; provider reasoning headroom is low.

- One approved raw SVD call returned `finish_reason="stop"` in 21.17s. Usage: 1,589 prompt, 4,761 completion and 6,409 total tokens; 1,408 prompt tokens cached. Visible response length was 1,743 characters.
- JSON parsing and the existing seven-question validator passed with the required 1/3/3 difficulty mix. Response content was intentionally not displayed or persisted, so mathematical/source quality was not reviewed.
- Zero retries, repairs, embeddings or database calls. Full suite: 98 passed in 2.44s; compileall, `pip check` and `git diff --check` passed.
- Diagnosis: application validation is not the root issue; variable provider-side reasoning consumes nearly the entire 5,000-token allowance. Step 2 needs separate approval for measured headroom or a documented reasoning control and one content-retaining SVD review call.

## V2.9 Reviewed SVD Verification — 2026-10-10

**Status:** PARTIAL — normal application path still truncates; no SVD content review.

- The single approved normal-path SVD call used a temporary 6,000-token cap with local pages 49–51 and synthetic citations. It returned `LengthFinishReasonError` at HTTP 200 after 25.39 seconds. No retry/repair, embedding or DB access occurred.
- No completed set was available for structural or mathematical review. The runtime cap was restored to 5,000 because 6,000 provided no reliability benefit and increased possible usage.
- Targeted quiz tests: 7 passed. Full suite: 98 passed in 2.40s; compileall, `pip check` and `git diff --check` passed.
- No production/browser login, database operation, migration, real attempt, Git action or deployment occurred. Further progress requires an approved provider reasoning control, provider/model change, or multi-call workflow design.

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
## Answer Model Fallback — 2026-10-12

**Status:** LOCAL PASS / USER_REVIEW_PENDING. The user approved the whole phase on 2026-10-12. See `PHASE_PLAN_ANSWER_MODEL_FALLBACK.md`.

- User-reported difficulty: Study answer generation sometimes returned no output when the primary model was busy. The user requested `deepseek-v4.1-flash` as a fallback.
- Read-only authenticated AI STAR `/models` inspection confirmed both `deepseek-v4-flash` and `deepseek-v4.1-flash`; no chat-generation request was made.
- Added one `deepseek-v4.1-flash` attempt after primary timeout/network, HTTP 429 or HTTP 5xx failures. Authentication/other 4xx and malformed responses remain non-retryable and secret-safe.
- Agent-observed difficulty: the first full verification found one trailing blank line in this progress record; it was removed before final verification. Lesson: keep failover bounded and classify transport/provider availability separately from invalid model content.
- Verification: 20 focused answer tests and 140 full tests passed; compilation, `pip check`, and `git diff --check` passed.
- The production website remains unchanged until the user performs Git/deployment actions. Embedding, chunking, retrieval, database/storage, secrets, dependencies and the local reviewed-bank quiz path are unchanged. No paid generation call, deployment, external write, or Git mutation occurred.

## Voyage Embedding Migration — 2026-10-12

**Status:** MIGRATION APPLIED / CUTOVER PARTIAL — PROVIDER LIMIT BLOCKED. The user selected `voyage-4-lite`, approved the local phase and migration 005, then approved the coordinated production cutover on 2026-10-12. See `PHASE_PLAN_VOYAGE_EMBEDDINGS.md`.

- Implemented a shared standard-library Voyage adapter using native 1,024-dimensional `document`/`query` embeddings, bounded responses, explicit timeouts, strict finite/nonzero validation and safe provider errors. Rewired configuration, Study retrieval, ingestion, the offline quiz adapter, UI and evaluation callers; removed the now-unused Google embedding SDK requirement.
- Added and applied migration 005 with a separate Voyage column/index and private search RPCs. Existing 768-dimensional Gemini vectors remain intact for rollback. Failed-document retry now creates a fresh provider-compatible version instead of reviving incompatible failed Gemini metadata.
- User-reported difficulty: Gemini quota exhaustion prevented new chunks. The selected replacement is prepared locally but has not been contacted or deployed.
- Agent-observed difficulties: provider migration affects query and document vectors together, and the old failed-version metadata cannot be reused at a new dimension. The additive column and fresh-version retry address those constraints. During SQL application, the editor initially appended migration 005 to an old verification query, so PostgreSQL rejected the combined text at parse time and made no schema change; replacing the editor contents with only the 158-line migration resolved it. Voyage similarity scores may not match Gemini's calibrated `0.70` threshold, so live threshold measurement is required before release.
- Verification: 103 focused tests and 152 full tests passed; application/tests/evaluation compilation, `pip check`, and `git diff --check` passed.
- User confirmed the Voyage key was entered privately; local configuration validation reported configured and redacted without displaying/transmitting it. The user then explicitly approved exactly one synthetic API check. It succeeded with one finite, nonzero 1,024-dimensional `document` vector in 1.146 seconds, with no retry, course material, student data or persistence.
- Migration 005 was then applied to Supabase project `kjxixskoeihbitcohhuo`; SQL Editor reported `Success. No rows returned`. Read-only postflight verified 81 total chunks, all 81 legacy Gemini embeddings preserved, zero Voyage embeddings before re-index, and both new Voyage and both legacy Gemini service-role search RPCs callable.
- The user then replied `approve` to the explicitly proposed coordinated cutover comprising production re-index/database writes, deployment, and retrieval/citation threshold verification. Release checks passed: 152 tests in 2.80 seconds, compilation, `pip check`, `git diff --check`, and a credential-pattern scan outside ignored local secrets/PDFs. Deployment instructions were corrected from the stale `[gemini]` placeholder to `[voyage]`.
- Read-only production preflight found two stored documents: one ready active document with 81 chunks and one failed document with zero active chunks. Fresh local extraction produced 81 and 543 structural chunks respectively, requiring 3 and 17 Voyage batch requests under the current batch size. The existing missing-`fontTools` and Form XObject warnings recurred for the 417-page failed PDF; extraction still completed. Remote `main` remains at deployed commit `fae56c0`.
- The user confirmed the Voyage key was added directly to Streamlit Community Cloud without sharing it in chat. This is user-reported and was not inspected. Cutover now waits only for the user-controlled selective commit/push of the verified release files. No re-index, document/version activation, deployment or Git mutation has occurred yet.
- **Production cutover attempt — PARTIAL / PROVIDER LIMIT BLOCKED, 2026-10-12:** read-only GitHub verification confirmed deployed-source `main` at `72c7a86` (`migrate embeddings to Voyage`) after the user rebooted the Streamlit app. The authenticated Admin Documents page loaded the new release, and the previously approved re-index was started only for the active 80-page document. PDF loading passed, but Voyage returned the application's classified allowance/rate-limit error during embedding creation. The UI still showed the prior ready `gemini-embedding-2` version, confirming the atomic cutover did not replace the active document or lose data. No immediate retry was made. User-reported evidence: the Voyage dashboard showed 4 tokens used and 199,999,996 remaining, with project limits of 10,000 TPM and 3 RPM. This rules out exhausted allowance and identifies the one-minute throughput window as the cause. Agent-observed difficulty: the existing one-second 429 retry cannot outwait that window when the active document's three batches are sent rapidly. The bounded retry now waits 61 seconds only for HTTP 429; network/5xx retry behavior remains one second. Voyage retrieval, threshold calibration and citation verification remain NOT TESTED until the fix is verified, committed, deployed and the active document is re-indexed.
