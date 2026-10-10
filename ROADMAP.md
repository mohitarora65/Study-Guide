# Roadmap — Grounded Mathematics Study Guide

**Status:** Version 1 APPROVED; Version 2 APPROVED — user said “reduce tokens rest is fine” on 2026-10-10
**Date:** 2026-10-10
**Versions:** Version 1 deployed study guide; Version 2 adaptive quiz

## 1. Delivery Strategy

Build the smallest secure vertical slices in dependency order. Each phase needs one whole-phase approval, then runs end-to-end through implementation, tests, fixes and documentation before review. Git staging, commits and pushes remain user-controlled.

Version 1 delivered the grounded study guide. Version 2 is the separately planned adaptive-quiz feature approved through V2-G1–G4. No third product version is planned.

## 2. Dependency Order

```text
V1.1 Foundation and identity
        ↓
V1.2 Document ingestion and retrieval store
        ↓
V1.3 Grounded student assistant
        ↓
V1.4 Evaluation and release hardening
        ↓
V1.5 Controlled deployment and final audit
        ↓
V2.1 Adaptive quiz implementation
        ↓
V2.2 Quiz evaluation, rollout and audit
        ↓
Post-completion interview artifacts
```

## 3. Version 1 Phases

### Phase V1.1 — Foundation, Identity and Data Boundary

**User-visible outcome:** A locally running Streamlit application where a verified `iiti.ac.in` Google account can enter, a wrong-domain user is denied, and an allowlisted admin sees document navigation.

**Deliverables:**

- minimal project structure, pinned dependencies and safe configuration examples;
- Streamlit Google OIDC login/logout;
- exact verified-domain validation and secret admin allowlist;
- opaque internal user key without stored email;
- initial Supabase schema/migrations for documents, chunks, threads and messages;
- server-only database access and denied public data access;
- basic signed-out, student and admin navigation states;
- tests for domain validation, role checks, ownership helpers and configuration failures;
- setup/run/test instructions and updated progress record.

**Exit criteria:** Local checks pass; wrong-domain/non-admin paths fail closed; secrets are absent from source and logs; schema can be applied to a development Supabase project. No PDF or Gemini flow is required yet.

**External needs:** Development Supabase project, Google OIDC client details and secret values supplied through local/hosting secret management—not chat or source control. Creating accounts, enabling paid services or trusting hooks requires separate approval if not already done.

### Phase V1.2 — Admin PDF Ingestion and Retrieval Store

**User-visible outcome:** An admin can upload one approved PDF, see processing/ready/failed status, retry safely and delete it; ready chunks are searchable with real page metadata.

**Deliverables:**

- PDF signature/size/parser validation and generated private object paths;
- private Supabase Storage upload;
- page-by-page `pypdf` extraction and low-text warnings;
- page-bounded chunks, Google `gemini-embedding-2` embeddings at 768 dimensions and pgvector search;
- transactional active-version switch, idempotent retry and duplicate detection;
- deletion that immediately removes search availability and retries cleanup safely;
- admin document interface and progress/error states;
- unit/integration tests using small representative fixtures, including corrupt and text-poor PDFs.

**Exit criteria:** Sampled chunks map to correct PDF pages; failed replacement preserves the previous ready version; deleted content cannot be retrieved; no partial index becomes active; actual corpus size and embedding storage are measured.

### Phase V1.3 — Grounded Student Assistant and Private History

**User-visible outcome:** An authenticated student asks a question, receives a LaTeX-capable answer with validated document/page citations or the standard insufficient-material refusal, and can revisit/delete only their own chats.

**Deliverables:**

