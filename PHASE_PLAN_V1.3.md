# Phase Plan V1.3 — Grounded Student Assistant and Private History

**Status: COMPLETE — user signed off V1.3 on 2026-10-09.** This plan followed the approved V1.3 outcome in `ROADMAP.md`, the user-approved architecture in `ARCHITECTURE.md`, and the existing V1.2 implementation. No architecture or schema change was included.

## 1. Outcome and Boundaries

An authenticated student can ask a bounded question, receive an answer based only on active indexed course material with citations mapped to real document pages, receive the fixed insufficient-material response when evidence is weak, and revisit/delete only their own chat threads.

**In scope:** query embedding with the already approved Gemini Embedding 2 provider at 768 dimensions; active-ready Supabase pgvector retrieval; early refusal; a structured, citation-ID-only generation contract; citation validation and at most one bounded repair; LaTeX-capable Streamlit chat/history; private ownership checks and permanent thread deletion; bounded context/output, safe provider/database errors, per-user throttling/global concurrency guard; focused automated and development integration tests; README and progress updates.

**Out of scope:** changing the approved architecture or existing schema without a separately approved change; new provider abstractions/model switching; LangChain/LangGraph; OCR, web search, tools/agents, new courses, analytics, deployment, production data, Git operations, broad role/identity changes, or uploading/transmitting course PDFs to the generation provider.

## 2. Provider Approval, Reported Terms, and Remaining Verification

The user selected DeepSeek V4 Flash, confirmed `https://ai.starimg.ru/v1`, and explicitly approved the integration and sending student questions/retrieved course excerpts despite unknown retention. User-provided model listing shows `deepseek-v4-flash` and a 1.05M context figure. The user says it supports OpenAI-compatible chat completions and structured JSON output. The user reports that `×0.1` means each model token deducts 0.1 balance tokens and that requests stop when the balance reaches zero. A dollar-denominated rate, remaining balance, and expiration are unknown; no overage is reported. The user says the service does not use prompts for training, but no published policy was available to verify that claim. Storage duration, subprocessors, and processing region remain unknown; the user explicitly accepts that uncertainty.

The supplied Help Center text documents the generic `https://ai.starimg.ru/v1` base URL and warns that client configuration stores keys in plain text. The exact model listing and protocol/JSON support were user-confirmed, not independently attributable provider documentation. A synthetic live smoke test passed on 2026-10-09: HTTP 200, requested model `deepseek-v4-flash` resolved to response model `DeepSeek-V4-Flash-0731`, and JSON-object output parsed successfully. Provider usage fields reported 49 prompt, 61 completion, 169 total tokens; these figures do not reconcile and exact balance deduction remains unverified. A second live synthetic RAG answer passed through Gemini embedding, active Supabase pgvector retrieval, AI STAR generation, and local citation validation; the answer cited `lA notes.pdf`, PDF page 25. No email, identity token, ownership key, or saved chat was sent. Do not silently substitute another endpoint/model.

Additional read-only checks on 2026-10-09 found third-party marketplace listings for AI STAR token products. Those listings make broad seller claims about chat/data storage and confidentiality, but they are not attributable provider terms and do not specify retention duration, training use, subprocessors, processing region, DeepSeek-specific rates, or V4 Flash routing. They do not satisfy this gate and are not treated as verified privacy or pricing evidence.

## 3. Cost and Data Handling

