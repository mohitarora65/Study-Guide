# Research — Grounded Mathematics Study Guide

**Status:** APPROVED — user replied “yes” on 2026-10-09
**Date:** 2026-10-09
**Scope:** Product and feasibility research only; no stack has been selected.

## Executive Finding

The proposed website is feasible as a tightly scoped pilot for approximately 120 enrolled students, but a zero-cost deployment cannot honestly promise production-grade uptime, unlimited concurrency, or fixed AI capacity. The product can strongly reduce unsupported answers through page-aware retrieval, conservative refusal, claim-level citations, and a teacher-reviewed evaluation set. It cannot rely on a prompt alone to guarantee that a generative model never adds unsupported content.

## 1. Grounding and Refusal

Retrieval-augmented generation has two distinct stages: retrieve relevant material, then generate from that material. Retrieval quality and generation faithfulness must therefore be tested separately. Google describes these two stages explicitly in its RAG overview.

Research on retrieval-augmented long-form answering found that even correct answers can include ungrounded sentences. This means “use only the supplied text” is a system requirement that needs verification and abstention, not merely a prompt instruction.

For this project, a supported response should meet all of these conditions:

1. Relevant chunks are retrieved from the approved document collection.
2. Each factual or mathematical claim is supported by the retrieved text.
3. Every displayed citation maps to a real document and page.
4. If evidence is absent, weak, or conflicting, the system returns a standard insufficient-material response.
5. The answer generator has no web-search tool or alternate knowledge source.

Google's grounding documentation defines perfect grounding as every claim being supported by one or more supplied facts and describes claim-level citations. That is an appropriate evaluation model for this product, even if a different provider is selected.

### Recommended Quality Controls

- Preserve document name and PDF page number during extraction and chunking.
- Use a conservative retrieval threshold and allow fewer than the maximum number of chunks when evidence is weak.
- Require citations to come from retrieved metadata rather than allowing the model to invent page numbers.
- Use a fixed refusal message when the minimum evidence rule is not met.
- Create a teacher-reviewed test set containing both answerable and deliberately unanswerable questions.
- Manually inspect citation correctness and mathematical faithfulness before student release.
- Treat formulas, definitions, theorem conditions, and worked-example assumptions as high-risk claims.

## 2. PDF Ingestion

The initial corpus—notes and one or two mostly text-searchable books—is small enough for a simple page-aware ingestion pipeline. OCR is not a core Version 1 requirement.

The pipeline should:

- accept PDF files from the admin only;
- extract text one page at a time;
- normalize repeated headers and footers where practical;
- split text into overlapping chunks without losing page metadata;
- generate embeddings once during ingestion, not on every question;
- report indexing progress and failures;
- delete both the file record and derived chunks when the admin removes a document.

Equations extracted from PDFs may be imperfect even when body text is selectable. The release check therefore needs representative formula-heavy pages. Image-only formulas or diagrams should be disclosed as a limitation rather than silently interpreted.

## 3. Authentication and Authorization

Streamlit currently supports OpenID Connect through `st.login`, `st.user`, and `st.logout`, including Google and Microsoft identity providers. A verified identity-provider email can be checked against the approved college domain after login.

Domain checking must be server-side and exact—for example, the address must end with `@approved.example`, not merely contain that text. The admin role must be assigned from a server-side allowlist or database role and never from a browser field.

If Supabase is considered later, its documentation recommends Row Level Security for exposed tables and combining it with Auth. Its built-in email sender is currently limited to two authentication emails per hour, so email/password signup using the default sender would not work for onboarding a class of 120. OIDC through the college's existing Google or Microsoft identity provider is likely the smallest viable path, subject to G3 verification and user approval.

## 4. Free-Tier Feasibility

### Streamlit Community Cloud

Streamlit documents approximate Community Cloud limits of up to 2 CPU cores, 2.7 GB memory, and 50 GB storage, and states that limits may change without notice. Apps without traffic for 12 hours hibernate and must wake on the next visit. Streamlit also warns that apps serving many or large files may hit resource limits.

Implication: it is suitable for an initial educational pilot, but the app must avoid loading the entire embedding index or every PDF into memory per session. Simultaneous class-wide use must be load-tested and cannot be guaranteed on the free service.

