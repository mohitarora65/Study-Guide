# Ingestion Repair Phase

**Status:** PARTIAL — root cause verified; production blocked by Gemini quota  
**Date:** 2026-10-12  
**Outcome:** Restore reliable PDF indexing when production currently stops before storing chunks.

## Verified diagnosis

- The failed production document is marked `EMBEDDING_FAILED`.
- Its failed version contains zero stored chunks and its ingestion run records zero processed pages/chunks.
- The existing ready document still contains 81 chunks for 80 pages using `gemini-embedding-2` with 768 dimensions.
- Local code creates text chunks before embedding, then embeds, inserts chunks, and activates the version. The failed run therefore stopped during embedding, before chunk insertion or activation.
- Google currently documents `gemini-embedding-2` and the existing `output_dimensionality` request field, so the configured model name and request shape are not presently obsolete.

The application intentionally persists only an operator-safe error code. The underlying provider response is therefore unavailable from current database metadata.

## Proposed bounded work

1. With separate explicit permission, send one short synthetic text to the configured Gemini embedding model and record only success/failure, status/error class, vector length, and latency. Do not send course material or student data.
2. Based on that evidence, make the smallest local correction in the existing ingestion/provider boundary. Do not change the database schema, embedding dimension, provider, dependency set, or product behavior unless separately approved.
3. Add one focused regression test for the verified failure and run the ingestion tests, full test suite, compilation, dependency check, and diff check.
4. Record the result and any remaining production action in `PROGRESS.md`.

## Permissions and risks

- The synthetic provider request may consume a small amount of Gemini quota or incur an unknown small charge; it requires explicit approval.
- Retrying the real failed document would call Gemini, write chunks, and modify production state; it is not included without separate explicit approval after the local fix is verified.
- No Git mutation will be performed.

## Exit evidence

- The provider failure is identified rather than guessed.
- A focused regression test demonstrates the local fix.
- Existing tests remain green.
- Any real-document retry is reported separately as authorized, completed, or not run.

## 2026-10-12 result

- The one approved synthetic request failed locally in 0.03 seconds with a plain `RuntimeError` before an HTTP status existed. It did not establish a Gemini quota, authentication, model, or rate-limit failure.
- Offline request construction succeeds with the installed SDK. The configured model and request shape remain supported, and the same unchanged ingestion code previously produced the healthy 81-chunk document.
- No evidence supports changing the splitter, database schema, model, batch size, or dependencies. A speculative code change was therefore not made.
- Focused verification passed: 19 ingestion tests, compilation, dependency consistency, and diff check.
- The remaining evidence-backed recovery is the existing failed-document retry. It will download the private PDF, call Gemini for its chunks, and write/activate production records, so it requires separate explicit approval.

## Approved production retry

- The user replied `approve` and authorized retrying the single `EMBEDDING_FAILED` production document.
- The retry loaded and extracted the private PDF, then Gemini returned HTTP 429 `RESOURCE_EXHAUSTED`: the configured Google project exceeded its current quota.
- Failure handling returned the document, version, and run to `failed`; postflight verified zero stored chunks, zero processed pages/chunks, and no active version. No partial index became searchable.
- PDF extraction emitted missing-`fontTools` and high Form XObject warnings, but reached the embedding stage; they are not the verified cause of this failure. No dependency was installed.
- The local application change preserves exhausted quota as the operator-safe code `EMBEDDING_QUOTA_EXCEEDED` and displays guidance to retry after quota resets or is increased. Provider details and credentials remain hidden. It is not deployed.
- Verification passed: 20 focused ingestion tests, 133 full tests, compilation, dependency consistency, and diff check.
- Restoring/increasing Gemini quota or changing billing is an account-level HIGH effect and was not performed. The failed document cannot be indexed until quota is available, after which it must be retried again.