- Gemini is used only to embed each submitted question; document embeddings are reused and never regenerated per question. At the previously verified standard text rate of $0.20 per million tokens, query embedding cost is very small, but the actual total depends on tokenization and usage metadata.
- For context only, DeepSeek's official direct API currently lists `deepseek-flash` at $0.15/M uncached input and $0.60/M output off-peak, and $0.30/M uncached input and $1.20/M output at peak; cached input is $0.003/M off-peak and $0.006/M peak. Prices vary and these are **not** the proposed gateway's prices or a forecast of its billing.
- The implementation sends only the current question, bounded recent conversation, and retrieved excerpts; it does not send email, identity tokens, or thread ownership identifiers. User explicitly accepts sending these to AI STAR although retention/storage terms are unknown.
- Add no credential to source or planning documents. The AI STAR key belongs only in local `[ai_star]` secrets / deployment secret storage, remains redacted in representations and logs, and is never requested in chat. The configured local key was used for the two approved synthetic calls; it was never printed or copied into project files. It was not compared with the value previously pasted into chat, so whether it is the same credential is unknown.
- Existing PRD says 90-day retention is proposed, but also says retention must be selected before architecture approval; V1.3 must not silently introduce automatic expiry. Preserve user-triggered deletion and surface this unresolved retention decision before implementation if it affects the approved scope.

## 4. Existing Contracts to Reuse

- `study_guide/ingestion.py`: existing Gemini embedding helper and validated 768-dimension vectors.
- `study_guide/database.py`: existing server-only Supabase client; add only minimal query/history/ownership operations if required.
- `supabase/migrations/002_ingestion.sql`: existing `match_chunks` RPC returns active-ready chunk content and metadata; reuse it rather than introduce a second vector search path.
- `supabase/migrations/001_initial.sql`: `threads` and `messages` already include ownership key, role, refusal flag, citation JSON, timestamps, and cascading deletion. No migration is planned unless read-only inspection proves the contract inadequate; any schema change needs explicit approval first.
- `app.py`, `study_guide/config.py`, and the existing Streamlit/auth patterns: reuse the current Study/Admin navigation and secret-safe configuration behavior.

## 5. Intended Files and Minimal Changes

| Path | Expected work if approved |
|---|---|
| `study_guide/answering.py` | Minimal bounded retrieval/generation orchestration, evidence refusal, output parsing, citation validation and safe errors. A direct single-provider client only after the provider gate and separate approval. |
| `study_guide/database.py` | Add narrow operations for owned threads/messages and existing active-vector RPC only where needed; enforce owner filters on every history read/delete. |
| `study_guide/config.py`, `.streamlit/secrets.toml.example` | Add only the approved generation credential/configuration after provider approval; never expose values. |
| `app.py` | Student chat, thread list/history, citations, refusal/error states, delete confirmation and bounded input. |
| `tests/` | Provider-fake/unit and AppTest coverage for citations, refusal, prompt injection, errors and cross-user isolation; no real paid calls in automated tests. |
| `README.md`, `PROGRESS.md` | Setup, privacy/provider caveats, phase evidence, actual cost/usage if exposed, and honest limitations. |

No generic provider interface, ORM, orchestration framework, extra schema, or new dependency is planned by default. Exact file list may be narrowed after reading affected callers during approved execution.

## 6. Acceptance Evidence

- Query embedding is finite and exactly 768 dimensions; only active ready chunks are retrieved.
- Weak/empty evidence returns the fixed refusal without an answer-generation request.
- Non-refusal responses cite only retrieved chunk IDs; filenames and page numbers come from database metadata, never model-generated text.
- Invalid/missing citation output gets at most one bounded repair; failure then refuses safely.
- Retrieved PDF instructions and user prompt injections are treated as untrusted content and cannot change system behavior or invoke tools.
- Every persisted/retrieved/deleted thread is owner-scoped; cross-user access attempts fail; deletion removes messages through the existing cascade.
- Input, context, output, per-user request rate and global in-flight generation are bounded; provider quota/timeouts and DB errors reveal no secrets or fabricated answers.
- Student chat/history/delete and Admin navigation remain functional in AppTest; provider calls are faked in automated tests.
- Development-only end-to-end evidence covers one supported answer with page citation, one early-refusal unit path, synthetic history reload and owner-only deletion. The supported answer was verified live on 2026-10-09; no chat record was written for that live query.

## 7. Execution and Authority

