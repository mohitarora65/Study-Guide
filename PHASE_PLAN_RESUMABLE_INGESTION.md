# Resumable Voyage Ingestion Phase

**Status:** LOCAL IMPLEMENTATION — PRODUCTION MIGRATION/DEPLOYMENT NOT AUTHORIZED
**Date:** 2026-10-12

## Approved outcome

Resume interrupted Voyage indexing without repeating already successful embedding batches, show the actual current ingestion state in Documents, and prevent overlapping indexing runs for the same document.

## Scope

- Persist source chunks before embedding and each Voyage vector batch as soon as it succeeds.
- Heartbeat the run as batches save; claim only stale or failed runs for resume, updating incomplete versions to current Voyage metadata first.
- Enforce one processing ingestion run per document in PostgreSQL.
- Display in-progress/interrupted status and offer resume after three minutes without a heartbeat.
- Preserve current atomic version activation and keep an existing active version searchable during re-indexing.
- Add one migration, focused regression checks, and update the phase ledger.

## Files

- `study_guide/ingestion.py`
- `study_guide/database.py`
- `app.py`
- `supabase/migrations/006_resumable_ingestion.sql`
- `tests/test_ingestion.py`
- `tests/test_schema.py`
- `PROGRESS.md`

## Boundaries

- Applying migration 006, cleaning production orphan run/version 4, deployment, and starting a production retry are separate HIGH actions and are not included.
- No Voyage request or production database mutation is part of local implementation/verification.
- Persisted partial chunks remain attached to an inactive processing/failed version and remain excluded from retrieval.

## Acceptance evidence

- A regression check proves each successful batch is persisted before the next rate-window wait.
- Existing indexing and activation tests pass after conversion to database-backed vectors.
- Compilation, dependency consistency and whitespace checks pass.
- Migration stays unapplied; no production write, provider request, deployment, or Git mutation occurs.

## Result

- Added durable chunk seeding and batch-by-batch Voyage vector writes; a resumed version embeds only rows with no vector and can proceed directly to activation when every batch was already saved.
- Added one-processing-run-per-document protection and an atomic resume claim for failed or three-minute-stale runs. Successful saves refresh the run heartbeat; resume updates incomplete versions to current Voyage metadata before filling missing vectors.
- The Documents page uses the latest run status, suppresses stale errors while a run is processing, and offers resume after the heartbeat is stale or immediately for a failed latest run.
- The existing active version remains searchable during re-indexing; only completed versions pass the unchanged atomic activation RPC.
- Verification: focused tests 36 passed; full suite 157 passed in 2.87 seconds; `compileall`, `pip check`, and `git diff --check` passed.
- Agent-observed difficulty: local records confirmed version 4 remained `processing`, while Streamlit logs showed the worker being reprovisioned. It had no persisted vectors because prior code saved them only after all Voyage requests. The resumable schema and code address this lifecycle gap; production behavior remains unverified until migration and release.
- No production migration, orphan cleanup, Voyage call, database write, deployment, or Git mutation was performed.
