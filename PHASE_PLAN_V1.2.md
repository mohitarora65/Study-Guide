# Phase Plan — V1.2 Admin PDF Ingestion and Retrieval Store

**Status:** COMPLETE — user approved on 2026-10-09  
**Version:** 1  
**Date:** 2026-10-09  
**Dependency:** V1.1 approved and complete

## 1. User-Visible Result

An authenticated admin can upload one approved PDF, see its processing/ready/failed state, retry or re-index safely, and delete it with confirmation. A ready document has page-bounded 768-dimensional embeddings in Supabase, and a server-side retrieval function returns matching chunks with immutable document and PDF-page metadata.

Ingestion remains synchronous and one-file-at-a-time. There is no background worker, batch uploader, OCR, student upload, chat answer generation, LangChain or deployment in this phase.

## 2. Evidence and Provisional Limits

The supplied `pdfs/lA notes.pdf` was inspected read-only:

- 626,231 bytes (612 KB), 80 unencrypted pages;
- text extracted from all 80 pages with Poppler;
- median 612 non-whitespace characters per page, minimum 121, maximum 2,224;
- no page fell below the proposed low-text threshold of 100 non-whitespace characters;
- sampled title, formula-heavy and final pages rendered legibly.

Larger books are expected later, so these limits are intentionally provisional:

- application and private-bucket hard cap: **25 MiB per PDF**;
- one file per submission;
- low-text warning: fewer than **100 non-whitespace extracted characters** on a page;
- initial page-bounded chunk target: **1,800 characters with up to 250 characters of within-page overlap**;
- embedding dimension: **768**, matching the approved database column;
- embedding model: **`gemini-embedding-2`**, pinned in each document version; changing models requires re-embedding because embedding spaces are incompatible.

Supabase Free currently permits a bucket limit up to 50 MB, while standard uploads above 6 MB are less reliable than resumable uploads. V1.2 will use the existing Python client's standard private upload and measure it with available samples. The 25 MiB cap must be revalidated when the larger books arrive; a resumable-upload implementation is not silently added.

## 3. In Scope

- Extend secret-safe configuration with an existing paid Gemini API key.
- Add `pypdf` and the official `google-genai` SDK only.
- Validate one upload at the trust boundary:
  - non-empty bytes;
  - `.pdf` display suffix;
  - `application/pdf` when a MIME value is supplied;
  - `%PDF-` signature;
  - 25 MiB maximum;
  - readable, unencrypted PDF with at least one page.
- Hash file bytes with SHA-256 for duplicate detection and generate private object paths from server-created identifiers, never the uploaded filename.
- Create/configure one private Supabase Storage bucket named `course-pdfs`, restricted to PDFs and 25 MiB.
- Extract text page by page with `pypdf`, retaining 1-based PDF page numbers and low-text-page warnings.
- Split text only within a page boundary; chunks never span pages.
- Batch direct Gemini embedding calls at 768 dimensions with bounded retry only for transient failures. Send chunk text and retrieval instructions only—never identity, tokens, object paths or whole unrelated documents.
- Persist partial work under a non-active version, then activate the complete version through one PostgreSQL transaction.
- Preserve the previous ready version when replacement/re-indexing fails.
- Make duplicate upload and failed-run retry idempotent; never create duplicate active chunks.
- Add server-only vector retrieval over active ready versions, returning stored document/version/chunk/page metadata.
- Delete safely: first make the document unavailable to retrieval, then remove its private object and derived rows; a cleanup failure stays unavailable and retryable.
- Replace the V1.1 database-check placeholder with the approved admin document interface and truthful status/error/warning states.
- Update tests, setup instructions and progress evidence.

## 4. Out of Scope

- OCR or image understanding for scanned pages.
- Multiple-file/batch upload, folders or drag-and-drop enhancements.
- Background workers, queues, scheduled ingestion or durable progress after the Streamlit process stops.
- Student upload or direct browser access to Supabase Storage.
- Answer generation, chat, citations shown to students, retrieval thresholds or conversation history behavior; those belong to V1.3.
- Automatic model selection, provider abstraction, LangChain or LlamaIndex.
- TUS/resumable upload unless a supplied larger book proves the standard path inadequate and the user approves the scope change.
- Deployment, public exposure, Git mutations, billing changes or production data migration.

## 5. Intended Files