The user approved V1.3 execution, AI STAR integration, and a synthetic live compatibility test; separately approved chat-data reads/writes and synthetic integration checks in development project `kjxixskoeihbitcohhuo`. The user accepts question/excerpt transmission while retention remains unknown. This does not authorize schema migration, real student data tests, deployment, or Git mutations. The phase may not be reported complete until the synthetic provider smoke test and remaining acceptance checks pass.

During an approved phase, complete implementation, the acceptance checks above, appropriate tests/fixes and documentation end-to-end, then stop for user review and sign-off. User performs all Git operations.

## 8. Model and Effort Forecast

- Recommended Codex route: current available general coding model at medium reasoning for straightforward UI/wiring, high reasoning only for ownership/citation/security review. This session does not expose a selectable model name or remaining usage window, so those are **unknown**, not promised.
- Estimated human-equivalent effort: 10–18 hours; 3–5 context sessions; approximately 2–4 five-hour usage windows (low confidence before gateway due diligence).
- Use Ponytail Full: existing code and schema first, no LangChain, no broad provider abstraction, and focused testing. Context7 was checked for current Supabase RPC and Streamlit chat patterns. Serena is unnecessary for this small codebase.
- Token/cost figures for app providers must be measured when a provider is approved; do not spend tokens on repeated corpus embedding or exploratory paid prompts.

## 9. Approval Record

**Phase plan approval:** User said “let’s proceed” on 2026-10-09 after reviewing the plan. This authorizes V1.3 execution within this plan. User separately approved chat-data reads/writes and synthetic integration checks in development project `kjxixskoeihbitcohhuo` by replying “continue” on 2026-10-09. The gateway remains excluded pending its independent verification/approval gate below.

**Model choice and provider approval:** User selected `deepseek-v4-flash` and explicitly approved the AI STAR integration and data transmission despite unknown retention on 2026-10-09. Synthetic live routing/JSON and grounded-answer checks passed.

**Phase sign-off:** User explicitly replied “approve” on 2026-10-09 after the implementation and test summary. V1.3 is accepted as complete.

**Schema/architecture:** Existing approved schema and architecture remain unchanged by this plan.

## 10. Sources Checked

- Official DeepSeek model pricing and routing: https://api-docs.deepseek.com/quick_start/pricing/
- Official DeepSeek first-call/API compatibility guidance: https://api-docs.deepseek.com/quick_start/
- Official DeepSeek model update/retirement notice: https://api-docs.deepseek.com/updates/
- Gateway landing/help/news pages inspected read-only: https://ai.starimg.ru/, https://ai.starimg.ru/help, https://ai.starimg.ru/news
- User-provided rendered Help Center excerpt (2026-10-09): documents generic OpenAI-compatible setup, common base URL/key, client-side plain-text key storage warning; visible model family table lists DeepSeek V3, not the selected V4 Flash identifier. Pricing/privacy/retention not included.
- User-provided model listing/answers (2026-10-09): lists `deepseek-v4-flash` with 1.05M context; user confirms chat completions and JSON output, `×0.1` balance deduction, and requests stop at zero. These are user-reported, not independently attributable provider terms; live compatibility remains to be tested.
- Third-party marketplace seller listings checked read-only (2026-10-09): https://plati.market/itm/api-gemini-flash-3-7-3-6-3-5-pro-3-1-auto-delivery-1m-1b/6056762?lang=en-US and https://x-sale.sellerstore.ru/products/6056762. Claims are seller-authored, not attributable provider terms; they do not establish DeepSeek pricing, retention, or routing.
- Supabase Python RPC documentation, via Context7: https://github.com/supabase/supabase-py/blob/main/src/postgrest/docs/examples/basic_queries.rst
- Streamlit chat UI documentation, via Context7: https://docs.streamlit.io/develop/tutorials/llms/conversational-apps
- Gateway-specific dollar price and privacy/retention terms: **not found / not verified**. User accepts sending questions/excerpts despite unknown retention. The user confirms generic protocol/model support, and the synthetic live test verifies basic route/JSON behavior. Marketplace seller claims are insufficient evidence.
