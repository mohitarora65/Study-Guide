# Phase Plan — Voyage Free-Tier Headroom

**Status:** LOCAL PASS / USER_REVIEW_PENDING  
**Version:** Production ingestion reliability follow-up  
**Approval:** USER_APPROVED — after the dashboard inspection showed 199,969,305 free `voyage-4-lite` tokens remaining but a Tier 0 limit of 10,000 TPM / 3 RPM, the user replied “ok do it” on 2026-10-12 to the proposed 8,000-token cap.

## Outcome

Keep each Voyage document-embedding request comfortably below the account's 10,000 TPM free-trial ceiling so tokenizer/accounting drift or small concurrent query embeddings do not consume the prior 200-token margin.

## Smallest complete change

- Reduce the shared document batch cap from 9,800 to 8,000 model tokens.
- Preserve the 128-input cap, 61-second spacing, one bounded transient retry, vector order and atomic version activation.
- Update the existing batching boundary tests and operator documentation.
- Run focused ingestion tests, the full suite, compilation, `pip check` and `git diff --check`.

## Boundaries

No provider call, production/database write, billing or account change, deployment, dependency change or Git mutation is authorized. A production MML retry remains separately gated after the user deploys the verified local change.

## Expected trade-off

The measured 283,498-token MML source needs at least 36 rather than 30 sequential batches, adding roughly six minutes of enforced waiting in exchange for 2,000 tokens of per-window headroom.

## Result

- Reduced the shared cap to 8,000 tokens; upload, retry and re-index inherit it through `embed_chunks()`.
- Updated the existing token-boundary tests plus README and operations guidance.
- Verification passed: 26 ingestion tests in 0.50 seconds, 155 full tests in 2.80 seconds, compilation, `pip check` and `git diff --check`.
- User-reported difficulty: the web re-index returned the Voyage allowance/rate-limit error again.
- Agent-observed cause: the dashboard showed ample free tokens but Tier 0's 10,000 TPM ceiling, while the previous 9,800-token cap left only 200 tokens of headroom. No implementation difficulty occurred.
- Production behavior remains unverified until the user reviews, commits and deploys the change, then separately authorizes one controlled MML re-index.
