# Architecture — Grounded Mathematics Study Guide

**Status:** APPROVED — user replied “yes” on 2026-10-09  
**Date:** 2026-10-09  

**Approved clarification, 2026-10-09:** V1.2 uses Google `gemini-embedding-2` at 768 dimensions. DeepSeek V4 Flash is a proposed V1.3 answer model only; no third-party generation integration is approved yet.

## 1. Architecture Goal

Build one small server-rendered Streamlit application that authenticates IIT Indore students, manages one approved PDF collection, retrieves page-aware evidence, and returns validated cited answers. Keep authorization, document state and citation provenance explicit; avoid agents, web tools and framework orchestration.

## 2. System Context

```text
Student/Admin browser
        |
        | HTTPS
        v
Streamlit application  <---->  Google Workspace OIDC
        |
        +----> Supabase PostgreSQL + pgvector
        |
        +----> Supabase private object storage
        |
        +----> Paid Gemini API (embeddings, V1.2)
        |
        +----> DeepSeek V4 Flash answer model (user-selected for V1.3; gateway integration not approved)
```

The browser never receives database service credentials, provider keys, raw embeddings or private Storage URLs. Streamlit is the only application backend.

## 3. Trust Boundaries and Identity

| Boundary | Trust decision |
|---|---|
| Google to Streamlit | Accept only a valid OIDC session with a verified email claim exactly ending in `@iiti.ac.in`. A substring match is forbidden. |
| Student versus admin | Admin access requires both an allowed domain and an exact email in a server-side secret allowlist. No UI value grants a role. |
| Browser to Streamlit | Treat every question, thread identifier, filename and action as untrusted. Re-check authorization server-side on every protected operation. |
| Streamlit to Supabase | Use server-held credentials. Public/anonymous database and Storage access is denied. Student ownership is enforced in application queries because Streamlit OIDC is not Supabase Auth. |
| PDF chunks/questions to Gemini embeddings | Treat text as data, never instructions. Send no name, email, identity token, secret, object path, whole unrelated document or chat history. |
| Retrieved evidence/questions to a future answer provider | Not active in V1.2. Any V1.3 integration must send only bounded retrieved excerpts and pass a separate pricing, privacy and compatibility approval. |

A stable internal `user_key` is derived from the OIDC issuer and subject using a keyed hash. Chat rows store that opaque key, not the student's email. The current verified email is used only for the domain check and admin allowlist.

## 4. Application Components

The implementation should remain a small set of modules with one responsibility each:

- **App/navigation:** login boundary and routing between student chat and admin documents.
- **Identity/authorization:** OIDC claim validation, exact-domain check, internal user key and admin allowlist.
- **Persistence:** narrow Supabase operations for documents, chunks, threads and messages.
- **Ingestion:** PDF validation, page extraction, chunking, embeddings and index-state transitions.
- **Retrieval:** query embedding and similarity search over ready document versions only.
- **Answering:** evidence threshold, bounded approved-generation-provider request, structured chunk citations and validation; not implemented or provider-approved in V1.2.
- **Views:** student chat/history and admin document management.

Do not add repository/service classes, dependency injection, event buses or generic provider adapters unless a later approved requirement makes them necessary.

## 5. Data Model

| Record | Minimum fields |
|---|---|
| `documents` | ID, display name, object path, content hash, status, active version, timestamps and safe error code/message. |
| `document_versions` | ID, document ID, version number, status, page count, embedding model/dimension and timestamps. |
| `chunks` | ID, version ID, page number, chunk order, text, embedding and content hash. |
| `threads` | ID, owner `user_key`, title and timestamps. |
| `messages` | ID, thread ID, role, text, refusal flag, citations JSON and timestamp. |
| `ingestion_runs` | ID, document/version, status, counts, retry key, safe error and timestamps. |

Only `ready` active versions participate in retrieval. Citations stored with an answer contain immutable document/version/chunk IDs plus the displayed document name and PDF page number at answer time.

## 6. Document Ingestion Flow

1. Re-check the admin role.
2. Validate the configured size limit, `.pdf` extension, PDF signature and parser readability before indexing.
3. Hash the bytes to detect accidental duplicate uploads and give the object a generated path; never trust the uploaded filename as a path.
4. Store the PDF privately and create a `processing` document version.
5. Extract text page by page with `pypdf`. Record empty or low-text pages as warnings.
6. Split within page boundaries so a chunk never produces an ambiguous page citation. Chunk size and overlap are calibrated on the actual books.
7. Embed batches with the approved paid API and store chunks with page metadata.
8. In one database transaction, mark the new version `ready` and make it active. A failed replacement leaves the old ready version active.
9. On failure, mark the run failed, hide partial chunks from retrieval and present a safe retryable error.

