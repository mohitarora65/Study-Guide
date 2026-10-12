# Voyage Embedding Migration Phase

**Status:** CUTOVER USER_APPROVED / WAITING FOR USER-ONLY RELEASE CHECKPOINT  
**Date:** 2026-10-12  
**Provider decision:** User selected hosted `voyage-4-lite`; native 1024-dimensional output will be used.

## Outcome

Replace Gemini embedding calls with Voyage for PDF indexing and Study queries while preserving page citations, atomic active-version changes, safe errors, and a rollback path.

## Local implementation scope

- Add one standard-library Voyage embeddings adapter for batched documents (`input_type=document`) and individual Study queries (`input_type=query`).
- Use `voyage-4-lite` with 1024-dimensional float vectors, bounded responses, a 30-second timeout, the existing one-retry transient policy for ingestion, and no hidden SDK retries.
- Replace `gemini_api_key` application/configuration references with an optional server-only `[voyage] api_key`; never store a real key in tracked files.
- Keep AI STAR answer generation and its model fallback unchanged.
- Add an additive Supabase migration that:
  - retains the existing 768-dimensional Gemini column for rollback;
  - makes that legacy column nullable;
  - adds a nullable 1024-dimensional Voyage column and its cosine index;
  - adds Voyage-specific active-chunk search functions with the current role restrictions.
- Write new chunk vectors only to the Voyage column and search only that column after cutover.
- Update focused configuration, ingestion, answering, database, app and schema tests, plus the example secrets and README.
- Remove the Google embedding SDK dependency only after no application import uses it.

## Cutover sequence — separately authorized HIGH actions

1. User creates a Voyage account/key and enters it directly into local and Streamlit secret controls. Codex must not receive or persist the raw key.
2. Run one tiny synthetic Voyage embedding compatibility check using no course text.
3. Apply the additive Supabase migration. **Completed 2026-10-12 with separate user approval.**
4. Coordinate application deployment and re-index every existing document from its private stored PDF. A brief Study-answer maintenance window is expected because query and stored embeddings must come from the same model.
5. Verify active-version metadata, 1024-dimensional storage, scoped retrieval quality, citations, failed-document recovery and production Study behavior.

Each external call, credential change, database migration/write, re-index and deployment above requires its own explicit approval. Local phase approval does not authorize them.

**Cutover approval:** on 2026-10-12, after being told the next phase comprised production re-indexing with Voyage, deployment, and retrieval/citation threshold verification, the user replied `approve`. Git mutations and entering the Voyage credential in Streamlit Community Cloud remain user-only actions under the project contract.

## Acceptance evidence for the local phase

- Document requests use `voyage-4-lite`, `input_type=document`, and 1024 dimensions; query requests use the same model/dimension with `input_type=query`.
- Empty, non-finite, wrong-count, wrong-dimension, oversized and malformed responses fail safely.
- HTTP 429 and transient network/5xx failures retain bounded ingestion retry behavior; provider payloads and credentials never reach UI errors.
- Database searches reject vectors other than 1024 values and call only the new Voyage RPCs.
- The migration is additive and preserves legacy vectors/chunks.
- Focused tests, full suite, compilation, dependency consistency and diff checks pass without a live provider/database call.

## Files

- `study_guide/embeddings.py` (new shared adapter)
- `study_guide/ingestion.py`
- `study_guide/answering.py`
- `study_guide/config.py`
- `study_guide/database.py`
- `study_guide/quizzing.py`
- `app.py`
- `supabase/migrations/005_voyage_embeddings.sql`
- `.streamlit/secrets.toml.example`
- `requirements.txt`
- relevant `tests/`
- `README.md`
- `PROGRESS.md`

## Risks and exclusions

- Voyage's free allowance is an external commercial policy, not an uptime or permanently-free guarantee. Requests beyond the allowance may be billable depending on the account.
- Course excerpts and student search questions will be transmitted to Voyage after cutover; account/data terms must be accepted by the user.
- Every existing document must be re-embedded. Mixing Gemini document vectors with Voyage query vectors is invalid even if dimensions were made equal.
- Deleting the legacy Gemini column/data is excluded; consider it only after Voyage production verification and a separate destructive-change approval.
- No key creation/entry, provider request, migration application, production database/storage write, re-index, deployment, dependency installation or Git mutation is included in the local phase.

## Result

- Added a standard-library Voyage adapter with `document`/`query` modes, native 1,024-dimensional float output, a 30-second timeout, a 4 MB response bound, strict response validation and redacted failures.
- Rewired configuration, Study retrieval, ingestion, the offline quiz adapter, UI controls and evaluation scripts from Gemini to Voyage. Removed the unused Google embedding SDK requirement without installing anything.
- Added and applied migration 005 with a separate Voyage vector column/index and private scoped/unscoped RPCs. The legacy Gemini column and all 81 existing legacy vectors remain preserved for rollback; the new Voyage column contains zero vectors until re-index.
- Failed-document retry now creates a current-provider version instead of reviving incompatible Gemini version metadata.
- Updated operations/setup documentation and added provider, retry, storage and schema regression coverage.
- Verification passed: 103 focused tests, 152 full tests, compilation of application/tests/evaluation scripts, `pip check`, and `git diff --check`.
- Live compatibility check approved by the user and completed on 2026-10-12: exactly one synthetic `document` request returned one finite, nonzero 1,024-dimensional vector in 1.146 seconds. No retry, course text, student data or persistence was involved.
- Supabase verification passed: SQL Editor reported success, both Voyage and both legacy Gemini RPCs are callable through the service role, and chunk counts were unchanged at 81 before/after. Retrieval similarity/threshold calibration, production re-index, UI cutover, deployment and rollback remain untested.
