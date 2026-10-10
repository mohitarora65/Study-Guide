# V2 Deployment Plan — Existing Streamlit App

**Status:** APPROVED — BLOCKED ON V2 QUIZ READINESS; NO PUSH
**Prepared:** 2026-10-10
**Target:** Existing `https://iiti-mathematics-study-guide.streamlit.app/` app, subject to dashboard confirmation
**Source:** `mohitarora65/Study-Guide`, `main`, `app.py`, subject to dashboard confirmation

## Outcome

Publish the locally implemented adaptive quiz to the existing app, then perform a bounded health/auth/navigation check without generating a quiz or creating student records.

## Known release risk

Repeated AI STAR trials did not make live quiz generation reliable. The approved redesign now builds quizzes locally from a bundled, source-checked bank covering the three approved topics. Provider latency is no longer a quiz release blocker. Deployment remains blocked on review of the complete bank, authenticated quiz browser evidence and the user-controlled release checkpoint; do not push V2 to the configured production branch yet.

## Required sequence and gates

1. **Review locally:** rerun tests/secret checks and review the exact V2 diff. Current local branch is `feature/adaptive-quiz-v2` at `1468908`, tracking the pushed feature branch. `origin/main` remains at `b8829fb`; local `main` points at `1468908` and is one commit ahead of `origin/main`. The current worktree also has local documentation/source changes and untracked `.serena/`; `.streamlit/secrets.toml`, local PDFs, virtual environments and ignored evaluation artifacts must not be pushed.
2. **Confirm production target:** user confirmed Supabase ref `kjxixskoeihbitcohhuo` is production. The open dashboard identifies the `Study-Guide` project as `PRODUCTION`. Do not inspect or copy secret values. Confirm the Streamlit app's connected repository/branch before the user's push.
3. **Production database preflight:** a read-only catalog query found all four quiz tables, both functions, RLS on all four tables, no SELECT privilege for `anon`/`authenticated`, no function execution for browser roles, and required function execution for `service_role`. The expected schema/access controls already exist, so migration `003` was not run again. Preserve the schema if application rollback is needed; do not delete data.
4. **User Git checkpoint:** only the user stages, commits and pushes. Streamlit Community Cloud monitors the connected GitHub source and updates the app after a push, so pushing to its configured branch is itself a production publication. The user must review the staged file list and diff before pushing.
5. **Cloud configuration:** use existing app secrets if they are already correct. No new key, provider, OAuth callback or paid service is planned. Any needed secrets, access, callback or app-setting change requires separate approval before editing.
6. **Post-deploy smoke check:** verify HTTPS health, Google sign-in/out and the authorized Student/Admin navigation. Do not generate a quiz, submit a real attempt, expose student records in logs, or make a capacity claim. If a safe UI/database check requires synthetic production data, stop for separate approval.
7. **Rollback:** if the app fails, user rolls back to the prior known-good V1 deployment/commit after confirming the exact deployed commit. Leave the additive quiz schema intact. Report any migration or app errors; do not perform destructive cleanup.

## Boundaries

- No provider calls, quiz generation, real student attempts, data deletion, paid services, OAuth permission changes, or provider switch.
- No Git staging, commits, branches, merges or pushes by Codex.
- No production database migration until the production project reference is confirmed and the migration action receives separate explicit approval.
- This is a controlled deployment request, not approval for a class-wide pilot. Final release status remains subject to actual smoke-test evidence.

## Current evidence

