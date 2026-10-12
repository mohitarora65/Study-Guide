# Voyage Token-Aware Batching Phase

**Status:** LOCAL PASS — USER_REVIEW_PENDING  
**Version:** Production ingestion optimization  
**Date:** 2026-10-12

## Approved outcome

Reduce long-document indexing time while preserving Voyage's current 10,000 TPM and three RPM free-tier limits. The user approved the local optimization direction on 2026-10-12. Deployment, provider calls, production indexing and billing changes remain excluded.

## Smallest safe implementation

- Use Voyage's model-specific local tokenizer to assemble variable-size batches capped at 9,800 tokens.
- Send one nearly full TPM batch per 61-second rate window; retain the bounded transient retry, vector order and atomic database activation.
- Preserve all callers: upload, retry and re-index continue to use `embed_chunks()`.
- Update focused batching/pacing tests, then run the focused and full suites, compilation, dependency consistency and `git diff --check`.

## Dependency gate

The official tokenizer is provided by the `voyageai` SDK. The user specifically approved adding and locally installing `voyageai==0.5.0` with its `tokenizers` and supporting packages on 2026-10-12. The SDK is pinned in `requirements.txt`; its model tokenizer is downloaded locally on first use and no course text is sent for token counting.

Using the already installed OpenAI `tiktoken` package was rejected because it is not the `voyage-4-lite` tokenizer and cannot safely enforce Voyage's TPM limit. A fixed larger batch was also rejected because the 417-page book's token distribution has not been measured.

## Expected effect and evidence boundary

Read-only measurement of the stored MML source found 417 pages, 543 chunks and 283,498 `voyage-4-lite` tokens. The present six-chunk/21-second strategy needs about 91 requests and 32 minutes. Sequential 9,800-token batches need 30 requests and about 29.5 minutes of enforced waiting, close to the 28.4-minute TPM floor. A proposed 3,000-token/21-second design was rejected before completion because measurement showed it would take about 36 minutes.

## Separate later approvals

- User-controlled review, Git commit and push.
- Production MML retry, which consumes Voyage allowance and writes a new document version.
- Any paid-tier or account-limit change.

## Result

- Replaced fixed six-chunk batches with exact model-token batches capped at 9,800 tokens and 128 inputs, with one 61-second rate window between requests.
- Preserved upload, retry and re-index callers, vector order, bounded provider retry and atomic activation. Invalid tokenizer output, tokenizer failure and oversized individual chunks stop safely before embedding.
- Read-only preparation/tokenization of the private MML source made no provider or database write: 417 pages, 543 chunks, 283,498 tokens, 30 sequential batches and about 29.5 minutes of enforced waiting. The theoretical TPM floor is about 28.4 minutes.
- The active notes measure 30,044 tokens and four batches, reducing enforced wait from 273 to 183 seconds.
- Verification: 36 focused embedding/ingestion tests and 155 full tests passed; compilation, `pip check` and `git diff --check` passed.
- User-reported difficulty: indexing duration was too long. Agent-observed difficulty: the first proposed 3,000-token/21-second design measured slower than the existing implementation on MML, so it was discarded before completion. Lesson: optimize against total document tokens and the binding TPM limit, not request count alone.