### Supabase

Supabase currently documents a Free plan with 500 MB database size, 1 GB file storage, 5 GB egress, and 50,000 monthly active users. The user count is ample for 120 students, while database, storage, and egress are the practical limits. Free projects may be paused after inactivity, and exceeding quotas can lead to service restrictions.

Supabase supports `pgvector` for storing embeddings and HNSW vector indexes. This could keep authentication, chat history, document metadata, and vector search in one service, but the exact fit depends on corpus size and embedding dimensions and belongs in G3.

### Generative AI

Google's Gemini Developer API currently offers model-dependent free access, but rate limits are per project and vary by model. The active quota must be checked in AI Studio rather than assumed from static documentation. Google's pricing page also states that content sent through the free tier may be used to improve its products, while paid-tier content is not.

Implications:

- A free AI tier is acceptable only if the user approves that data handling after provider comparison.
- Student identity and email must never be included in model requests.
- Requests should send only the question and retrieved excerpts needed for the answer, not entire books.
- The UI must handle quota errors clearly and retry only bounded, transient failures.
- A zero-cost launch needs a documented upgrade or shutdown decision if real usage exceeds quotas.

## 5. Security and Privacy

The main risks are unauthorized access, one student reading another student's history, leaked API keys, malicious question text, malicious instructions embedded inside a PDF, and accidental disclosure of course material.

OWASP notes that indirect prompt injection can arrive through documents used by RAG systems. Uploaded text must therefore be treated as reference data, not executable instructions. Version 1 will not give the model tools that can modify data, access secrets, browse the web, or perform actions.

Required safeguards:

- HTTPS deployment and secrets stored only in the hosting platform's secret manager.
- Verified college-domain login and a separate server-side admin allowlist.
- Per-user authorization for chat history.
- File-type and size validation before parsing.
- No executable PDF content, macros, or links are followed.
- No user email, identity token, or secret is sent to the language model.
- Admin deletion removes stored PDF objects and derived chunks.
- Logs avoid raw student questions and retrieved book passages unless debugging is explicitly enabled for a limited period.

## 6. Product Recommendation Feeding the PRD

Proceed with a narrow Version 1:

- one course and one approved collection;
- institutional OIDC login with exact domain enforcement;
- admin-only document ingestion;
- page-aware retrieval;
- answers with deterministic citation metadata;
- conservative insufficient-material refusal;
- private student chat history;
- a teacher-authored grounding test set;
- a pilot deployment with visible quota and availability limitations.

Do not add agents, web search, quizzes, analytics, multi-course tenancy, OCR, or complex orchestration in Version 1.

## 7. Decisions Deferred to G3/G4

- Which identity provider the college domain uses: Google Workspace or Microsoft Entra.
- AI generation and embedding provider, including free-tier data-use terms.
- Hosted Postgres/vector service versus a simpler local index with external persistence.
- Final hosting platform and capacity plan.
- Exact automatic chat-retention period; Version 1 must at minimum support user deletion and admin deletion of course data.
- Measured retrieval threshold, chunk size, and concurrency limits after corpus-based tests.

## Sources

