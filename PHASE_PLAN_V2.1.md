# Phase Plan V2.1 — Complete Adaptive Quiz Implementation

**Status:** COMPLETE — USER APPROVED ON 2026-10-10; LIVE FULL-QUIZ SMOKE LIMITED
**Version:** V2
**Depends on:** V2-G1–G5 approved
**Prepared:** 2026-10-10

## User-visible outcome

An authenticated student chooses an admin-managed topic, completes seven fresh PDF-grounded MCQs, receives cited feedback only after submission and builds a rolling topic-mastery score. An authenticated admin manages topics and views or deletes summary progress by institutional email.

## In scope

- Install and pin the minimum compatible LangChain/LangGraph packages in the existing project virtual environment.
- Verify AI STAR through LangChain's custom OpenAI-compatible base URL and JSON mode with a synthetic payload before depending on that adapter.
- Implement the approved deterministic LangGraph retrieval/generation/validation/repair graph without persistence or model-controlled database writes.
- Add the additive quiz schema and transactional functions, then apply that migration to the already confirmed development Supabase project.
- Extend verified identity with normalized institutional email for quiz profiles only.
- Implement topic administration, quiz generation, local grading, mastery, student progress, admin progress and atomic deletion.
- Test the complete local feature and existing Version 1 behavior, fix in-scope failures, and update operating documentation.

## Out of scope

- Deployment, Git mutations, automated retention jobs, full-question history, short-answer grading, question-bank editing, web search, leaderboards, exports and multi-course support.
- LangGraph checkpointers/stores, LangSmith, Deep Agents, subagents or model-selected database tools.
- More than three live AI STAR calls during this phase.
- Production-like load claims or the V2.2 human quality evaluation.

## Intended files and scope map

- `requirements.txt` — pin `langchain`, `langchain-openai` and `langgraph` versions that pass the adapter check.
- `study_guide/auth.py` — add normalized verified email to `Identity`; preserve domain/admin/user-key behavior.
- `study_guide/quizzing.py` — quiz schemas, difficulty mix, LangGraph workflow, validation, grading and safe errors.
- `study_guide/database.py` — narrow topic, profile, mastery, summary, analytics and deletion operations.
- `supabase/migrations/003_adaptive_quiz.sql` — tables, constraints, indexes, browser-role revocations and atomic/idempotent completion/deletion functions.
- `app.py` — Student Quiz/Progress and Admin Topics/Student Progress pages using existing navigation and error patterns.
- `tests/test_auth.py` — email normalization and identity regression coverage.
- `tests/test_quizzing.py` — mastery boundaries, graph branches, schema/domain validation, citations, grading and provider-payload privacy.
- `tests/test_quiz_database.py` — ownership, admin summaries, idempotency, transaction contract and deletion behavior with fakes/contract checks.
- `tests/test_app.py` — navigation, topic/attempt/results/progress/admin interface states where Streamlit AppTest supports them.
- `tests/test_schema.py` — migration security, constraints and function privilege assertions.
- Existing tests — update only fixtures/callers broken by the intentional `Identity` field change.
- `README.md`, `OPERATIONS.md`, `PROGRESS.md` — setup, data handling, migration, deletion, evidence and restart state.

No existing Version 1 answer-generation function or database schema is replaced.

## Implementation sequence

### 1. Compatibility and dependency checkpoint

1. Check current official package metadata and select the smallest compatible pinned versions.
2. Install only the three approved direct packages and their required dependencies into `.venv`.
3. Invoke AI STAR through `ChatOpenAI(base_url=..., model="deepseek-v4-flash")` using synthetic content and JSON mode.
4. Stop with evidence if ordinary invocation or JSON mode is incompatible; do not create a second hidden client path for quizzes.

Provider budget: one tiny compatibility call. A second call is reserved for the completed seven-question smoke set; one additional retry is allowed only if a real compatibility/output issue needs confirmation. No email, student data or course excerpt is used in the first probe.

### 2. Schema and persistence

1. Author `003_adaptive_quiz.sql` with `quiz_topics`, `quiz_profiles`, `topic_mastery` and `quiz_attempts`.
2. Add constraints for score/count ranges, case-insensitive topic uniqueness, foreign keys, idempotent attempt UUIDs and timestamps.
3. Revoke browser-role table/function access and restrict execution to the server role.
4. Add atomic functions for completion and student quiz-data deletion.
5. Verify the migration contract locally/static first, then apply it once to the confirmed development Supabase project.
6. Run bounded generated-data lifecycle checks and remove only the synthetic records created by this phase.

### 3. Quiz domain and graph

1. Reuse existing embedding, active-chunk retrieval, AI STAR limits, citation mapping and safe-error patterns.
2. Implement the three documented difficulty mixes and weighted mastery helper.
3. Build the deterministic graph: retrieve → generate → validate → optional repair → result/safe failure.
4. Validate exactly seven questions, four distinct options, one valid answer, exact difficulty mix, unique normalized questions, bounded fields and retrieved citation IDs.
5. Keep user key and email outside graph state and provider messages.
6. Grade locally and persist only the approved summary through the idempotent database function.

### 4. Student and admin interfaces

1. Add Quiz and My Progress to authenticated student navigation.
2. Keep the active quiz/results in Streamlit session state with a stable attempt UUID.
3. Require all seven selections and hide feedback before submission.
4. Add admin Topics and Student Progress pages with server-side role checks and explicit deletion confirmation.
5. Preserve readable mobile layout, labels, focus order and text/icon correctness states.

