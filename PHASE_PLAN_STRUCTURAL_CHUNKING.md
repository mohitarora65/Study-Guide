# Structural Chunking Phase

**Status:** LOCAL PASS / USER_REVIEW_PENDING  
**Date:** 2026-10-12  
**Outcome:** Improve retrieval boundaries and reduce avoidable embedding volume without changing citation provenance or storage contracts.

## Scope

- Replace the fixed character-window implementation inside `study_guide/ingestion.py::_chunks_for_page` with page-bounded recursive structural chunking.
- Prefer boundaries in this order: blank-line paragraph, list/line boundary, sentence ending, then a hard character fallback.
- Greedily pack complete units up to 2,400 characters.
- Carry only complete trailing units, up to 250 characters, into the next chunk.
- Preserve the existing `Chunk` shape, 1-based PDF page, per-page `chunk_order`, SHA-256 content hash, embedding model/dimension, database schema, and retrieval API.
- Update focused ingestion tests and the README chunking description.

## Acceptance evidence

- No chunk crosses a PDF page or exceeds 2,400 characters.
- Normal paragraphs/sentences are not cut when a usable boundary exists.
- Oversized unbroken text still terminates deterministically through the hard-split fallback.
- Overlap consists of complete trailing structural units and remains at most 250 characters.
- Chunk order and hashes remain deterministic.
- Focused ingestion tests, full test suite, compilation, dependency consistency, and diff check pass.

## Impact and exclusions

- Existing active chunks do not change automatically. Re-indexing is required to adopt the new boundaries and remains a separate production write/provider action.
- The failed document still cannot embed until Gemini quota resets or is increased.
- No tokenizer, NLP package, PDF parser, OCR, database migration, provider/model change, billing action, deployment, or Git mutation is included.
- Complex PDF extraction/font warnings are not solved by chunking; extracted-text quality must be evaluated separately after quota is available.

## Files

- `study_guide/ingestion.py`
- `tests/test_ingestion.py`
- `README.md`
- `PROGRESS.md`

## Risk control

The active-version workflow already prevents partial replacements from becoming searchable. The phase will remain local; production re-indexing is not authorized by phase approval.

## Result

- Replaced fixed 1,800-character windows with standard-library structural splitting and greedy packing up to 2,400 characters.
- Paragraph, numbered/bulleted-list and sentence boundaries are preferred. Complete trailing units provide up to 250 characters of overlap; oversized units use deterministic non-overlapping hard splits.
- Preserved PDF page, per-page order, SHA-256 hash, embedding, storage and retrieval contracts.
- Updated the ingestion tests and README. No dependency, schema, provider or model change was needed.
- Verification passed: 22 focused ingestion tests in 0.30 seconds; 135 full tests in 2.33 seconds; empty/short/unpunctuated/paragraph/list assert checks; compilation; `pip check`; and `git diff --check`.
- Difficulty: the first overlap test assumed only the final sentence would be repeated, while the implementation correctly carried two complete sentences within the 250-character budget. The assertion was corrected to verify the actual bounded shared suffix/prefix. A later ad hoc uniqueness assertion was discarded because identical source passages may legitimately have identical content hashes; database identity is version/page/order.
- Not performed: provider request, production re-index, quota/billing change, deployment, dependency installation or Git mutation.
