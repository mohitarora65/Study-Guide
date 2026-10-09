# AGENTS.md — Automatically loaded project instructions for Codex

**Mandatory:** Before working on this project, read `fun-optimised.md` in this folder and follow its **Section 0 startup/approval gates**. If the file is absent or unreadable, stop and report the missing file rather than proceeding.

- Start by confirming the actual project directory, then classify new vs. existing. Do read-only inspection first; never assume an existing codebase is approved for changes.
- **Do not create or modify application source code, install packages, scaffold, or deploy until G1–G5 planning gates have produced real files AND received explicit approval.** A project idea is not approval to implement.
- Discovery: ask **one question per message** until the idea, users, constraints and scope are clear.
- Persist the planning outputs required by `fun-optimised.md` (brief, research/PRD, stack, architecture/design, roadmap) to **actual Markdown files**. Verify each file exists before reporting its phase complete. Do not substitute chat summaries for deliverables.
- After each gate, summarize the saved file(s), request explicit user approval, and update `PROGRESS.md` with the decision. Never approve your own stage. Quick Build may combine docs but not skip essential decisions.
- **Only after approving a whole implementation phase**, execute its internal tasks end-to-end, including tests and fixes, then stop for review/sign-off. No task-by-task approval loops.
- Follow user-controlled Git: all staging, commits, branches, merges, and pushes are performed by the user. Ask permission before deployment, paid services, destructive actions, major scope/architecture changes, installs, or hook trust.
- Use available Serena, Context7, Playwright CLI and Ponytail selectively. They do not override approval gates.
- If the workspace is inaccessible, state the exact blocker; do not hallucinate documents or continue to coding.

**Startup response rule:** If no idea: ask only “What project do you want to build? Describe it in one or two sentences.” If an idea is known: ask the next single essential discovery question. **Never respond to the idea by immediately writing code.**