- bounded query and conversation validation;
- vector retrieval over active ready versions only;
- calibrated initial evidence threshold and fixed early refusal;
- structured answer contract using retrieved chunk IDs; the user approved AI STAR `deepseek-v4-flash` integration and accepts question/excerpt transmission despite unknown retention. User reports OpenAI-compatible chat completions/JSON output, a `×0.1` balance deduction coefficient, and hard stop at zero. Synthetic live requests passed: the chat/JSON probe returned HTTP 200 and response model `DeepSeek-V4-Flash-0731`; a grounded answer cited the expected PDF page 25. Dollar pricing and data-handling claims remain unverified. Official DeepSeek API aliases/rates do not establish AI STAR's mapping or price;
- citation validation/mapping and at most one bounded repair attempt;
- chat/history UI, thread ownership and permanent deletion;
- clear quota, timeout, database and invalid-output states;
- per-user throttling and global concurrency guard;
- unit/integration tests for citation integrity, refusal, injection text, failures and cross-user isolation.

**Exit criteria:** Critical chat/history flows pass; model-generated filenames/pages cannot enter citations; unsupported evidence refuses; students cannot access another student's history; failures never fabricate an answer.

### Phase V1.4 — Grounding Evaluation, Security and Release Hardening

**User-visible outcome:** A tested pilot candidate with recorded evidence for grounding, access control, accessibility, reliability and measured limits.

**Deliverables:**

- teaching-assistant-authored 40-question set required by the PRD;
- repeatable evaluation runner and recorded citation/refusal/formula results;
- retrieval/chunk/threshold tuning using the real corpus without weakening refusal safeguards;
- authentication/authorization, prompt-injection, filename/input and secret-leak tests;
- timeout/quota/storage/database failure exercises;
- Streamlit AppTest plus targeted Playwright critical-path checks;
- keyboard, focus, labels, contrast and mobile-width review;
- cold-start, latency, memory and small concurrent-load measurements;
- risk register, known limits and release-candidate README.

**Exit criteria:** PRD thresholds are met or failures are reported honestly; no critical security issue remains; formula errors that block release are fixed; tests and untested areas are recorded; the result is labeled no higher than evidence supports.

**User dependency:** The teaching assistant supplies or approves the 40 evaluation questions and manually judges citation support and high-risk formulas.

### Phase V1.5 — Controlled Deployment, Final Audit and Pilot Release

**User-visible outcome:** An approved Streamlit Community Cloud deployment connected to production-configured Google OIDC, Supabase, paid Gemini embeddings and the separately approved answer provider, with verified smoke tests and rollback guidance.

**Deliverables:**

- deployment configuration and secret checklist;
- explicit pre-deployment cost, privacy and rollback review;
- deployment only after separate user permission;
- deployed login, admin upload, chat, citation, refusal, history and deletion smoke tests;
- quota/cost alerts or hard limits where the provider supports them;
- complete requirement-to-evidence audit across security, privacy, reliability, performance, deployment and documentation;
- final README, operating notes and accurate progress handoff;
- release approval request and user-run Git checkpoint guidance.

**Exit criteria:** Deployment evidence is recorded; no secret is exposed; critical flows work at the real URL; rollback is understood; final audit categories are PASS/FAIL/NOT TESTED/N/A with evidence; user explicitly approves the release.

## 4. Version 2 — Adaptive Quiz

### Phase V2.1 — Complete Adaptive Quiz Implementation

**User-visible outcome:** An authenticated student can choose an admin-managed topic, complete seven fresh PDF-grounded MCQs, receive delayed cited feedback and build a rolling mastery score; an admin can manage topics and view/delete student progress by institutional email.

**Deliverables:**

- verify and pin compatible `langchain`, `langchain-openai` and `langgraph` packages;
- run a bounded synthetic AI STAR compatibility probe through LangChain custom-base-URL JSON mode before committing to the adapter;
- add the deterministic LangGraph batch-generation/validation workflow without a checkpointer or model-controlled database tools; approved batch strategy stops on failure within three requests, without repair;
- add the quiz topic, profile, attempt-summary and mastery migration with denied browser access and transactional/idempotent completion/deletion functions;
- extend verified identity with normalized institutional email while excluding it from provider payloads and logs;
- add quiz retrieval, exact seven-MCQ validation, deterministic grading and rolling-mastery logic;
- add student Quiz/Progress and admin Topics/Student Progress pages;
- add focused unit, database-contract, graph-branch, Streamlit and Version 1 regression coverage;
- apply the additive migration only to the already confirmed development Supabase project after the V2.1 phase approval explicitly includes that write;
- complete authenticated local smoke checks and update README, operations and progress records.