| Path | Planned change |
|---|---|
| `app.py` | Admin-only upload/list/status/retry/re-index/delete UI; keep student route unchanged. |
| `study_guide/config.py` | Secret-safe Gemini key and fixed ingestion limits/model validation. |
| `study_guide/database.py` | Narrow Storage, document/version/run, activation, deletion and retrieval operations. |
| `study_guide/ingestion.py` | Upload validation, hashing, page extraction, page-bounded chunking, direct Gemini embeddings and orchestration. |
| `supabase/migrations/002_ingestion.sql` | Private bucket configuration, warning/measurement columns, transactional activation/deletion functions and active-version vector-search RPC. |
| `.streamlit/config.toml` | Match Streamlit's upload ceiling to 25 MiB. |
| `.streamlit/secrets.toml.example` | Add a placeholder-only Gemini API key section. |
| `requirements.txt` | Add pinned `pypdf==6.19.0` and `google-genai==2.29.0`. |
| `tests/test_ingestion.py` | Validation, extraction, warning, chunking, batching, retry and failure-state tests. |
| `tests/test_database.py` | Storage/database/RPC boundary tests with provider fakes. |
| `tests/test_config.py` | Gemini configuration and secret-safe failure tests. |
| `tests/test_schema.py` | Migration function, bucket restriction, active-version search and privilege assertions. |
| `tests/test_app.py` | Admin document-state UI checks without real credentials or paid calls. |
| `README.md` | Local Gemini setup, PDF limits, ingestion behavior and current limitations. |
| `PROGRESS.md` | Approval, actual execution evidence, remote writes and remaining risks. |

No generic repository layer, provider interface, worker framework or extra component library is planned. If implementation proves another file essential, it must be directly required and reported.

## 6. Data and Transaction Design

The additive migration will:

- record file byte size, extracted character count and low-text PDF page numbers;
- ensure the `course-pdfs` bucket is private with PDF MIME and 25 MiB restrictions;
- add a transaction that verifies version ownership/model/dimension, marks the completed version ready and switches `documents.active_version_id` atomically;
- add a transaction that clears search availability before object cleanup begins;
- add a vector-search function that joins only `documents.status = 'ready'` and the exact active ready version;
- revoke function access from `anon` and `authenticated`, granting execution only to `service_role`.

Storage and PostgreSQL cannot share one transaction. The application therefore records explicit states and performs compensating cleanup. A failed cleanup never makes a deleting or failed document searchable again.

## 7. Implementation Approach

1. Inspect installed APIs and current schema; do not alter Git.
2. Add and test pure validation, extraction and page-bounded chunking first.
3. Add the direct Gemini embedding boundary with a small batch size, 768 dimensions, explicit retrieval instructions and bounded transient retry.
4. Add the additive migration and static assertions.
5. After confirming the same development project, apply migration `002_ingestion.sql` and create/configure the private bucket.
6. Implement persistence/orchestration using the existing Supabase client; keep old active versions visible until atomic activation.
7. Implement the Streamlit admin states and destructive-action confirmation.
8. Run unit/AppTest/schema tests, then live development integration with the supplied notes.
9. Verify retrieval metadata, retry/idempotency and deletion using generated test content; fix and rerun until passing or honestly blocked.
10. Update README and `PROGRESS.md`, then stop for V1.2 review/sign-off.

## 8. Acceptance and Test Evidence

Automated checks must prove:

- non-PDF suffix, MIME, signature, oversized, encrypted, corrupt, empty and zero-page inputs fail safely;
- provider/parser details do not leak through browser-visible errors;
- every chunk has a real 1-based PDF page and no chunk crosses a page boundary;
- empty/low-text pages warn without pretending OCR occurred;
- duplicate upload/retry does not create duplicate active chunks;
- a failed replacement leaves the prior ready version active;
- only a completely embedded version can become active;
- delete makes content unavailable before cleanup and remains idempotent after partial failure;
- search SQL filters to active ready versions and returns stored provenance;
- Gemini calls use the fixed model/dimension and exclude identity/secrets;
- students cannot reach or trigger admin ingestion controls.

Live development evidence will use project `kjxixskoeihbitcohhuo` and must show:

- the private bucket rejects public access;
- `lA notes.pdf` uploads and becomes ready;
- page count is 80 and sampled stored chunks map to their real PDF page numbers;
- a bounded Gemini embedding request returns exactly 768 values per chunk;
- a known Linear Algebra query retrieves a relevant chunk with stored document/page metadata;
- the in-app admin list/status/retry flow works;
- a generated temporary test PDF can be deleted and is no longer retrievable;
- actual chunk count, embedding storage estimate, ingestion time and provider usage metadata are recorded.

