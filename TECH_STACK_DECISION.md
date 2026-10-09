# Technology Stack Decision — Grounded Mathematics Study Guide

**Status:** APPROVED — user said “the rest is fine” and confirmed paid API access on 2026-10-09
**Date:** 2026-10-09
**Decision owner:** User

**Approved clarification, 2026-10-09:** V1.2 retrieval uses Google `gemini-embedding-2` at 768 dimensions. User approved AI STAR generation at `https://ai.starimg.ru/v1` with model `deepseek-v4-flash`, and explicitly accepts sending questions/retrieved excerpts despite unknown data retention. User reports OpenAI-compatible chat completions/JSON output, a `×0.1` token-balance multiplier, and requests stopping at zero. Dollar pricing and the user's report that data is not used for training are not independently verified; storage duration remains unknown. Synthetic live model/API and grounded-answer tests passed. The configured local key was used for those calls and never printed; whether it is the same credential previously pasted into chat is unknown. Official DeepSeek direct-API aliases/rates are not treated as AI STAR routing/pricing evidence.

## 1. Decision Goals

Choose the smallest maintainable stack that can:

- serve approximately 120 authenticated students;
- restrict access to the exact college email domain, `iiti.ac.in`;
- store private per-student chat history;
- ingest a small collection of text-searchable PDFs with page provenance;
- retrieve relevant passages and produce cited, grounded answers;
- fit a free-tier or near-zero-cost pilot without pretending that free tiers provide guaranteed capacity.

## 2. Common Foundation for All Options

These choices remain the same because they match the approved scope and avoid unnecessary services.

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Familiar to the user and supported by Streamlit Community Cloud. |
| Web UI and server | Streamlit | Fastest suitable route for the approved learning/production app; native chat, upload, session and LaTeX UI support. |
| Authentication | Streamlit native OIDC with Google Workspace: `st.login`, `st.user`, `st.logout` | Uses the college's existing Google identity rather than building password storage. Exact verified `iiti.ac.in` checks and an admin allowlist remain server-side. |
| PDF extraction | `pypdf` | Small, permissively licensed Python dependency that supports page-by-page text extraction. Version 1 does not need OCR. |
| Database, file storage and vector search | Supabase Free: PostgreSQL, private Storage and `pgvector` | One managed service can hold document metadata, private PDF objects, chunks, embeddings and chat history. PostgreSQL gives transactions for safe re-indexing and deletion. |
| Database access | `supabase-py` plus SQL functions for vector search | Reuses one supported client instead of adding an ORM and a separate vector database. |
| Testing | `pytest`; Streamlit AppTest for UI logic; Playwright only for deployed critical flows | Small unit/integration tests first, with real-browser tests only where authentication and deployment require them. |
| Deployment | Streamlit Community Cloud plus Supabase | Lowest-operations pilot path. The app will disclose 12-hour hibernation, variable limits and no uptime guarantee. |

### Security boundary

The browser talks only to the Streamlit app. Database and AI credentials stay server-side. The app derives a stable internal user identifier from the verified OIDC identity, enforces per-user history access on every server operation, and never sends names, email addresses or identity tokens to the AI provider. Private PDFs are never exposed through public Storage URLs.

Supabase RLS remains defense in depth, but Streamlit OIDC is separate from Supabase Auth. G4 must therefore choose either database access with short-lived user-scoped claims or a server-only database role with mandatory application authorization; it must not claim that Supabase `auth.uid()` automatically represents a Streamlit user.

## 3. AI Provider Options

The AI provider is the only material stack fork. Each option uses retrieved excerpts only—never web search or whole books at question time.

### Option A — Paid Gemini API

**Approved for V1.2:** `gemini-embedding-2` at 768 dimensions for document and query embeddings. A Gemini answer model is not selected.