**Exit criteria:** The AI STAR LangChain adapter works or the phase stops with evidence; exactly seven grounded MCQs are enforced; invalid/fabricated outputs create no attempt; grading and mastery are deterministic; duplicate submission is idempotent; student isolation/admin authorization pass; email is absent from AI requests/logs; the full regression suite passes; the approved development migration and local critical flow are verified.

**Out of scope:** automated retention jobs, full-question history, question-bank editing, short-answer grading, web search, leaderboards, exports, multi-course support and deployment to a new hosting service.

### Phase V2.2 — Quiz Evaluation, Production Rollout and Final Audit

**User-visible outcome:** The live Streamlit application exposes the approved quiz workflow with reviewed question quality, documented operational limits and a rollback path.

**2026-10-10 redesign:** live quiz generation was replaced locally by a bundled, source-checked bank after bounded provider/model strategies remained unreliable. The student flow now makes zero generation/embedding calls; provider-generation code is retained only for offline evaluation. See `PHASE_PLAN_QUESTION_BANK.md`.

**Deliverables:**

- create a compact, admin/TA-approved quiz evaluation matrix with three representative topics assigned across the three mastery bands;
- generate and manually review one seven-question set for each topic/band assignment (three generations, 21 MCQs total) for question clarity, correct option, explanation, difficulty and citation support;
- exercise insufficient-topic evidence, provider failure, duplicate submission, session loss and admin deletion behavior;
- measure quiz-generation latency and a small concurrent burst without claiming class-wide capacity;
- complete privacy/security/accessibility review for stored emails and both quiz interfaces;
- update operations with migration rollback, quiz-data deletion and incident steps;
- provide precise user-run Git commit/push instructions; Streamlit deployment updates only after the user's push;
- verify the deployed student and admin critical paths using test records and remove those records afterward;
- complete the Version 2 requirement-to-evidence audit and request release sign-off.

**Exit criteria:** Every sampled MCQ is reviewed or any failure is fixed/retested; deployed login, topic, quiz, results, progress, admin analytics and deletion work; no critical privacy/security finding remains; provider usage/latency and known limits are recorded; rollback is documented; the user explicitly approves the Version 2 release.

**User dependencies:** The admin provides/approves the initial topic names and manually reviews the evaluation matrix. The user performs Git staging, commit and push. Deployment and deletion of live test records remain separately visible actions within the approved phase.

## 5. Post-Completion Interview Artifacts

Because this is a Learning/Production project, after audited product completion:

1. create 2–3 distinct 16:9 LaTeX Beamer preview templates using real project content;
2. compile and visually inspect previews where tooling permits;
3. obtain the user's template choice;
4. create and verify the complete editable interview deck and PDF;
5. create one organized LaTeX source and PDF containing exactly 200 answered, difficulty-labeled project interview questions: 150 technical and 50 decision/reflection.

These are project artifacts, not a third product version.

## 6. AI Model and Usage Plan

### What is verified

- Official OpenAI guidance currently positions GPT-6.1 Sol for complex technical work and Luna for focused repeatable work, with medium/default effort as a balanced starting point.
- Exact model availability, reasoning controls, credits, five-hour allowance and remaining usage depend on the user's plan/client and are not visible to this project workspace.
- Application providers are separate by role: Google `gemini-embedding-2` at 768 dimensions is approved for V1.2/V1.3 query retrieval. The user approved AI STAR `deepseek-v4-flash`; synthetic chat-completions/JSON and grounded-answer checks passed, with the expected page citation. The ×0.1 deduction and stop-at-zero are user-reported; dollar pricing is unknown. Retention is unknown and explicitly accepted by the user; no-training is a user report, not verified policy.

Before approving V1.1, confirm the actual selectable Codex model and reasoning level from the model control (or `/model` in the CLI) and visible usage status if available. Do not interpret a chat session as a quota reset.

### Phase forecast

