# Phase Plan — On-Demand Adaptive Quiz Fallback

**Status:** LOCAL PASS / USER REVIEW PENDING; no production/provider run or deployment performed.

## Outcome

For Quick Quiz, show every active topic, reuse enough matching built-in or approved questions when available, and otherwise generate a cited quiz from retrieved course material in the student's current study scope. Keep Custom Quiz practice-only and bank-based.

## Scope and files

- `app.py`: expose active topics to Quick Quiz; try the current bank first, then call the existing grounded generator only when the bank cannot supply the quiz. Keep Custom Quiz restricted to bank-eligible topics.
- `study_guide/quizzing.py`: pass the active study scope into retrieval and use subject-neutral quiz instructions.
- `tests/test_app.py`, `tests/test_quizzing.py`: verify bank-first behavior, material fallback, scope preservation and failure handling with mocked providers.
- `PROGRESS.md`, `README.md`: record behavior, evidence and limits.

## Acceptance evidence

- Built-in/approved questions are used without an AI generation call when sufficient.
- An active topic with no sufficient bank questions attempts grounded retrieval/generation in the selected study scope; generated questions require citations to retrieved chunks.
- No relevant indexed evidence fails safely without saving a quiz attempt.
- Existing quiz grading/mastery behavior and Custom Quiz behavior remain unchanged.
- Focused and full tests, compilation, `pip check`, and `git diff --check` pass.

## Risks and permissions

- Uses the already configured Voyage query-embedding and AI STAR quiz-generation integrations only on the fallback path. This can consume existing provider balance; existing per-user quiz generation rate limit applies. No live provider call, deployment, database write, migration, or Git mutation is part of local implementation.
- Machine Learning material is not currently verified as an active ready index. Until indexing succeeds and retrieval is confirmed, Machine Learning generation should safely report insufficient material.
- Generated questions are ephemeral and are not inserted into the reviewed bank; course citations are shown with the quiz.