### 5. Verification, fixes and documentation

- Run focused tests during implementation, followed by the complete pytest suite.
- Run Python compilation and `pip check`.
- Verify no identity/email appears in provider payload captures, logs or browser errors.
- Use one live seven-question quiz smoke set after deterministic tests pass; inspect its structure/citations, not the full V2.2 quality matrix.
- Run a local authenticated critical-path browser check for admin topic creation, student quiz completion, mastery/progress display and admin deletion using synthetic records.
- Remove the phase's synthetic remote quiz records after confirming the exact targets.
- Update README, operations and progress with measured call count, latency, package versions, migration evidence, tests and known limits.

## Acceptance evidence

- LangChain custom-base-URL JSON mode returns parseable content from AI STAR with the selected pins.
- The graph returns exactly seven valid questions or a safe failure after at most one repair.
- All difficulty bands produce the exact approved mix in deterministic tests.
- Fabricated citations, duplicate questions/options, incomplete sets and invalid indexes are rejected.
- Submission calculates the expected score/mastery and a repeated attempt UUID cannot update it twice.
- Student A cannot read or mutate Student B's summaries/mastery; non-admin access to email analytics and topic mutation fails.
- Email is stored only in the quiz profile and absent from model/embedding inputs and logs.
- Admin deletion removes the target profile/mastery/summaries without touching another student or Version 1 chat history.
- The existing Study/Documents/chat flows and full regression suite pass.
- The development migration and local authenticated critical flow are verified with evidence.

## External effects and permissions included in approval

Approving this phase authorizes these bounded actions:

- install the selected LangChain/LangGraph packages into the project-local `.venv` and update `requirements.txt`;
- make at most three AI STAR calls under the provider budget above and the necessary small Gemini topic-embedding calls, with no identity in payloads;
- apply one additive `003_adaptive_quiz.sql` migration to the already confirmed development Supabase project;
- create and then delete clearly identified synthetic quiz topics/progress records used for verification.

Approval does not authorize deployment, Git operations, deleting real student/course data, changing provider accounts, adding paid services or exceeding the three-call AI STAR cap.

## Tools and fallback

- Use Context7 and official LangChain/LangGraph documentation for the selected versions.
- Use `rg` and targeted reads; the codebase remains small enough to skip Serena.
- Use pytest, Streamlit AppTest, compilation and dependency checks already present in the project.
- Use the existing Brave browser integration for the local authenticated smoke check if available; otherwise record that browser portion as unverified rather than installing another browser.
- If AI STAR is incompatible with LangChain JSON mode, stop the phase as blocked at the approved stack boundary and present the exact compatibility evidence. Do not silently revert to Option A or add a parallel quiz provider path.

## Model and usage forecast

- Current available coding model: GPT-5 in this session; reasoning level and fallback availability are not exposed.
- Recommended effort: high for schema/idempotency/privacy and graph validation; medium for Streamlit UI and documentation.
- Estimated work: 10–16 human-equivalent hours, 3–5 context sessions and approximately 2–4 five-hour usage windows; confidence is medium-low.
- AI STAR cap: three calls, expected roughly 8,000–25,000 total input/output tokens for this phase; record actual response usage when exposed.
- Gemini: a few short topic embeddings only; expected usage is negligible relative to existing document ingestion.
- Codex token/spend telemetry is unavailable and will not be inferred from session count.

## Git checkpoint

Codex will not stage, commit, branch, merge, tag or push. After phase evidence is complete, provide user-run commands scoped to the changed files and recommend a commit such as `feat: add adaptive quiz workflow`.

## Approval request

Approve this whole V2.1 phase for end-to-end execution, including the bounded package installation, maximum three AI STAR calls, additive development Supabase migration and cleanup of phase-created synthetic quiz records described above.

## Approval record

The user approved the whole V2.1 phase on 2026-10-10 by replying “yes.” This authorizes the bounded package installation, maximum three AI STAR calls, additive migration on the confirmed development Supabase project, implementation/testing and cleanup of phase-created synthetic quiz records. It does not authorize Git mutations or deployment.

## Execution record — 2026-10-10

- Pinned `langchain 1.4.4`, `langchain-openai 1.7.0` and `langgraph 1.2.14`.
- Implemented the deterministic graph, strict seven-MCQ validation, local grading, rolling mastery, admin topics, student/admin progress and profile deletion.
- Applied `003_adaptive_quiz.sql` to confirmed development project `kjxixskoeihbitcohhuo`. A synthetic two-attempt lifecycle proved mastery `71 → 88`, idempotent duplicate handling, admin email lookup and cascade deletion; all synthetic rows were removed.
- LangChain custom-base-URL JSON compatibility passed (reported usage: 45 input, 57 output, 161 total). The other two allowed calls attempted one full grounded quiz each and both reached the safe provider-error path; visible balance use increased by roughly 480 and 470 weighted units. No fourth call was made.
- Reduced quiz evidence/output bounds and required concise fields after the smoke failures. This change is covered deterministically but could not be live-retested under the approved call cap.
- All 91 tests, compilation, dependency consistency, Streamlit health and signed-out privacy copy pass. Authenticated browser and live full-quiz quality/latency remain for V2.2.
- No Git operation or deployment occurred.
- The user approved V2.1 on 2026-10-10 by replying “approve v2.1.” The phase is signed off with the live full-quiz provider limitation recorded above; provider reliability and question-quality evaluation remain in the planned V2.2 phase.