- Commit `1468908` is on the pushed feature branch; `origin/main` remains at V1 commit `b8829fb`. Local `main` points to the feature commit, and the worktree contains uncommitted phase updates. No Git mutation was made.
- Local automated suite: 98 passing tests; compile, dependency consistency and diff checks passed. Local UI tests use mocked identity/data; a real authenticated quiz browser flow was not completed.
- V2.3 used two AI STAR calls and one Gemini embedding to verify one synthetic quiz set. No production data was written and no deployment occurred.
- V2.4 used two AI STAR calls and zero embeddings; both remaining topic generations failed safely. No retries, database access, production data or deployment occurred. Details: `PHASE_PLAN_V2.4.md` and ignored `evaluation/quiz_results/v24_followup.json`.
- A subsequent authenticated read-only GET to AI STAR `/models` returned HTTP 200 and listed the configured model. This establishes endpoint/key access only, not generation health. Proposed two-call evaluation and test-safe browser QA await approval in `PHASE_PLAN_V2.5.md`.
- V2.5 used its two-call cap: Eigenvalues passed source review; SVD again ended in `LengthFinishReasonError` at HTTP 200 with the 3,500-token cap. Browser authentication was not tested. Deployment remains blocked pending an approved SVD output adjustment/retest and safe authenticated quiz-path evidence.
- V2.6 added a concise-output prompt instruction, but its single approved SVD retest still returned `LengthFinishReasonError` at HTTP 200; the token cap was not raised. Further generation testing or increasing the cap needs new approval. Deployment remains blocked.
- V2.7 raised the cap to 5,000, but its single SVD attempt still returned `LengthFinishReasonError` at HTTP 200 after 21.83 seconds. Further blind cap increases are not recommended; provider-specific diagnostics and a new approved approach are required. Deployment remains blocked.
- V2.8's raw diagnostic returned `finish_reason="stop"` and passed JSON/quiz validation, but used 4,761 of 5,000 completion tokens for only 1,743 visible characters. Content was deliberately not stored, so SVD mathematical quality remains unreviewed. Deployment remains blocked pending a reliable token strategy, one reviewed SVD set and authenticated quiz-path evidence.
- V2.9's one normal-path SVD request still returned `LengthFinishReasonError` at a temporary 6,000-token cap. The runtime cap was restored to 5,000 because the increase did not improve reliability. Deployment remains blocked pending an approved reasoning/model/workflow decision, one reviewed SVD set and authenticated quiz-path evidence.
- V2.10 sent one approved low-effort SVD request at the existing 5,000-token cap. AI STAR returned content without truncation or rejecting the parameter, but the draft failed quiz validation and the one-call cap blocked repair. The runtime setting was restored because a usable set was not verified. Deployment remains blocked.
- V2.11 returned a structurally valid SVD set on its first call in 15.44 seconds. Source review found two mathematically equivalent correct options in Q6; difficulty labels also overstate recall questions. The low-effort setting was removed as planned. No repair call was made; deployment remains blocked on question quality and authenticated browser evidence.
- V2.12 strengthened the shared quiz prompt for mathematically distinct options and difficulty calibration, then made one approved low-effort SVD request. It timed out after 90.49 seconds without content; no repair/retry occurred. The prompt improvement remains, while the temporary reasoning setting was removed. Question quality remains unverified and deployment stays blocked.
- The user approved bounded three-batch generation. Local implementation passes 102 tests; live SVD evaluation validated the easy batch, then the medium batch hit the 2,000-token limit. It stopped after two calls in 36.01s without a partial quiz. Batching remains local; no complete SVD set or readiness evidence was obtained. See `PHASE_PLAN_BATCHED_QUIZ.md`.
- A local transport test corrected LangChain's token-limit field to the provider-documented `max_tokens`; 103 tests pass. The separately approved non-thinking trial then failed JSON parsing on its first easy batch after 24.09s and stopped. The temporary thinking toggle was removed; no complete quiz or readiness claim. See `PHASE_PLAN_NONTHINKING_QUIZ.md`.
- The approved `gpt-5.6-luna` quiz-only trial used AI STAR's authenticated model catalog. Easy validated in 6.40s, but medium timed out at 30.01s; hard was skipped and no complete quiz existed for review. The candidate model was restored to `deepseek-v4-flash`. See `PHASE_PLAN_QUIZ_MODEL.md`.
- The user approved replacing live quiz generation with a bundled bank. The local implementation covers all three approved topics and every mastery mix without provider or database changes. Full bank content and authenticated browser review remain release gates. See `PHASE_PLAN_QUESTION_BANK.md`.
- Current local regression suite: 116 passed in 2.70s; compileall, `pip check` and `git diff --check` passed. Authenticated quiz/browser accessibility checks remain not tested.
- Production Supabase ref was confirmed by the user and dashboard. Read-only catalog results confirm the quiz schema and role protections are present; no production SQL mutation was made.
- Deployment must remain paused until the complete bank and authenticated quiz flow are reviewed. Afterward, the user must verify the Community Cloud source branch and perform any push; no public app update has occurred.
- Current Streamlit Community Cloud behavior is documented at [deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [connect GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account), and [app settings/secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings). Community Cloud checks the connected GitHub source for updates; secrets are managed in app settings.

## Approval record

The user approved this deployment plan on 2026-10-10 by replying “approve,” then approved the production migration action and confirmed `kjxixskoeihbitcohhuo` is the production project. Read-only preflight showed the expected schema and protections already exist, so no migration was needed or re-run. Git operations remain user-controlled.

On 2026-10-10 the user explicitly requested that remaining work continue and deployment proceed quickly. The local release audit then passed: 116 tests in 2.66 seconds, compilation, dependency consistency, `git diff --check`, a source secret-pattern scan with no matches outside excluded secret/artifact paths, and local Streamlit health on ports 8501 and 8502. The public app endpoint responded and redirected to Streamlit authentication. Authenticated browser QA could not run because no browser automation surface was available. The release therefore remains a controlled pilot candidate with that limitation. The feature branch is already present on `origin`, but the reviewed question-bank changes remain uncommitted; Codex did not stage, commit or push them.
