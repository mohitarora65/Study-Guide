# Phase Plan V1.4 — Grounding Evaluation, Security and Release Hardening

**Status: COMPLETE — user approved V1.4 close-out on 2026-10-09.** All evaluation thresholds pass, the discovered local pip advisory was remediated and the repeat scan is clean. Dark-theme and separate student-account browser checks remain documented limitations. The three-request synthetic burst is not a class-capacity guarantee. This plan follows V1.4 in the approved `ROADMAP.md` and the evaluation criteria in `PRD.md`. No deployment is authorized by this sign-off.

## Outcome

Produce an evidence-backed pilot candidate: repeatable grounding results against the approved course PDFs, critical security/reliability checks, accessibility and performance findings, and an honest release-candidate README. This phase does not deploy or authorize a student pilot.

## Scope and boundaries

- Automatically draft a 40-question evaluation set from the existing course material: at least 25 answerable questions covering definitions, derivations, formulas and applications, and at least 15 plausible out-of-syllabus/unanswerable questions.
- The questions are drafts, not ground truth. A teaching assistant must approve/edit the set and manually judge citation support and high-risk formulas before results count against PRD release thresholds.
- Draft the set in this work session without calling Gemini or AI STAR. DeepSeek remains answer-generation-only; this plan does not add a question-generation provider or feature to the running app.
- Build a repeatable evaluation runner and record answer/refusal, citation validity/support, refusal recall, unsupported-answer rate and formula review results. Use only approved synthetic/test data and the existing course PDFs; no real student identity or history.
- Test retrieval/chunk/threshold behavior without weakening refusal safeguards; cover auth/authorization, prompt injection, inputs/filenames and secret leakage; exercise timeout/quota/storage/database failures.
- Run existing automated tests, add focused AppTest/Playwright critical-path checks where supported, inspect keyboard/focus/labels/contrast/mobile width, and measure cold start, latency, memory and small concurrent load.
- Record risks and known limits; update README and progress with measured results and untested areas.

## Out of scope

- Deployment, production account changes, schema changes, Git operations, or onboarding real students.
- New runtime AI-provider calls for question generation, LangChain, new architecture, or added product features.
- Treating AI-drafted questions as TA approval or using unreviewed labels as factual evaluation ground truth.

## Intended files and approach

- Add `evaluation/` artifacts for the draft set, runner and results (exact filenames to follow existing repository conventions after inspection).
- Extend focused tests under `tests/`; make only minimal fixes required by the approved hardening checks.
- Update `README.md` and `PROGRESS.md`; preserve existing user data and approved schema.
- Use the current project environment and dependencies. Do not install packages without separate approval; use existing Playwright tooling if available, otherwise record the limitation and provide reproducible manual checks.

## Acceptance evidence

- The 40-question draft has the required 25/15 split and appropriate topic coverage; TA approval/editing is clearly tracked before scored evaluation.
- The runner is repeatable and records actual evidence for every PRD threshold: citation validity 100%, citation support at least 90%, refusal recall at least 90%, unsupported-answer rate no more than 10%, and manual review of all high-risk formula questions. Report FAIL honestly when a threshold is missed or TA review is pending.
- Security, failure-handling, UI/accessibility and performance checks are documented with executed results and explicit NOT TESTED items.
- Automated regression tests pass after fixes; no critical security issue remains unresolved for pilot candidacy.
- No deployment or live-user test occurs in this phase.

## External risks and approvals

- The existing AI STAR provider may be used for bounded answer-generation evaluation after this phase is approved; its retention is unknown and accepted by the user, dollar pricing is unverified, and requests reportedly stop at zero balance. Keep calls to the approved test set and report observable usage; do not send identities or saved chats.
- The teaching assistant must review the generated questions and judge citation support/formulas. Until that review happens, the evaluation is preparatory and cannot claim the PRD thresholds are met.
- Deployment remains a separate V1.5 approval. User performs all Git operations.

## Model and effort forecast

- Recommended Codex route: current available general coding model; medium effort for runner/test integration, high effort for security and evaluation review. Exact selectable model and usage-window status are not exposed to this workspace.
- Estimate: 10–18 human-equivalent hours plus TA review; 3–5 context sessions; approximately 2–4 five-hour usage windows (low confidence). Provider token cost is unknown; measure actual reported usage and stay within the user's balance hard stop.
- Use existing code and standard library where practical; no new framework or provider abstraction.

## Git checkpoint

No Git mutation by Codex. After review, the user can inspect `git status` and `git diff --stat`, explicitly stage reviewed files, inspect the staged diff and commit if desired.

## Approval record

User approved the whole V1.4 phase by replying “yes” on 2026-10-09. User requested automatic sample-question generation; the resulting 40-question draft is offline evaluation material, not runtime question generation. Live provider calls remain gated on TA review/approval of every question.