Retry uses an idempotency key for the document hash/version so it cannot create duplicate active chunks.

## 7. Question and Answer Flow

1. Re-check login/domain, thread ownership, question length and per-user request limits.
2. Create a query embedding and retrieve a small number of high-scoring chunks from active ready versions.
3. If no result crosses the calibrated support threshold, return the fixed insufficient-material response without calling the answer model.
4. Send only the question, bounded conversation context and retrieved excerpts. Each excerpt receives an application-generated chunk ID.
5. Require structured output containing answer text and cited chunk IDs; the model never supplies filenames or page numbers.
6. Reject any citation ID outside the retrieved set. Map valid IDs to stored document/page metadata.
7. If the response has missing/invalid citations or violates the grounded-output contract, make at most one bounded repair attempt; otherwise refuse safely.
8. Store the question, answer/refusal and validated citations under the authenticated user's thread.

The model has no web, file, database or action tools. Citation support and formula accuracy are measured through the approved evaluation set; the architecture does not claim that structural validation proves factual grounding.

## 8. Deletion and Retention

- A student may delete any owned thread immediately; ownership is checked in the delete query.
- Proposed automatic chat retention is **90 days from the last thread activity**, followed by permanent deletion. This is part of G4 approval and can be revised by the user.
- Document deletion first marks the document unavailable to retrieval, then removes derived rows and the private object. If object deletion fails, the document stays unavailable and cleanup is retried.
- Logs exclude full questions, answers, PDF text, email addresses, tokens and secrets. Operational logs keep request IDs, timings, counts and safe error codes.

## 9. Failure and Recovery Rules

| Failure | Behavior |
|---|---|
| OIDC failure or wrong domain | Deny access; do not reveal protected content. |
| Sleeping Streamlit/Supabase service | Show a truthful wake/retry message; never report an answer as pending if no durable job exists. |
| PDF parse or embedding failure | Keep the version non-searchable, preserve the prior ready version and allow admin retry. |
| Weak retrieval | Return the standard insufficient-material response. |
| Gemini embedding timeout/quota/error | Bounded retry only for transient failures, then a clear non-fabricated error. |
| Future answer-provider timeout/quota/error | V1.3 must define bounded behavior after that integration is approved. |
| Invalid model citations/output | One repair attempt at most, then refuse. |
| Database write failure after generation | Tell the user the answer could not be saved; do not claim it is in history. |
| Deletion cleanup failure | Keep content unavailable, record cleanup state and retry without restoring search access. |

## 10. Capacity and Cost Controls

- Cap question length, retrieved excerpts, conversation context and generated output.
- Batch embeddings during admin ingestion; never recompute document embeddings per question.
- Use a 768-dimension Gemini embedding unless corpus evaluation shows it is inadequate.
- Apply per-user throttling and a global concurrency guard; exact limits are calibrated before the pilot.
- Configure provider budget alerts/hard limits where supported and display quota failure cleanly.
- Measure cold start, typical latency, memory and a small concurrent-load sample before release. No claim is made that free hosting supports 120 simultaneous questions.

The reported 10-million-token allowance belongs to the separate third-party generation service, not Google embeddings. It is not treated as verified capacity until that provider's pricing, model routing, privacy terms and reset/expiry rules are checked during an approved V1.3 phase.

## 11. Security Verification Required Before Pilot

- Wrong-domain, unauthenticated and non-admin access tests.
- Cross-student thread read/update/delete tests.
- Malicious thread/document IDs and filenames.
- Prompt-injection text inside both a PDF and a question.
- Secret and personal-data checks in browser errors and logs.
- Citation IDs that are missing, duplicated or not retrieved.
- Failed replacement ingestion and failed document deletion cleanup.
- Quota, timeout and database/storage outage behavior.

## 12. Deliberate Limits

- One course and one collection.
- One fixed embedding provider in V1.2. V1.3 may add one fixed answer provider only after approval; no generic provider switching layer.
- No background worker service in Version 1. Admin ingestion may run synchronously with visible progress if it fits measured limits.
- No OCR, agents, web search, autonomous tools or analytics dashboard.
- No LangChain/LangGraph unless an approved later requirement introduces orchestration that direct calls cannot express clearly.
