# Phase Plan — V1.1 Foundation, Identity and Data Boundary

**Status:** COMPLETE — PASS; user approved 2026-10-09  
**Version:** 1  
**Date:** 2026-10-09  

## 1. User-Visible Result

A locally runnable Streamlit foundation with Google sign-in configuration, exact `iiti.ac.in` access enforcement, student/admin navigation, safe secret handling and a migration-ready Supabase schema. A real Google login and development-database smoke test will run only if the user configures existing credentials outside chat and source control.

## 2. In Scope

- Create the minimal Python/Streamlit project structure.
- Install only phase-required dependencies into a project-local virtual environment after approval.
- Configure native Streamlit OIDC for Google Workspace using secret placeholders.
- Validate logged-in state, verified email, exact `iiti.ac.in` domain and server-side admin allowlist.
- Derive an opaque internal user key from OIDC issuer/subject using a server secret; do not persist email.
- Provide signed-out, access-denied, student and admin navigation states.
- Create the initial Supabase SQL migration for documents, versions, chunks, ingestion runs, threads and messages.
- Deny anonymous/public table access and document the server-only database boundary.
- Add narrow configuration/database connection checks without implementing ingestion or chat behavior.
- Add focused automated tests and update setup/progress documentation.

## 3. Out of Scope

- PDF upload, extraction, chunking, embeddings or vector search.
- Gemini calls, answering, citations or chat persistence behavior.
- Production deployment or public exposure.
- Creating Google, Supabase or Gemini accounts/projects; enabling billing; changing provider settings.
- Applying a migration to any non-development database.
- Real-user load testing, LangChain, OCR, agents, web search or additional features.
- Git staging, commits, branches, merges, pushes or hook trust.

## 4. Intended Files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit entry point and role-aware navigation. |
| `study_guide/__init__.py` | Package marker only. |
| `study_guide/config.py` | Required secret/config loading with safe failures. |
| `study_guide/auth.py` | OIDC claim validation, domain/admin rules and opaque user key. |
| `study_guide/database.py` | Minimal server-side Supabase connection check and shared access boundary. |
| `supabase/migrations/001_initial.sql` | Initial schema, indexes, vector extension and public-access restrictions. |
| `.streamlit/secrets.toml.example` | Placeholders only; never real credentials. |
| `.gitignore` | Exclude secrets, virtual environment, caches and local artifacts. |
| `requirements.txt` | Pinned phase dependencies only. |
| `tests/test_auth.py` | Domain, verified-email, role and user-key tests. |
| `tests/test_config.py` | Missing/invalid configuration tests. |
| `tests/test_schema.py` | Small static assertions for required tables, ownership fields and access restrictions. |
| `README.md` | Local setup, secrets, run/test steps and current limitations. |
| `PROGRESS.md` | Approval evidence, completed files, actual tests and restart handoff. |

If inspection during implementation proves one listed file unnecessary, omit it rather than creating boilerplate. Any additional file must be directly required by the approved result and reported.

## 5. Dependencies and Installation Permission

Planned direct dependencies:

- `streamlit` for the app and native OIDC;
- `Authlib` as required by Streamlit OIDC;
- `supabase` for server-side database access;
- `pytest` for tests.

Exact compatible versions will be checked against current official documentation and pinned. Approval of this phase authorizes creation of a project-local `.venv` and installation of these pinned packages only. It does not authorize global installs, unrelated packages, package-manager changes or external account creation.

## 6. Implementation Approach

1. Inspect current project files and Python tooling without altering Git.
2. Confirm current Streamlit/Supabase APIs from official documentation.
3. Create the smallest runnable skeleton and safe configuration boundary.
4. Implement pure claim-validation functions first, then connect them to `st.user`.
5. Define the schema and access restrictions in one ordered migration.
6. Add student/admin navigation without placeholder feature pages that imply unfinished functionality works.
7. Run focused tests, then the full phase suite; fix and rerun until passing or honestly blocked.
8. If existing development credentials are configured, run manual Google login and development Supabase connection/migration smoke tests. Never print secrets.
9. Update README and progress evidence, then stop for phase review/sign-off.

## 7. Acceptance and Test Evidence

Automated checks must prove:

- exact `@iiti.ac.in` verified addresses are allowed;
- lookalike, suffix, substring, uppercase/whitespace edge cases and unverified/missing email claims fail safely as intended;
- admin access requires an exact server-side allowlist match;
- the same OIDC issuer/subject yields a stable opaque user key, while different subjects do not;
- missing secrets produce a safe operator-facing error without leaking values;
- students cannot select admin navigation through browser-controlled input;
- schema includes ownership/citation-ready fields, required foreign keys/indexes and no anonymous grants;
- application imports and starts far enough for Streamlit/AppTest checks without real secrets.

Manual/integration evidence, when credentials are available:

- a real `iiti.ac.in` Google account reaches the student area;
- signed-out and wrong-domain sessions cannot reach protected views;
- only an allowlisted account sees admin navigation;
- the migration applies to the intended development Supabase project and a server-side connection succeeds.

Any credential-dependent check not run will be labeled **NOT TESTED**, never passed by inference.

## 8. Risks, Permissions and Stop Conditions

- Do not paste API keys, OAuth secrets, database keys or tokens into chat. Configure them locally or in the provider secret manager.
- Before applying SQL, resolve and display only the non-secret target project identity; never apply to an uncertain or production target.
- Remote migration requires explicit confirmation of the development target if credentials become available during the phase.
- No deployment, billing change, external account creation, destructive database action or Git mutation is authorized.
- Stop only for missing essential credentials, an uncertain external target, a material architecture/scope change or another safeguard defined in the approved project contract.

## 9. Tools and Fallbacks

- **Context7/official docs:** verify current Streamlit OIDC and Supabase client behavior; fallback to official vendor documentation.
- **Ponytail Full:** keep the code and dependency set minimal; it does not reduce validation, authorization or tests.
- **pytest/Streamlit AppTest:** primary automated checks.
- **Playwright:** use only if a real browser flow adds evidence beyond AppTest; do not automate or persist the user's Google credentials. Manual login is the fallback.
- **Serena:** skip unless the new code becomes large enough to justify symbol tooling; ordinary `rg` and selective reads should suffice.

## 10. Model and Usage Forecast

- Recommended execution model: **GPT-6.1 Sol, medium reasoning**, following official guidance for complex coordinated technical work.
- Account availability/current selected model: **not visible to the workspace and therefore unverified**. If GPT-6.1 Sol is unavailable, use the strongest available Sol-class coding model at medium reasoning and record the actual selection.
- Estimated human-equivalent effort: **5–9 hours**.
- Estimated chat/context sessions: **2–3**.
- Estimated five-hour Codex usage windows: **1–2**; this is not a promise of continuous compute.
- Codex API tokens/spend and remaining account allowance: **unknown** because no billing/usage telemetry is exposed here.
- Application Gemini use in this phase: **none**.

## 11. User-Controlled Git Checkpoint After Review

After the phase passes and the user accepts it, suggest commands scoped to the actual created paths: `git status`, `git diff --stat`, explicit `git add <paths>`, `git diff --cached`, and a commit such as `feat: add authenticated app foundation`. The user runs every Git mutation.

## 12. Approval Effect

Approval authorizes end-to-end execution of this complete phase, including the listed local files, project-local virtual environment, pinned dependency installation, tests, fixes and documentation. It does not authorize remote migration without a confirmed development target, deployment, spending, production changes, external account creation or Git mutation.