User approved V1.4 close-out on 2026-10-09 after reviewing the completed evaluation and hardening evidence.

## Execution Evidence and Remaining Work

- Drafted 40 questions in `evaluation/questions.json` with the required 25/15 split. On 2026-10-09 the user confirmed all 40 were approved by a teaching assistant as written; that status is recorded in the dataset. Offline validation confirms the approval gate is satisfied.
- Added a standard-library evaluator that checks citations against active document versions/page counts, captures answer/refusal and timing, leaves human judgments blank, and reports PRD thresholds as pass/fail/pending/incomplete. Generated result files are Git-ignored.
- Automated verification: 80 tests passed; `compileall` and `pip check` passed. Existing auth/ownership/provider-failure tests remain green. The retry-merge path is covered by a focused test.
- A local Streamlit server was bound only to `127.0.0.1` and stopped after checks. Its health endpoint returned HTTP 200 in 2.2 ms; five concurrent health probes all returned 200 in about 1.0–1.2 ms. The Python process used about 59 MB RSS, and the server reported ready within the 1.5-second startup wait. These are local dev-server/health-only measurements, not deployed cold-start or answer-generation capacity evidence.
- Source-level accessibility review found visible labels for chat, history, upload, and action controls, and textual status/error messages. A read-only Brave check of the signed-out local page confirmed the sign-in button is keyboard-reachable with a visible focus indicator and the layout fits a 390-pixel viewport without horizontal overflow. Contrast, authenticated browser critical paths, and browser-level failure handling remain NOT TESTED. Playwright CLI has no Chromium executable; no browser was installed.
- Existing unit/integration coverage checks domain authorization, owner-filtered chat operations, prompt-injection handling, safe provider errors and schema grants. `pip check` found no broken requirements. A targeted review of installed direct versions found `pypdf==6.19.0` meets the fixed version for three September 2026 resource-consumption advisories, and `streamlit==1.65.0` is newer than the fixed version listed in a Windows-only advisory. This is not a complete dependency audit: no scanner was installed, and transitive-package/advisory coverage remains unverified.
- Full live evaluation completed against the approved set; four errored questions were retried individually and merged with the first 36 results. The user confirmed the 24 generated supported answers/citations and all 11 high-risk formula answers were correct. The reviewed result is Git-ignored at `evaluation/results/20261009T122132Z-ta-reviewed.json`. Metrics: 40 questions, zero provider errors, 100% validity among 46 emitted citations, 100% citation support, 100% refusal recall, 0% unsupported answers, and zero formula errors. All five automated thresholds pass. One supported question (A09) was refused. A targeted retrieval-only check found its supporting definition on PDF page 25 at similarity 0.836; this sent one query embedding to Gemini and read Supabase, with no answer generation or database write. Median end-to-end duration was 12.04 seconds; maximum was 41.132 seconds. Exact provider balance deduction is unavailable.
- No Supabase writes, deployment, schema changes, or Git mutations occurred in V1.4. The sandbox initially blocked DNS; the approved run was retried with network access and completed.
- The user accepted A09's supported-question refusal as a known limitation on 2026-10-09. The refusal safeguard remains unchanged; no prompt or threshold adjustment was made.
- Remaining limitations: dark-theme contrast and a separate student-account browser flow were not tested. The three-request synthetic burst is not a class-capacity guarantee. No unresolved dependency advisory remains in the scanned local Python environment. V1.4 is ready for user review/sign-off, not deployment.

### Latest V1.4 Hardening Update — 2026-10-09

- Replaced low-contrast caption styling; light-theme application body text and the primary sign-in button pass WCAG AA contrast checks. Existing signed-out keyboard-focus and 390-pixel width checks remain passing.
- Authenticated IIT Admin sign-in exposed duplicate inferred `<lambda>` Streamlit page paths. Explicit `study` and `documents` paths fixed navigation; a regression test covers uniqueness. Authenticated Study and Documents navigation rendered read-only; Admin saw `lA notes.pdf` as ready (80 pages). No question was submitted and no Supabase write occurred. The local test session was signed out afterward.
- Three concurrent synthetic answer requests completed in 6.28, 6.59 and 7.10 seconds with 1, 1 and 2 citations. This is a smoke test, not a capacity guarantee.
- OSV batch audit queried 74 installed Python distributions. It reported pip 26.1.2 affected by [GHSA-qwm4-qh6w-59xr](https://github.com/advisories/GHSA-qwm4-qh6w-59xr), fixed in 26.2.0. After user approval, local `.venv` pip was updated to 26.2.0 and the repeat OSV scan found zero advisories across the 74 distributions. No audit package was installed.
- Verification after the fix: 81 tests passed; `compileall` and `pip check` passed. No schema, architecture, deployment, Supabase writes, or Git operations occurred.
