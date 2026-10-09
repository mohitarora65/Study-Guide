# V2 Deployment Plan — Existing Streamlit App

**Status:** APPROVED — WAITING FOR USER PUSH
**Prepared:** 2026-10-10
**Target:** Existing `https://iiti-mathematics-study-guide.streamlit.app/` app, subject to dashboard confirmation
**Source:** `mohitarora65/Study-Guide`, `main`, `app.py`, subject to dashboard confirmation

## Outcome

Publish the locally implemented adaptive quiz to the existing app, then perform a bounded health/auth/navigation check without generating a quiz or creating student records.

## Known release risk

The three approved AI STAR quiz-generation requests each ended with `LengthFinishReasonError` at the prior 1,800-token cap. The local cap is now 3,500, but it has not been live-tested; the user declined another provider test and asked to proceed. Quiz generation may still return the safe temporary-unavailable message. This deployment must not be described as having verified quiz generation or production readiness.

## Required sequence and gates

1. **Review locally:** rerun tests/secret checks and review the exact V2 diff. The current worktree is uncommitted on `main`; `.serena/`, `.streamlit/secrets.toml`, local PDFs, virtual environments and ignored evaluation artifacts must not be pushed.
2. **Confirm production target:** user confirmed Supabase ref `kjxixskoeihbitcohhuo` is production. The open dashboard identifies the `Study-Guide` project as `PRODUCTION`. Do not inspect or copy secret values. Confirm the Streamlit app's connected repository/branch before the user's push.
3. **Production database preflight:** a read-only catalog query found all four quiz tables, both functions, RLS on all four tables, no SELECT privilege for `anon`/`authenticated`, no function execution for browser roles, and required function execution for `service_role`. The expected schema/access controls already exist, so migration `003` was not run again. Preserve the schema if application rollback is needed; do not delete data.
4. **User Git checkpoint:** only the user stages, commits and pushes. Streamlit Community Cloud monitors the connected GitHub source and updates the app after a push, so pushing to its configured branch is itself a production publication. The user must review the staged file list and diff before pushing.
5. **Cloud configuration:** use existing app secrets if they are already correct. No new key, provider, OAuth callback or paid service is planned. Any needed secrets, access, callback or app-setting change requires separate approval before editing.
6. **Post-deploy smoke check:** verify HTTPS health, Google sign-in/out and the authorized Student/Admin navigation. Do not generate a quiz, submit a real attempt, expose student records in logs, or make a capacity claim. If a safe UI/database check requires synthetic production data, stop for separate approval.
7. **Rollback:** if the app fails, user rolls back to the prior known-good V1 deployment/commit after confirming the exact deployed commit. Leave the additive quiz schema intact. Report any migration or app errors; do not perform destructive cleanup.

## Boundaries

- No provider calls, quiz generation, real student attempts, data deletion, paid services, OAuth permission changes, or provider switch.
- No Git staging, commits, branches, merges or pushes by Codex.
- No production database migration until the production project reference is confirmed and the migration action receives separate explicit approval.
- This is a controlled deployment request, not approval for a class-wide pilot. Final release status remains subject to actual smoke-test evidence.

## Current evidence

- Local worktree has uncommitted V2 changes; last known local commit is `b8829fb` (`v1`). Remote `origin` points to the expected GitHub repository. No Git mutation was made.
- Local automated suite: 97 passing tests; compile, dependency consistency and diff checks passed. Local UI tests use mocked identity/data; a real authenticated browser flow was not completed.
- Production Supabase ref was confirmed by the user and dashboard. Read-only catalog results confirm the quiz schema and role protections are present; no production SQL mutation was made.
- Deployment is waiting for the user to verify the Community Cloud source branch and push the reviewed changes. No public app update has occurred.
- Current Streamlit Community Cloud behavior is documented at [deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [connect GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account), and [app settings/secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings). Community Cloud checks the connected GitHub source for updates; secrets are managed in app settings.

## Approval record

The user approved this deployment plan on 2026-10-10 by replying “approve,” then approved the production migration action and confirmed `kjxixskoeihbitcohhuo` is the production project. Read-only preflight showed the expected schema and protections already exist, so no migration was needed or re-run. Git operations remain user-controlled.
