# Final UI and Project Close-out Phase

**Status:** LOCAL PASS — user approved the whole phase on 2026-10-11; deployment pending
**Version:** V3 final polish
**Visible outcome:** Clearer Study and Quiz pages, accurate upload guidance, verified local behavior, and an honest final project handoff.

## In scope

- Study page:
  - Rename the main heading to **“Let’s resolve your doubt”**.
  - Change the question placeholder to **“Ask a question from your course material…”** while retaining the existing character limit.
  - On **New chat**, show an optional chat-name field; when blank, use the first question (bounded to the existing 80-character title limit).
  - Allow an owned saved chat to be renamed later.
- Adaptive Quiz page:
  - Rename the heading to **“Let’s test”**.
  - Preserve the existing seven-question adaptive **Quick Quiz** and its mastery update.
  - Add a reviewed-bank **Create Custom Quiz** mode with one or more topics, 5/7/10 questions, and one or more difficulty levels.
  - Keep all questions on one page.
  - Make custom quizzes practice-only: no attempt/mastery database write.
  - Show score, correct/incorrect totals, per-difficulty results, explanations, citations, and updated mastery where applicable.
- Documents page:
  - Set Streamlit's uploader limit to 25 MB so its UI matches the existing 25 MiB application and storage boundary.
- Verification and close-out:
  - Add focused tests for chat naming/renaming, custom quiz selection and non-persistence, result summaries, labels, and upload configuration.
  - Run the full test suite, compilation, dependency consistency, diff checks, and a local Streamlit smoke test.
  - Update README/PROGRESS only where behavior or final status actually changed.

## Expected files

- `app.py`
- `study_guide/database.py`
- `study_guide/question_bank.py`
- `.streamlit/config.toml`
- `tests/test_app.py`
- `tests/test_chat_database.py`
- `tests/test_question_bank.py`
- `README.md`
- `PROGRESS.md`

## Boundaries

- No AI-generated custom questions, new dependency, schema migration, provider call, database write, deployment, or Git mutation.
- Custom quiz results are session-only and do not appear in Quiz Progress.
- Existing authentication, approved-question review, quick-quiz persistence, mastery formula, and admin pages remain unchanged.
- Deployment and any production smoke test remain separately gated after the user performs the required Git commit/push.

## Acceptance evidence

- A blank custom chat title falls back to the first question; a supplied title is used; only the owner can rename a chat.
- Custom quizzes respect selected topics, count, and difficulty, fail clearly when the reviewed pool is insufficient, and never call `complete_quiz_attempt`.
- Quick Quiz still creates exactly seven questions and persists its summary/mastery.
- Results correctly summarize arbitrary custom counts and the quick-quiz mastery result.
- The uploader presents a 25 MB limit and backend 25 MiB validation remains intact.
- All existing and new local checks pass.

## Risks

- Some topic/difficulty/count combinations may not contain enough approved questions; the UI will reject those combinations without silently changing the request.
- Streamlit uses MB wording while backend validation uses MiB; both are configured to the numeric limit 25, with backend validation remaining authoritative.