- [Google Cloud: RAG overview](https://cloud.google.com/use-cases/retrieval-augmented-generation)
- [Google Cloud: Check grounding with RAG](https://cloud.google.com/generative-ai-app-builder/docs/check-grounding)
- [Groundedness in Retrieval-augmented Long-form Generation](https://arxiv.org/abs/2404.07060)
- [Streamlit: User authentication and information](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Streamlit: Community Cloud resource limits and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- [Streamlit: Static-file limitations](https://docs.streamlit.io/develop/concepts/configuration/serving-static-files)
- [Supabase: Free-plan quotas](https://supabase.com/docs/guides/platform/billing-on-supabase)
- [Supabase: Authentication rate limits](https://supabase.com/docs/guides/auth/rate-limits)
- [Supabase: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase: Vector columns](https://supabase.com/docs/guides/ai/vector-columns)
- [Google AI: Gemini API pricing and data-use distinction](https://ai.google.dev/gemini-api/docs/pricing)
- [Google AI: Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [OWASP: Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

## Version 2 Research — Adaptive Quiz Agent

**Status:** APPROVED — user replied “yes” on 2026-10-09
**Date:** 2026-10-09

### Finding

The proposed quiz is feasible using the existing retrieval, generation, validation and Supabase boundaries. It does not need an open-ended autonomous agent. The dependable design is a constrained workflow: retrieve evidence for an admin-defined topic, generate exactly seven structured MCQs, validate the complete set, grade locally, and update mastery in one database operation.

### Structured Quiz Generation

LangChain's current structured-output interface can return a schema-validated object and can retry schema errors. This fits an MCQ payload containing question text, four options, one correct option, difficulty, explanation and cited retrieved-chunk IDs. Schema validation alone is insufficient: application validation must also enforce exactly seven questions, distinct option text, a valid answer index, unique questions within the attempt and citations limited to retrieved chunks.

The current AI STAR endpoint already supports JSON output, and Version 1 already validates generated JSON and performs one bounded repair attempt. G3 should therefore compare keeping this small direct implementation with adding LangChain. A framework is justified only if it reduces validation/orchestration code enough to offset a new dependency and provider-adapter risk.

### Stateful Adaptation

Long-term mastery is application data, not conversational agent memory. LangGraph distinguishes thread checkpoints from cross-thread long-term stores and warns that in-memory persistence is lost on process restart. Because Supabase is already the system of record, topic mastery and attempt summaries should remain in Supabase even if LangGraph is selected for workflow orchestration.

The proposed transparent scoring rule is:

- Attempt score: `correct answers / 7 × 100`.
- First attempt mastery: the attempt score.
- Later mastery: `0.60 × latest attempt score + 0.40 × previous mastery`, rounded to a whole percentage.
- Foundation (`0–49`): four easy and three medium questions.
- Developing (`50–79`): two easy, four medium and one hard question.
- Strong (`80–100`): one easy, three medium and three hard questions.

This is a simple product heuristic, not a psychometrically validated measure. The UI must call it “mastery score,” explain the weighting, and avoid presenting it as an academic grade.

### Cost and Latency

Generate all seven questions in one bounded model request after one topic embedding/search. Submission is graded against the validated answer key in application code and requires no model call. This creates predictable provider usage per attempt and avoids seven sequential generation calls. If generation or validation fails, no attempt or mastery change is stored.

### Grounding and Quality Risks

- A topic name may retrieve insufficient or overly narrow evidence. In that case, quiz creation must fail clearly rather than use model knowledge.
- A structurally valid MCQ can still be ambiguous or unsupported. The evaluation set must include human review of the question, answer, explanation and citation together.
- Fresh generation may produce semantically similar questions across separate attempts. Cross-attempt deduplication is excluded because summary-only history intentionally does not retain question text.
- Difficulty labels are model instructions rather than calibrated item-response measurements. Release testing must verify that the three mixes are recognizably different without claiming formal calibration.

### Identity and Privacy

The existing server uses a secret Supabase credential and performs authorization before database operations. Supabase documents that service-role/secret access bypasses Row Level Security, so every new database function must continue to enforce ownership in server code and revoke browser-role access. Student email must never enter embedding or generation requests.

The smallest explicit retention rule is manual course-end deletion: quiz summaries, mastery and institutional email remain until an admin deletes that student's quiz profile. The dashboard must provide that deletion action and operations documentation must require it at course end. Automatic scheduled retention is deferred because the application has no course calendar or background worker.

### Recommendation Feeding G3/G4

- Preserve the existing Gemini embedding, pgvector retrieval and AI STAR generation services.
- Store mastery and summary history in Supabase; do not use agent memory as the source of truth.
- Compare a direct structured workflow against LangChain/LangGraph before adding dependencies.
- Use one model call per quiz, one bounded repair attempt, deterministic grading and an atomic mastery update.
- Keep question text and selected answers only in the active Streamlit session/results view; persist summary data only.
- Keep all quiz tables and functions inaccessible to browser roles; the Streamlit server remains the authorization boundary.

### Version 2 Sources

- [LangChain: Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangChain: Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Supabase: API keys and service-role behavior](https://supabase.com/docs/guides/getting-started/api-keys)
- [Supabase: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase: Database function privileges](https://supabase.com/docs/guides/database/functions)

