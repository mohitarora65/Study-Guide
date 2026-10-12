# Phase Plan — Readable Structured Answers

**Status:** LOCAL PASS / USER_REVIEW_PENDING  
**Version:** Existing deployed MVP follow-up  
**Requested:** 2026-10-12 — the user reported that current generated answers are not properly readable and asked for structured output.

**Approval:** USER_APPROVED — the user replied “yes” on 2026-10-12 to the whole-phase approval request.

## Outcome

New study-chat answers are easy to scan: a direct answer first, then short Markdown paragraphs, steps or bullets when useful, with Streamlit-compatible LaTeX for mathematics. Citations remain separately rendered from validated source metadata.

## Smallest complete change

- Keep the existing provider JSON object and its two validated fields: `answer` and `cited_chunk_ids`.
- Tighten the generation instruction so `answer` is readable Markdown rather than an unstructured text block.
- Preserve the current `ValidatedAnswer`, chat persistence, database schema, history renderer and citation trust boundary.
- Add one focused prompt-contract test and run the existing answering/app tests.

## Files in scope

- `study_guide/answering.py`
- `tests/test_answering.py`
- `README.md` only if its user-facing feature description needs one short clarification
- `PROGRESS.md`

## Acceptance evidence

- Captured provider messages require concise Markdown structure, readable mathematical notation and no unsupported material.
- Existing citation validation and refusal behavior still pass.
- Focused answering and app tests pass, followed by the full suite, compilation, `pip check` and `git diff --check`.
- No live AI request, production/database write, migration, dependency change, deployment or Git mutation.

## Risks and limits

- Formatting guidance improves future model responses but cannot guarantee identical structure for every question.
- Existing saved answers remain unchanged.
- This phase does not redesign the chat UI or add a new response-schema abstraction.

## Approval gate

Approved and completed locally. Production behavior remains unverified until the user deploys the change and asks a real grounded question.
