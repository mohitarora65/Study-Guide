# Phase Plan — Composer Answer Fallback

**Status:** LOCAL + ONE LIVE SYNTHETIC FALLBACK PASS / USER REVIEW PENDING.

## Outcome

Keep `deepseek-v4-flash` first, retain `deepseek-v4.1-flash`, and try `composer-2.5-fast` as a third Study-answer model after transient failures from each earlier model.

## Scope

- Update the existing AI STAR answer-model chain only; no new provider, dependency, endpoint, key, prompt, retrieval or quiz-model change.
- Preserve retry eligibility: timeout/network, HTTP 429 and HTTP 5xx only. Do not fall through on other HTTP errors, malformed output or local validation errors.
- Add a mocked end-to-end test that fails the first two attempts transiently, succeeds on Composer, and validates the grounded answer/citation.
- Update operator documentation and `PROGRESS.md`.

## Acceptance evidence

- A successful primary request still makes one call.
- The third model is called only after both prior models have eligible transient failures.
- Non-retryable failures stop without calling subsequent models.
- Focused/full tests, compilation, dependency check and diff check pass.

## Risk and limits

- A worst-case answer request can add one extra metered AI STAR call. The approved live test used one Composer request after locally simulated transient failures for the first two models; no course material or student data was sent. Balance impact is not available from the response.
- The live test confirms Composer endpoint/model compatibility for one small synthetic prompt and the app's fallback routing. It does not confirm actual DeepSeek outages, answer quality at scale, or cost. No catalog request, deployment, database write or Git mutation occurred.

## Result

- Local mocked end-to-end regression: HTTP 503 from DeepSeek V4 Flash, timeout from DeepSeek V4.1 Flash, valid grounded/cited answer from Composer; passed.
- One approved live probe on 2026-10-12 used the same sequence, but simulated the first two transient failures locally and made one AI STAR request to `composer-2.5-fast`. It returned `{"message":"Composer fallback test passed."}` in 10.78 seconds. No course/user content or identity was included. Provider usage/cost was not reported.
- The full application test suite passed: 161 tests; compileall, `pip check` and `git diff --check` passed.