| Criterion | Assessment |
|---|---|
| Learning and development | One official Python SDK for embeddings with explicit retrieval-oriented instructions. |
| Cost | Streamlit and Supabase can begin free. AI usage is metered, but current paid rates are low enough for a small pilot; set a hard project budget and usage alerts before students join. |
| Data treatment | Google's pricing page says paid-tier content is not used to improve its products. |
| Retrieval quality | Managed embeddings avoid loading a local model into Streamlit's limited memory. A 768-dimension vector keeps Supabase storage smaller, but quality must pass the approved 40-question evaluation. |
| Performance | External calls add latency, but the lightweight app server and managed vector search are a better fit than local models under Community Cloud limits. |
| Main risks | Requires a billing account/prepayment; quotas and model availability can change; course excerpts and questions leave the application boundary. |

**Why selected for retrieval:** It keeps vector generation managed, supports the approved 768 dimensions and avoids a local embedding model competing with Streamlit's limited memory.

### Selected V1.3 generation model; integration approved with open risks

The user approved AI STAR at `https://ai.starimg.ru/v1` with model `deepseek-v4-flash`. User-reported chat-completion/JSON support passed a synthetic live test: HTTP 200, response model `DeepSeek-V4-Flash-0731`, valid JSON. A live grounded answer also passed and cited PDF page 25. Initial usage reported 49 prompt, 61 completion and 169 total tokens; billing reconciliation is unknown. The user reports a `×0.1` balance multiplier and stop-at-zero. Dollar pricing and remaining balance are unknown. No storage/retention terms were found; the user explicitly accepts question/excerpt transmission despite that uncertainty. The reported no-training policy remains unverified. The configured local key was used and never printed; whether it matches the earlier chat-pasted key is unknown.

Retrieval remains on Gemini and generation uses a separate direct client. This is a narrow two-provider design, not a generic provider abstraction, model router or LangChain integration.

### Option B — Gemini API Free Tier (strict zero-cash pilot)

**Models proposed:** the same Gemini generation and embedding family, subject to the account's active free-tier availability.

| Criterion | Assessment |
|---|---|
| Learning and development | Same simple implementation as Option A. |
| Cost | No AI token charge within current free limits. |
| Data treatment | Google's current pricing page says free-tier content is used to improve its products. This needs explicit institutional approval beyond general permission to use third-party AI. |
| Reliability | Rate limits are account/project-specific and can change. The app must show quota errors and cannot promise class-wide availability. |
| Main risks | Data-use terms, lower/variable capacity and no production guarantee. |

**Decision rule:** Do not select this for real students unless the college explicitly accepts the provider's free-tier data treatment. It is acceptable for synthetic-data development and a private demo.

### Option C — Paid OpenAI API

**Models proposed:** `gpt-6-luna` for answers and `text-embedding-3-small` for retrieval.

| Criterion | Assessment |
|---|---|
| Learning and development | Mature Python SDK and documented embeddings; still only one AI provider. |
| Cost | No assumed free tier. Current low-cost model and embedding rates should be inexpensive at pilot volume, but actual usage must be budget-capped and measured. |
| Data treatment | OpenAI states API data is not used to train models by default unless the customer opts in; default abuse-monitoring retention can be up to 30 days. |
| Retrieval quality | The embedding model is documented for retrieval and has a 1,536-dimension default, using roughly twice the vector storage of the proposed Gemini configuration. |
| Main risks | Requires paid API access; model quality and cost need corpus-based comparison; provider retention controls may require account eligibility for stricter settings. |

**When to choose:** Prefer this if its data terms/account controls are more acceptable to the college or if it materially beats Option A on the 40-question grounding evaluation.

## 4. Comparison

| Concern | A: Paid Gemini | B: Free Gemini | C: Paid OpenAI |
|---|---:|---:|---:|
| Up-front infrastructure cost | Near zero | Zero | Near zero |
| Ongoing AI cost | Low, metered | Free within quotas | Low, metered |
| Provider says content is not used for model improvement by default | Yes | No | Yes |
| Expected implementation effort | Lowest | Lowest | Low |
| Suitable for real-student pilot | Recommended, after policy review | Only with explicit institutional data-use approval | Yes, after policy review |
| Capacity guarantee | No | No | No |
| Must pass project evaluation set | Yes | Yes | Yes |