The later, larger books are not available now. Their upload reliability and final cap remain **NOT TESTED** until supplied; this does not justify claiming large-book readiness.

## 9. Permissions and External Effects Requested by Whole-Phase Approval

Approval authorizes all of the following for V1.2 only:

- install `pypdf==6.19.0` and `google-genai==2.29.0` into the existing project `.venv`;
- add the Gemini key placeholder to the example and read the user's locally configured key without printing it;
- make bounded paid Gemini embedding calls for the supplied notes and focused smoke tests, expected to remain far below one million input tokens;
- apply additive migration `002_ingestion.sql` to confirmed development project `kjxixskoeihbitcohhuo`;
- create/configure the private `course-pdfs` bucket there;
- upload `pdfs/lA notes.pdf` to that private development bucket for verification;
- create and delete temporary remote test documents/objects required for deletion checks.

Approval does **not** authorize deletion of the local PDF, deletion of non-test remote documents, deployment, public bucket access, provider billing/configuration changes, Git operations or work outside this phase. Unexpected material spend, a different target project, destructive non-test action or major architecture change requires a new decision.

## 10. Tools and Fallbacks

- **Ponytail Full:** smallest complete modules and dependency set; no orchestration framework.
- **Context7 and official docs:** current `google-genai`, Streamlit and Supabase APIs.
- **PDF skill / Poppler:** inspect real samples and verify page/text behavior; `pypdf` remains the application parser.
- **pytest / Streamlit AppTest:** primary automated evidence.
- **Browser automation:** live admin/OAuth/storage smoke test; use the existing Brave integration if Playwright CLI still lacks Chrome.
- **Serena:** skip unless the codebase becomes large enough to justify symbol tooling.

If live Gemini access is unavailable, finish provider-fake tests and report live embedding/retrieval as blocked; do not substitute another provider or fabricate vectors.

## 11. Model and Usage Forecast

- Recommended execution: GPT-6.1 Sol, medium reasoning; raise to high only for transaction/failure-path review.
- Actual selectable Codex model and remaining account usage are not exposed here and remain unverified.
- Estimated human-equivalent effort: 8–14 hours.
- Estimated chat/context sessions: 2–4.
- Estimated five-hour usage windows: 2–3.
- Paid application usage: bounded document embeddings for the sample and focused retries, expected below one million input tokens; actual provider usage metadata will be recorded.

## 12. Git Checkpoint After Sign-Off

Git remains user-controlled. After V1.2 passes and is accepted, suggest explicit user-run staging for changed application, migration, tests and documentation paths. Do not include `.streamlit/secrets.toml`. Do not suggest staging `pdfs/lA notes.pdf` unless the user separately chooses to version course material and confirms repository/licensing implications.

## 13. Approval Effect

Approval authorizes end-to-end execution of this complete phase, including the specific local dependencies, bounded paid embedding calls and development Supabase writes listed above. It does not approve V1.3, deployment, Git mutations, unbounded paid usage or unrelated external changes.

**Approval:** User replied “yes” on 2026-10-09, authorizing the whole phase as scoped above.

**Provider confirmation:** On 2026-10-09 the user explicitly approved Google `gemini-embedding-2` at 768 dimensions for V1.2. DeepSeek V4 Flash remains outside this phase and is only a proposed V1.3 answer model pending separate provider verification and approval.

**Phase sign-off:** User replied “approve v1.2” on 2026-10-09 after reviewing the execution report. V1.2 is complete; this does not approve V1.3 provider integration or deployment.

## 14. Sources Checked

- Google Gen AI Python SDK v2.14 documentation through Context7; PyPI currently reports `google-genai 2.29.0`.
- Google Gemini Embeddings documentation: `https://ai.google.dev/gemini-api/docs/embeddings`.
- Google Gemini API pricing: standard `gemini-embedding-2` text input is currently listed at $0.20 per million tokens; the supplied notes are expected to cost under one cent to index once, subject to actual provider token accounting.
- Supabase Python Storage/RPC documentation through Context7.
- Supabase Storage limits: `https://supabase.com/docs/guides/storage/uploads/file-limits`.
- Supabase standard-upload guidance: `https://supabase.com/docs/guides/storage/uploads/standard-uploads`.
- Streamlit file-upload configuration documentation through Context7.
- Local read-only inspection of `pdfs/lA notes.pdf`.