| Phase | Version | Risk | Recommended Codex route* | Reasoning | Human-equivalent effort | Chat/context sessions | Five-hour usage windows | Confidence |
|---|---|---|---|---|---:|---:|---:|---|
| V1.1 foundation/identity | V1 | Medium | GPT-6.1 Sol; available Sol fallback | Medium | 5–9 h | 2–3 | 1–2 | Medium |
| V1.2 ingestion/index | V1 | High | GPT-6.1 Sol | Medium→High for transaction/failure review | 8–14 h | 2–4 | 2–3 | Medium |
| V1.3 grounded assistant | V1 | High | GPT-6.1 Sol | High for citation/security logic | 10–18 h | 3–5 | 2–4 | Medium-low |
| V1.4 evaluation/hardening | V1 | High | GPT-6.1 Sol; Astra only if available and justified | High/Extra High for final review | 10–18 h plus TA judging | 3–5 | 2–4 | Medium-low |
| V1.5 deployment/audit | V1 | High | GPT-6.1 Sol | Medium→High | 5–9 h plus approvals | 2–3 | 1–2 | Medium |
| V2.1 adaptive quiz implementation | V2 | High | Current Codex GPT-5 session; no fallback verified | High for identity/schema/idempotency, medium for UI | 10–16 h | 3–5 | 2–4 estimated | Medium-low |
| V2.2 evaluation/rollout/audit | V2 | High | Current Codex GPT-5 session; no fallback verified | High for review/security, medium for rollout | 6–10 h plus TA review | 2–3 | 1–2 estimated | Medium-low |
| Interview artifacts | Post-completion | Medium | Luna/Sol for generation; Sol/Astra for verification | Medium→High | 8–14 h plus template choice | 2–4 | 1–3 | Medium |

\*Recommendations follow official guidance, not proof of account access. Use the lightest actually available model/effort that passes the phase checks; record the selected model and visible usage after every phase.

**Estimated Version 2 total:** 16–26 human-equivalent hours, 5–8 chat/context sessions and approximately 3–6 five-hour usage windows. The client does not expose actual Codex token use or remaining allowance, so these are planning ranges rather than quota promises. Add 8–14 hours and 1–3 windows for post-completion interview artifacts.

**Application-provider estimate:** V2.1 allows at most three AI STAR calls: one tiny adapter probe, one complete seven-question smoke set and one retry only if needed. V2.2 adds three successful seven-question generations, one for each representative topic/mastery-band assignment. Deterministic fixtures cover every remaining branch without provider calls. A rough combined range is 30,000–80,000 AI STAR input/output tokens, with low confidence until the first seven-question payload is measured. Gemini adds one small topic embedding per quiz generation. Exact deductions and monetary cost remain unknown and must be recorded where available.

API token/spend estimates for Codex are **unknown** because this workspace cannot see account billing or token telemetry. Gemini usage will be measured from actual ingestion and question traces during development; no safe total can be inferred from the reported 10-million-token allowance alone.

## 7. Phase Approval and Git Checkpoints

Before each implementation phase, present one compact plan covering scope, files, tests, permissions, model/effort and usage forecast, then ask: “Approve this whole phase for end-to-end execution?” Once approved, complete and test the whole phase without task-by-task approval loops.

After each accepted phase, suggest user-run commands scoped to the project files: `git status`, `git diff --stat`, explicit `git add <paths>`, `git diff --cached`, and a phase-specific commit. The AI does not stage, commit, branch, merge, rebase or push.

## 8. V2-G5 Approval Effect

Approving this roadmap authorizes preparation of the V2.1 whole-phase plan only. It does not yet authorize dependency installation, source changes, the Supabase migration, provider calls, deployment or Git mutations. V2.1 implementation begins only after separate V2-G6 whole-phase approval that identifies those actions.

## 9. Model Guidance Sources Checked on 2026-10-09

- [Official OpenAI model-selection guidance](https://developers.openai.com/api/docs/guides/model-selection)
- [Official models available in Work and Codex](https://learn.chatgpt.com/docs/models)