No provider is approved merely because it has a strong general model. The selected option must meet the PRD's citation support, refusal and formula-fidelity thresholds on the actual course corpus.

## 5. Rejected Alternatives

- **Local FAISS/Chroma as the production store:** Streamlit Community Cloud's local filesystem is not an appropriate durable source of truth for admin uploads, deletion and re-indexing.
- **A separate managed vector database:** duplicates Supabase capabilities and adds credentials, quotas and failure modes for a small single-course corpus.
- **LangChain or LlamaIndex in Version 1:** direct provider calls, `pypdf`, and one SQL retrieval function cover the required flow with less framework coupling. Reconsider only if the implementation proves that needed retrieval/evaluation behavior would otherwise be duplicated.
- **Self-hosted generation models:** Community Cloud resources and the 120-student target make this a poor reliability and latency trade-off.
- **Custom email/password accounts:** adds password and email-verification risk when the college already has an identity provider.

## 6. Recommendation and Approval Choices

Current approved selection:

1. Common foundation above.
2. Paid `gemini-embedding-2` at 768 dimensions for V1.2 retrieval.
3. Google Workspace OIDC with an exact verified-email check for `iiti.ac.in`.
4. Direct SDK calls with no LangChain or provider-switching framework.
5. AI STAR `deepseek-v4-flash` is approved for V1.3 generation; live routing/JSON compatibility is pending a bounded smoke test. Unknown retention is explicitly accepted by the user and remains a documented privacy risk.

The user reports a purchased third-party generation balance of 10 million tokens, 0.1 balance-token deduction per model token, and blocking at zero. These are not independently verified; dollar pricing, remaining balance and expiry/reset behavior remain unknown. This balance does not apply to Google embeddings. Keys must never be placed in planning files, source control, logs or tests.

The user may instead choose Option B or C. Choosing B requires a separate explicit acceptance of the free-tier data-use terms. Choosing C replaces only the AI SDK/models; it does not justify a generic multi-provider abstraction in Version 1.

## 7. Decisions Deferred to G4

- Component boundaries and file layout.
- Database schema, authorization enforcement and deletion transactions.
- Page-aware chunking, retrieval SQL, citation assembly and refusal checks.
- Chat-retention period and cleanup job.
- Student/admin navigation, states and accessibility details.
- Exact upload limit after measuring the real PDFs.
- Recovery behavior for partial ingestion, quota failures and sleeping services.

## 8. Sources Checked on 2026-10-09

