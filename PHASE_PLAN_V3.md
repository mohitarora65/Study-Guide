# V3 Proposal — Structured Study Modes and Question Extraction

**Status:** V3.1–V3.4 LOCAL PASS; V3.5 MIGRATION PASS — deployment and authenticated workflow review remain pending.

## Goal

Let an admin upload either theory material or question material, extract reusable questions with source provenance, and let students study in Mid Sem, End Sem, Quiz or Overall mode.

## Proposed product flow

### Admin upload

Each upload requires:

1. **Material type:** `Theory` or `Questions`.
2. **Coverage:** one or more of `Mid Sem`, `End Sem`, or `Quiz`.

`Overall` is not stored as another tag; it is the union of all three coverage groups.

### Question-source priority

1. Approved questions extracted from `Questions` uploads.
2. Approved exercise/question sections extracted from `Theory` uploads.
3. The existing bundled reviewed bank as a fallback during migration.

Every extracted question retains its source document, PDF page and extraction status. Draft or rejected questions must never reach students.

### Student experience

The student first selects one of four study modes:

- **Mid Sem:** only content and approved questions tagged Mid Sem.
- **End Sem:** content and approved questions under the agreed End Sem coverage rule.
- **Quiz:** content and approved questions tagged Quiz.
- **Overall:** union of all available coverage.

The selected mode scopes both grounded Study answers and adaptive-quiz questions so the two experiences do not disagree about the syllabus boundary.

## Proposed minimal data changes

- Add material type and coverage metadata to uploaded documents.
- Add an extracted-question table containing source/version/page, prompt, options or answer structure, correct answer, explanation, difficulty, coverage, and review status.
- Preserve existing document/chunk IDs, private storage, page citations, topic mastery and attempt summaries.
- Do not store generated questions in student attempt rows; keep the current summary-only privacy boundary.

The exact schema remains provisional until the question format and review workflow are approved.

## Proposed extraction and review flow

1. Validate and index the PDF using the existing private ingestion pipeline.
2. For `Questions`, prioritize question-numbered blocks, exercises and answer-key sections.
3. For `Theory`, index all content for Study and optionally identify explicit exercise/question sections as secondary candidates.
4. Convert candidates into a strict question schema with source-page citations.
5. Place every candidate in an admin review queue; this review is mandatory before student use.
6. Admin approves, edits or rejects the question before activation.
7. Student mode and mastery determine which approved questions are sampled.

No model-generated answer should be trusted merely because it is structurally valid; correctness and unique-answer review remain release gates.

## Delivery phases

### V3.1 — Requirements and schema

Freeze question formats, answer-key handling, mode semantics, review rules, migration behavior and acceptance criteria. Produce PRD, architecture and migration plan updates only.

### V3.2 — Upload classification

Add Theory/Questions and coverage controls to the admin upload flow, persist metadata, and filter retrieval by study mode. Include migration and access-control tests.

### V3.3 — Question extraction and review

Extract cited candidates, add the admin review queue, and activate only approved questions. Any paid/provider-backed extraction requires a separate bounded approval and cost/privacy record.

### V3.4 — Student study modes

Add Mid Sem, End Sem, Quiz and Overall selection, apply it consistently to Study retrieval and quiz sampling, and preserve existing mastery behavior.

### V3.5 — Migration and controlled rollout

Classify existing documents, migrate the bundled bank without losing provenance, run source review and authenticated browser QA, then perform a separately approved production migration/deployment.

## Acceptance direction

- Admin cannot upload without selecting material type and coverage.
- Every student-visible extracted question is approved and has a valid source page.
- Question uploads take precedence over theory-derived candidates without duplicating equivalent questions.
- Study and quiz obey the same selected coverage.
- Overall equals the union of the three stored coverage groups.
- Existing chats, documents, mastery and attempt history remain intact.
- Unsupported or unreviewed content fails safely.

## Decisions

1. **APPROVED, 2026-10-11:** admin approval is mandatory for every extracted question before student use.
2. **DELEGATED_DECISION, 2026-10-11:** accept both MCQ and descriptive source questions. Only complete four-option MCQs can be approved for Adaptive Quiz; descriptive items remain editable drafts.
3. **DELEGATED_DECISION, 2026-10-11:** documents and questions may have multiple coverage tags. End Sem filters the `end_sem` tag; an admin makes content cumulative by assigning both tags.
4. **DELEGATED_DECISION, 2026-10-11:** use “Class Quiz” for the syllabus tag so it is distinct from the Adaptive Quiz feature.
5. **DELEGATED_DECISION, 2026-10-11:** extraction is an explicit admin action after upload and uses deterministic local parsing only—no paid model call or new dependency.
6. **DELEGATED_DECISION, 2026-10-11:** approved extracted questions are preferred; the existing 33 reviewed questions remain the fallback.

Trigger: direct user message `bhai tu sambhal ab`. Delegation covers safe local code, tests and documentation only. Applying migrations, production data changes, deployment, credentials, paid calls and Git mutations remain excluded.

## Boundaries

- No OCR, new provider, dependency, migration, paid extraction request, production write, deployment or Git mutation is authorized by this proposal.
- Existing secrets, authentication, server-only database access and private PDF storage remain unchanged.

## Local execution result — 2026-10-11

- Added upload classification, shared study-mode selection, scoped retrieval, deterministic page-linked extraction, private review records, an admin review page and approved-question-first quiz sampling.
- Prepared additive migration `004_study_modes_and_questions.sql`; it was not applied anywhere.
- Verification: 126 tests passed; compilation, dependency integrity, diff whitespace and localhost Streamlit health passed.
- Not tested: real migration execution/rollback, existing-document production classification, authenticated browser review/upload flow, and deployed behavior.

## Migration result — 2026-10-11

- User specifically approved applying migration `004` to the current Supabase production project.
- Preflight confirmed the table, columns and scoped RPC were absent. The migration ran inside an explicit transaction and Supabase returned `Success. No rows returned`.
- Postflight confirmed: table and RPC exist; RLS is enabled; `anon` and `authenticated` cannot select the table or execute the RPC; `service_role` has the required table/RPC access.
- The one existing document defaulted to Theory with all three coverage tags; the new question-candidate table contains zero rows. No chat, quiz-attempt or mastery row was changed.
- Rollback was not exercised because it would be destructive. Application deployment and production workflow testing remain separate actions.
