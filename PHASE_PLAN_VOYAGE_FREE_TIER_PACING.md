# Voyage Free-Tier Pacing Phase

**Status:** LOCAL PASS — USER_REVIEW_PENDING  
**Version:** Production embedding cutover follow-up  
**Date:** 2026-10-12

## Outcome

Make document ingestion fit the existing Voyage free-trial limits of 10,000 tokens per minute and three requests per minute without adding billing, dependencies, or provider changes.

## Scope

- Reduce document embedding batches from 32 chunks to 6 chunks.
- Wait 21 seconds between successful batch requests; retain the existing bounded transient retry and 61-second HTTP 429 wait.
- Update focused ingestion tests for batch sizing, pacing, retries, vector order, and safe failure behavior.
- Run the focused and full local test suites, compilation, dependency check, and diff check.
- Record verified results and the production retry outcome in `PROGRESS.md`.

## Impact

- Callers remain unchanged: upload, failed-document retry, and re-index all share `embed_chunks()`.
- The active 80-page PDF becomes 14 requests and should take about 4.5 minutes to embed before database insertion.
- The old Gemini version remains active until all Voyage vectors are created and atomically activated.
- The failed 417-page PDF is excluded from the next production retry.

## Evidence and risk

- The deployed 32-chunk batches contain approximately 12,841, 11,407, and 5,540 tokens using the installed tokenizer; the first two exceed the account's 10,000 TPM limit individually.
- Six-chunk batches keep the largest observed three-batch window near 7,799 tokens, leaving margin for tokenizer differences.
- Streamlit request/session longevity during the approximately 4.5-minute re-index remains a production verification risk.
- No credential, migration, database, deployment, Git, billing, or account change is included in this local phase. The user performs all Git mutations; production retry remains separately controlled by the existing cutover approval.

## Approval gate

The user replied `approve` on 2026-10-12. Local implementation and verification are complete. Deployment, Git mutation, and another production re-index were not performed.

## Result

- Document embedding now uses six-chunk batches with 21-second pacing between calls; the existing bounded retry behavior is unchanged.
- The real 81-chunk PDF now forms 14 batches. The installed tokenizer estimated a maximum batch of 2,979 tokens and a maximum consecutive three-batch window of 7,799 tokens.
- Verification passed: 33 focused tests, 152 full tests, compilation, `pip check`, and `git diff --check`.
- User-reported difficulty: production re-index again showed the Voyage allowance/rate-limit message.
- Agent-observed cause: 32-chunk requests were approximately 12,841 and 11,407 tokens, individually above the account's 10,000 TPM limit; waiting and retrying could not make those requests valid.
- Lesson: rate-limit handling must bound request size as well as retry timing.
