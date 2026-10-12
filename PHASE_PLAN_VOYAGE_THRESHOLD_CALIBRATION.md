# Phase Plan — Voyage Retrieval Threshold Calibration

**Status:** LOCAL PASS / USER_REVIEW_PENDING  
**Date:** 2026-10-12

## Outcome

Measure Voyage retrieval scores across the existing TA-approved 25 supported and 15 unsupported questions, then make the smallest tested threshold change only if the two groups have an adequate separation.

## Scope

- Make at most 40 `voyage-4-lite` query-embedding requests, one per approved evaluation question.
- Run read-only production searches at a zero diagnostic threshold; store only question IDs, expected class, top score/page and aggregate metrics in an ignored local artifact.
- Make no AI STAR calls and no database, document, account, billing, deployment or Git changes.
- If the measurements support a safe cutoff, update the shared retrieval threshold, focused tests, README, operations guidance and progress record locally.
- Do not retry the MML book during this phase.

## Acceptance evidence

- Report supported/unsupported score distributions, overlap and candidate threshold trade-offs.
- Preserve refusal safety; do not select a threshold merely to make one supported question pass.
- Run focused answering/database tests, the full suite, compilation, `pip check` and `git diff --check` after any code change.
- Keep deployment and user-controlled Git actions separate.

## Risks

- Score distributions may overlap, in which case a single threshold is insufficient and no production cutoff change will be recommended.
- The 40 query embeddings consume provider allowance; exact billed usage is not exposed locally.
- Retrieval-only calibration does not establish answer-generation quality or citation correctness.

## Result

- The user approved the whole phase on 2026-10-12.
- One batched Voyage request embedded all 40 approved questions; 40 read-only production searches made no database writes.
- Supported top scores ranged from `0.492516` to `0.675599`; unsupported top scores ranged from `0.159110` to `0.427963`, with no overlap.
- Every cutoff from `0.43` through `0.49` separates this dataset. The local cutoff is `0.46`, the midpoint of the observed gap, to avoid the brittle `0.0025` margin at `0.49`.
- Evidence is stored in ignored `evaluation/results/voyage_threshold_calibration_20261012.json` with IDs, expected classes, scores and pages only.
- Verification passed: 22 focused tests, 152 full tests, compilation, `pip check` and `git diff --check`.
- Deployment and grounded answer/citation smoke tests remain separate.
