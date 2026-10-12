# Answer Model Fallback Phase

**Status:** LOCAL PASS / USER_REVIEW_PENDING  
**Date:** 2026-10-12  
**Outcome:** Keep Study answers available when the primary AI STAR model is temporarily busy, without changing retrieval or embeddings.

## Scope

- Keep `deepseek-v4-flash` as the primary Study answer model.
- Add `deepseek-v4.1-flash` as a single fallback attempt for transient provider failures only: network/timeout errors, HTTP 429, and HTTP 5xx.
- Do not fall back for authentication/permission failures, invalid requests, malformed model output, grounded-answer validation failures, refusals, or the app's local concurrency limit.
- Preserve the current prompt, JSON contract, grounded citations, output validation, timeout, rate limit, and user-facing safe errors.
- Add focused tests for model order, eligible and ineligible failures, bounded attempts, and secret-safe errors.
- Update the README and phase record.

## Acceptance evidence

- A successful primary request makes no fallback request.
- A transient primary failure attempts `deepseek-v4.1-flash` exactly once.
- HTTP 4xx errors other than 429 do not use the fallback.
- If both models fail, the user receives the existing safe error without provider payloads or credentials.
- Existing answer-generation and full local test suites pass, together with compilation, dependency consistency, and diff checks.

## Impact and exclusions

- Worst case for one generation pass rises from one provider request to two. The existing one-time output-repair pass remains separate, so an invalid successful response may still trigger its current repair request.
- The current website quiz flow uses the reviewed local question bank; the unused live quiz-generation adapter is not changed in this phase.
- `gemini-embedding-2`, chunking, retrieval, database/storage, schemas, dependencies, secrets, deployment, and Git are unchanged.
- The provider catalog read confirmed both `deepseek-v4-flash` and `deepseek-v4.1-flash` on 2026-10-12. No paid chat-generation call is included; live busy-state behavior remains unverified until separately authorized or naturally observed.

## Files

- `study_guide/answering.py`
- `tests/test_answering.py`
- `README.md`
- `PROGRESS.md`

## Risk control

Retry eligibility will be explicit and narrow. There will be no generic retry loop, dependency, provider abstraction, or model configuration surface.

## Result

- Added `deepseek-v4.1-flash` as one transient-only fallback in the shared Study answer adapter; the primary remains `deepseek-v4-flash`.
- Timeout/network, HTTP 429 and HTTP 5xx failures are eligible. Authentication/other HTTP 4xx and malformed responses fail safely without switching models.
- The prompt, response contract, validation, output repair, concurrency/rate limits, timeout, retrieval and embedding behavior are unchanged.
- Updated focused regression coverage and operator documentation.
- Verification: 20 focused answer tests and 140 full tests passed; compilation, `pip check`, and `git diff --check` passed.
- Not performed: paid chat-generation call, production deployment, embedding request/change, database write, dependency installation, or Git mutation.
