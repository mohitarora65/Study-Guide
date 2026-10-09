# Phase Plan V2.2 — Quiz Evaluation and Release Readiness

**Status:** PARTIAL — KEPT LOCAL BY USER
**Version:** V2
**Depends on:** V2.1 complete and user-approved
**Prepared:** 2026-10-10

## User-visible outcome

Evidence that quiz questions are usable and grounded, the local student/admin flows are ready for release, and a clear deployment and rollback handoff. Public deployment remains a separate action requiring explicit approval after the user pushes the reviewed changes.

## Proposed evaluation matrix

| Set | Admin-managed topic | Mastery band | Required mix | Questions |
|---|---|---:|---|---:|
| A | Rank and fundamental subspaces | 0% / new | 4 easy, 3 medium, 0 hard | 7 |
| B | Eigenvalues and eigenvectors | 60% / developing | 2 easy, 4 medium, 1 hard | 7 |
| C | Singular value decomposition | 85% / strong | 1 easy, 3 medium, 3 hard | 7 |

These topics are proposed from the approved course evaluation set (`evaluation/questions.json`) and the current linear algebra corpus. The user may revise them in the phase approval reply.

## In scope

- Diagnose the V2.1 full-generation failures using local logs/configuration and provider-visible status without exposing credentials or student data.
- If the existing approved AI STAR path can be made reliable within the cap, generate one set per approved matrix row and save a review artifact with questions, choices, answer key, explanation, difficulty and page citations.
- Stop generation at three AI STAR calls total; no automatic retry or model/provider switch. If a call fails, record the result and finish deterministic/local checks.
- Support manual review of all generated questions for clarity, answer correctness against cited material, explanation support, difficulty and citation validity.
- Exercise insufficient evidence, provider failure, duplicate submission, session loss, student isolation and synthetic admin deletion with deterministic/local tests and approved synthetic data.
- Review stored-email privacy, student/admin UI accessibility, operational limits, migration rollback and quiz-data deletion instructions.
- Update `README.md`, `OPERATIONS.md`, `PROGRESS.md`, this phase plan and any narrowly needed application/tests/docs fixes.
- Provide precise user-run Git commands and a release evidence summary.

## Out of scope and approval boundaries

- No more than three AI STAR calls total; no additional Gemini calls beyond the three small retrieval embeddings needed for those generations.
- No paid provider, model/provider switch, package installation, new database migration, production data changes or real student records.
- No staging, commits, branches or pushes; Git remains user-controlled.
- No public deployment or production configuration changes in this approval. After local review and the user’s GitHub push, request explicit deployment approval before publishing the change or exercising deployed paths.
- No class-wide capacity guarantee; only a small bounded burst measurement if it can be performed without exceeding the AI STAR call cap.

## Intended files and approach

- `study_guide/quizzing.py` — make only evidence-backed reliability fixes within the approved provider contract.
- `app.py` — targeted UI/accessibility or session-loss fixes if evaluation finds a reproducible issue.
- `tests/test_quizzing.py`, `tests/test_quiz_database.py`, `tests/test_app.py`, `tests/test_schema.py` — cover each found issue and the critical failure paths.
- New ignored `evaluation/quiz_results/` artifacts — retain only synthetic evaluation material; do not save credentials, identity or unnecessary corpus excerpts.
- `README.md`, `OPERATIONS.md`, `PROGRESS.md`, `PHASE_PLAN_V2.2.md` — record actual results, costs/usage where visible and limitations.

## Acceptance evidence

- Each of the three proposed MCQ sets either contains seven valid, cited questions with its exact approved difficulty mix or has a clearly recorded safe failure; total provider calls never exceed three.
- Every generated MCQ receives a manual quality decision before any release claim. Defects are fixed and regenerated only if the fixed total call allowance permits it; otherwise the affected criterion stays unmet.
- No invalid or failed quiz creates an attempt; duplicate completion does not change mastery twice; session loss and privacy behavior are recorded.
- Student data isolation, email visibility scope, admin-only controls, deletion behavior, keyboard navigation and readable focus states have evidence or are explicitly marked untested.
- Local regression checks pass after all fixes; operations and rollback instructions match the deployed V1 and proposed V2 change.
- No V2 release or deployment claim is made without the user's separate deployment approval and later deployed-path evidence.

## Verification plan

- Run focused and full automated tests, compilation, dependency consistency and a secret scan after approval and any fixes.
- Use the existing local app and authenticated browser profile if available; do not broaden browser permissions.
- Run at most one generation for each approved matrix row, recording elapsed time and visible provider usage without logging secrets or full identities.
- Use only synthetic data for admin deletion and remove only the exact phase-created records after verifying their identifiers.
- If the provider again fails on a full generation, do not retry beyond the cap; surface the concrete failure evidence and mark live quality evaluation partial.

## Approval request

Approve this whole V2.2 phase for bounded local evaluation and release readiness, including the proposed three-topic matrix, at most three AI STAR calls, necessary small Gemini embeddings, synthetic-data cleanup and in-scope fixes. This approval does not authorize Git mutations or public deployment.

## Approval record

The user approved the whole V2.2 phase on 2026-10-10 by replying “approve.” The three-topic matrix and boundaries above are approved. This includes the capped live evaluations, local fixes/checks and synthetic-data lifecycle in this plan; it excludes Git mutations and public deployment.

## Execution report — 2026-10-10

**Status: PARTIAL — KEPT LOCAL BY USER.** The safe-failure and call-cap criteria passed, but usable question sets and release-readiness criteria did not.

- Exactly three AI STAR requests were made: Rank and fundamental subspaces (11.85 s), Eigenvalues and eigenvectors (13.27 s), and Singular value decomposition (10.32 s). Each returned HTTP 200 but terminated with `LengthFinishReasonError`; no repair request or hidden transport retry was made. No set completed, so no questions were available for manual quality review. The ignored metadata artifact is `evaluation/quiz_results/v22_20261010.json`.
- The output limit was raised from 1,800 to 3,500 tokens based on the observed truncation, with a regression assertion. This change was not live-verified because the approved call cap was exhausted. No provider switch or further call was attempted.
- Local verification: 97 tests pass; compilation, `pip check`, and `git diff --check` pass; the local Streamlit health endpoint returns `ok`. Streamlit UI tests cover student-only navigation, student quiz submission, student mastery/history, admin email filtering and topic creation. Three deprecated table-width arguments were replaced with `width="stretch"`. Synthetic database idempotency, admin email lookup, mastery summary and exact-record cleanup passed. No V2 topics or synthetic quiz profile were left behind.
- The real browser showed the signed-out page. Authenticated browser navigation, keyboard/focus behavior on the quiz flow, generated-question quality, and end-to-end quiz latency remain unverified. Thus V2 is not release-ready and was not deployed. No Git operations occurred.

At V2.2 close-out, the user chose to leave the feature local (2026-10-10); no follow-up provider generation was requested. The user later requested a separate deployment, which is tracked in proposed `DEPLOYMENT_PLAN_V2.md`. This does not change V2.2's partial result or authorize any Git operation; release readiness remains unverified.