- [Streamlit native OIDC authentication](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Streamlit Community Cloud resource limits and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- [Supabase billing and Free quotas](https://supabase.com/docs/guides/platform/billing-on-supabase)
- [Supabase database size](https://supabase.com/docs/guides/platform/database-size)
- [Supabase vector columns](https://supabase.com/docs/guides/ai/vector-columns)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Gemini API pricing and data-use distinction](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
- [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)

## 9. Version 2 Stack Decision — Adaptive Quiz

**Status:** APPROVED — user selected Option C on 2026-10-10
**Date:** 2026-10-10

### 9.1 Unchanged Foundation

Version 2 keeps Streamlit, Google Workspace OIDC, `pypdf`, Supabase/PostgreSQL/pgvector, `gemini-embedding-2`, AI STAR `deepseek-v4-flash`, pytest and Streamlit Community Cloud. Mastery and attempt summaries remain normal Supabase application data regardless of the orchestration option.

### 9.2 Option A — Direct Bounded Workflow

Add a focused quiz module that calls the existing embedding/retrieval functions, sends one JSON-schema prompt through the existing AI STAR client, validates the seven-question payload, grades locally and updates Supabase transactionally.

| Criterion | Assessment |
|---|---|
| Existing-code fit | Highest; directly reuses retrieval, provider calls, JSON repair, citation mapping, rate limiting and safe errors. |
| New dependencies | None. |
| Reliability | Explicit application-controlled steps; no model-selected tools or agent loop. |
| Persistence | Supabase is the only durable state; Streamlit session holds the active quiz/results. |
| Provider compatibility | Already proven against the configured AI STAR endpoint. |
| Maintenance | Smallest change and fewest upgrade surfaces. |
| Learning value | Demonstrates RAG, structured generation, deterministic grading, adaptation and transactional state without an agent-framework label. |

### 9.3 Option B — LangChain Structured Generation

Keep the application workflow explicit but use LangChain model wrappers and structured output for quiz generation and retry behavior. Existing Supabase retrieval and mastery storage stay unchanged.

| Criterion | Assessment |
|---|---|
| Existing-code fit | Moderate; replaces the working direct AI STAR client only for quiz generation or requires two provider paths. |
| New dependencies | LangChain core plus a compatible chat-model integration package. |
| Reliability | Schema support is useful, but project-specific citation, duplicate, option and exact-count checks are still required. |
| Persistence | Unchanged Supabase tables; LangChain memory is unnecessary. |
| Provider compatibility | Must verify the AI STAR OpenAI-compatible endpoint through the chosen LangChain adapter. |
| Maintenance | More framework/version coupling for limited reduction in local validation code. |
| Learning value | Adds recognizable LangChain experience without a state graph. |

### 9.4 Option C — LangChain and LangGraph Workflow

Model quiz creation as graph nodes such as load mastery, retrieve evidence, generate, validate/repair and return quiz. Submission and persistence remain deterministic application/database operations rather than model tools.

| Criterion | Assessment |
|---|---|
| Existing-code fit | Lowest; the workflow is short and already maps cleanly to ordinary functions. |
| New dependencies | LangChain, LangGraph, provider integration and their transitive packages. |
| Reliability | Graph edges make transitions visible, but do not replace validation, authorization, transactions or idempotency. |
| Persistence | A graph checkpointer would duplicate state already held by Streamlit/Supabase; it should be omitted for this scope. |
| Provider compatibility | Requires the same AI STAR adapter verification as Option B. |
| Maintenance | Largest API and dependency surface. |
| Learning value | Strongest agent-framework portfolio signal and leaves a path to later tool-based tutoring workflows. |

### 9.5 Comparison

| Concern | A: Direct | B: LangChain | C: LangChain + LangGraph |
|---|---:|---:|---:|
| New production dependencies | None | Medium | Highest |
| Reuse of proven AI STAR code | Full | Partial | Partial |
| Project-specific validation still required | Yes | Yes | Yes |
| Durable state duplicated | No | No | Potentially, unless checkpointer is omitted |
| Agent/tool autonomy | None | Optional and unnecessary | Available but deliberately constrained |
| Expected implementation effort | Lowest | Medium | Highest |
| Best fit for current seven-question workflow | **Yes** | Acceptable | More machinery than required |

### 9.6 Recommendation

Select **Option A: Direct Bounded Workflow**. The approved feature has no open-ended planning or tool-selection problem: the server always loads mastery, retrieves evidence, generates one validated set and returns it. Supabase already provides long-term state. Adding LangChain or LangGraph would not remove the security-sensitive validation, authorization, idempotency or transaction code.

The product may still call the feature “Adaptive Quiz.” Internally describing it as an autonomous agent would overstate its behavior. LangChain/LangGraph should be reconsidered only when a later approved feature needs dynamic tool choice, pausable multi-step execution or several specialist workflows.

If the user's primary objective is specifically to demonstrate an agent framework in a portfolio, choose Option C with no checkpointer and no model authority over database writes. That choice knowingly prioritizes framework-learning value over the smallest production design.

### 9.7 Sources

- [LangChain: Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain: Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

### 9.8 Approved Selection

The user selected **Option C — LangChain and LangGraph Workflow** by replying “c” on 2026-10-10.

Implementation constraints carried into G4:

- Use `langchain-openai` `ChatOpenAI` with the approved AI STAR custom base URL and model only after a bounded compatibility check.
- Prefer JSON mode plus local schema/domain validation because AI STAR compatibility with provider-native JSON Schema is not established.
- Use a deterministic LangGraph state graph; the model does not choose arbitrary tools or transitions.
- Do not add a LangGraph checkpointer or store. Supabase remains the only durable source of truth.
- Keep grading, authorization, idempotency and database writes outside model control.
