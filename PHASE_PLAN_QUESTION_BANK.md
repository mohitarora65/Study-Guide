# Reviewed Question Bank Redesign

Status: SOURCE REVIEW COMPLETE — USER SIGN-OFF PENDING.

Approval: after the live quiz model path remained unreliable, the user approved the proposed pre-generated, reviewed question-bank redesign by replying “approve all” on 2026-10-10.

Outcome: student quiz sessions select seven questions locally from a bundled bank, preserving the approved mastery mixes, local grading, cited feedback and summary-only persistence. No model or embedding request occurs when a student starts a quiz.

Scope: cover the three approved course topics with at least four easy, four medium and three hard questions each. Randomize selected questions and option order. Unsupported topics fail safely until reviewed content is added. Keep provider-generation code only for offline evaluation; it is no longer called by the student UI.

Affected paths: `study_guide/question_bank.py`, student quiz caller in `app.py`, connected tests and current architecture/product/operations documentation. No database schema change, dependency, credential, production write, deployment or Git mutation.

Acceptance: all three topics can produce every approved mastery mix; each quiz has seven unique questions, four distinct options, stable answer keys after shuffling and page citations. Existing submission/mastery summary behavior remains unchanged. Full local suite, compilation, dependency and diff checks pass.

Result: added 33 source-checked questions covering Rank and fundamental subspaces (pages 24–29), Eigenvalues and eigenvectors (pages 43–44), and Singular value decomposition (pages 49–50). Each topic has four easy, four medium and three hard questions. A final visual review verified all 33 keyed answers, explanations and cited PDF pages. One Rank medium question was tightened to require the pivot columns of the original matrix instead of leaving the post-elimination wording ambiguous. Student quiz creation now performs zero model, embedding or retrieval requests. Unsupported active topic names are hidden from the student selector and the selector itself also fails safely when called directly.

Verification: focused bank/app tests passed (24). After the content-review wording fix, the full regression suite passed (116 tests in 2.10 seconds); compilation, dependency consistency and `git diff --check` passed. The bank tests enforce per-topic difficulty capacity, question/option uniqueness, field bounds, citations, every mastery mix and correct-answer preservation after option shuffling.

Difficulty: the Graphify map was useful for locating the app, quiz and persistence boundary, but it was stale around the removed repair node; actual callers were verified directly before editing. A test fixture using the old unsupported `Vector spaces` topic initially hid the start button as designed; the fixture was corrected and a regression test now covers that behavior. During content review, the phrase “after elimination” could wrongly suggest taking columns from rref(A); the question now explicitly selects matching pivot columns from the original A. No new user-reported difficulty.

Release boundary: no production database, deployment, provider request or Git mutation occurred. Owner/teaching-assistant sign-off on the reviewed bank and authenticated browser QA remain pending before release.
