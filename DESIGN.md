# Interface Design — Grounded Mathematics Study Guide

**Status:** APPROVED — user replied “yes” on 2026-10-09
**Date:** 2026-10-09

## 1. Design Direction

A quiet, study-focused Streamlit interface with two role-aware areas: student chat and admin documents. The design prioritizes readable mathematics, visible source pages and honest states over decorative dashboard elements.

## 2. Information Architecture

```text
Signed out
└── Sign in with IIT Indore Google account

Student
├── New chat
├── Current conversation
└── My previous chats

Admin
├── Student chat
└── Document management
```

Students never see document controls. Admin navigation appears only after server-side role confirmation.

## 3. Sign-In Screen

- Product name and one-sentence purpose.
- “Sign in with Google” primary action.
- Notice that only verified `iiti.ac.in` accounts are allowed.
- Short privacy notice: questions and retrieved course excerpts are processed by the approved AI provider; identity details are not sent to it.
- Clear wrong-domain, cancelled-login and provider-error states.

No registration form, password fields or public demo access.

## 4. Student Chat

### Layout

```text
┌─────────────────────────────────────────────────────────┐
│ Mathematics Study Guide                    Account menu │
├────────────────┬────────────────────────────────────────┤
│ + New chat     │ Conversation title                     │
│                │                                        │
│ My chats       │ Student question                       │
│ • Thread A     │                                        │
│ • Thread B     │ Answer with rendered mathematics       │
│                │                                        │
│                │ Sources                                │
│                │ [Book name — page 42]                  │
│                │                                        │
│                │ [Ask a question…]             [Send]   │
└────────────────┴────────────────────────────────────────┘
```

On narrow screens, chat history moves into a collapsible drawer above the conversation.

### Answer presentation

- Render Markdown and LaTeX with Streamlit-supported safe rendering.
- Place sources directly below each answer, not in a distant bibliography.
- Each source chip shows the stored document name and PDF page number.
- A refusal appears as a neutral information state using the approved text: “The provided material is insufficient to answer this question.”
- Provider or database failures look different from an evidence refusal and include a retry action only when retry is safe.

### Chat actions

- New chat.
- Open an owned previous thread.
- Delete the current thread after a confirmation explaining permanent deletion.
- No editing, sharing, export, reactions or regeneration in Version 1.

## 5. Admin Document Management

### Document list

Each row shows:

- document name;
- status: uploaded, processing, ready, failed or deleting;
- page count and low-text-page warning when known;
- last updated time;
- allowed actions for the current state.

Status uses text plus an icon, never color alone.

### Upload flow

1. Select one PDF.
2. Show filename, size and the configured limit before submission.
3. Start upload/indexing with visible step/status text.
4. On success, show ready state and page/warning summary.
5. On failure, show a safe reason and retry action without making the document searchable.

Version 1 does not need drag-and-drop batches, folders or bulk actions.

### Destructive actions

- Re-index explains that the current ready version remains searchable until replacement succeeds.
- Delete requires confirmation naming the document and states that the PDF and derived index will be removed.
- After deletion begins, the document is immediately unavailable to student retrieval even if background cleanup must retry.

## 6. Required Interface States

| Area | States |
|---|---|
| Authentication | signed out, redirecting, wrong domain, provider error, signed in |
| Chat | empty, composing, retrieving/generating, answered, refused, quota error, service error |
| History | loading, populated, empty, deletion confirmation, deletion failed |
| Documents | empty, uploading, processing, ready, warning, failed, re-indexing, deleting |
| App availability | normal, waking, database unavailable, AI unavailable |

Long-running states include descriptive text and do not rely on an indefinite spinner alone.

## 7. Accessibility and Responsive Rules

- All inputs and controls have visible labels.
- Keyboard users can reach login, navigation, chat input, send, sources, upload and confirmation actions in a sensible order.
- Focus remains visible and moves to the result/error after submission.
- Status and errors use icon/text in addition to color.
- Body text and mathematical notation remain readable at mobile width and 200% zoom.
- Buttons have descriptive names such as “Delete thread” rather than icon-only controls.
- Motion is limited to native progress feedback; no decorative animation.

## 8. Content Rules

- Say “Sources” rather than “References generated by AI.” Citations come from stored metadata.
- Distinguish “insufficient course material” from technical failure.
- Do not expose stack traces, provider messages, object paths, user identifiers or quota details to students.
- Disclose free-host cold starts and pilot availability without presenting them as faults caused by the student.
- Admin errors state the next safe action: retry, replace the PDF or contact the operator.

## 9. Visual Scope

Use Streamlit's theme configuration and small targeted CSS only if needed for citation/source presentation. Do not introduce a separate component library or custom JavaScript in Version 1. Final colors and logo are non-blocking polish; accessible contrast and readable spacing are mandatory.

## 10. G4 Approval Decisions

Approval of this design confirms:

- role-aware student/admin navigation;
- chat with inline document/page sources;
- private chat history with permanent delete;
- simple one-PDF-at-a-time admin ingestion;
- explicit refusal, warning, quota and service-failure states;
- proposed 90-day inactive-chat retention;
- restrained Streamlit-native visual styling.

## 11. Version 2 Interface — Adaptive Quiz

**Status:** APPROVED — user replied “approve” on 2026-10-10
**Date:** 2026-10-10

### 11.1 Information Architecture

```text
Student
├── Study
└── Quiz
    ├── Choose topic
    ├── Active seven-question attempt
    ├── Results
    └── My progress

Admin
├── Documents
├── Quiz topics
└── Student progress
```

The Quiz page is visible to every authenticated student. Topic and progress administration appear only after server-side admin confirmation.

### 11.2 Student Quiz Start

- Page title and one sentence explaining that questions use approved PDFs.
- Active-topic select box managed by the admin.
- Selected topic's current mastery percentage, level and latest score when available.
- A short explanation that mastery personalizes difficulty and is not an official grade.
- “Start 7-question quiz” primary action.
- Privacy note that the institutional email and summary results are stored and visible to course admins; question text and selected answers are not kept after the results session.

If no topics are active, show a neutral state asking the student to return after the admin adds topics. If evidence is insufficient, name the selected topic and explain that no quiz was created.

### 11.3 Active Attempt

Render seven numbered question groups on one page. Each group contains:

- difficulty label;
- question text with safe Markdown/LaTeX;
- four radio-button options;
- no correctness, explanation or citation before submission.

Show “Answered X of 7.” The “Submit quiz” button remains disabled until all seven questions have one answer. Changing topic or starting another quiz is unavailable while an attempt is active; “Discard quiz” requires confirmation because the attempt cannot be restored.

### 11.4 Results

After the summary/mastery transaction succeeds, show:

- score as `correct / 7` and percentage;
- previous and updated mastery;
- current mastery level;
- one result card per question with selected option, correct option, correct/incorrect text, explanation and source document/PDF page;
- “Start another quiz on this topic” action.

Correctness uses text and icon in addition to color. Results remain available only in the active session and are not listed as reopenable history.

### 11.5 My Progress

Show a compact table with topic, mastery percentage/level, latest score, attempts and last completion date. Show summary-history rows with topic, score, resulting mastery and date. Do not show class rank, badges, streaks, leaderboards or predictions.

### 11.6 Admin Topic Management

- Text input plus “Add topic.”
- Rows show topic name, active/inactive state and update time.
- Rename validates uniqueness.
- Deactivate/activate uses an explicit labeled control; deactivation explains that history remains but new quizzes stop.
- No topic deletion or page-range editor.

### 11.7 Admin Student Progress

Show one row per student/topic with institutional email, topic, mastery, latest score, attempt count and last activity. Provide a simple email/topic filter only if the table becomes difficult to scan; no charts or exports in this phase.

“Delete quiz data…” opens a confirmation naming the institutional email and stating that all quiz summaries and mastery for that student will be permanently removed. The action does not delete chat history or the identity-provider account.

### 11.8 Required States

| Area | States |
|---|---|
| Topic selector | loading, active topics, no topics, service error |
| Quiz creation | ready, retrieving, generating, insufficient evidence, provider busy/error, invalid generation |
| Attempt | unanswered, partially answered, ready to submit, discard confirmation |
| Submission | saving, committed results, retryable database error, duplicate rerun |
| Progress | no attempts, populated, loading/error |
| Admin topics | empty, populated, validation error, activation change error |
| Admin progress | empty, populated, delete confirmation, delete success/error |

### 11.9 Accessibility and Responsive Rules

- Each radio group uses the full question text or numbered accessible label.
- Keyboard order follows questions 1–7 and then submission.
- Focus moves to the first unanswered question after an invalid submission attempt and to the score heading after success.
- Long equations and options wrap without horizontal page overflow.
- Results do not rely on red/green alone.
- On mobile width, cards and controls use one column; tables may use Streamlit's horizontally scrollable data table with visible column headings.

### 11.10 V2-G4 Approval Decisions

Approval confirms the deterministic graph boundary, no LangGraph persistence, summary-only Supabase records, institutional-email admin analytics, manual course-end deletion, the student Quiz/Progress screens and the admin Topics/Student Progress screens described above.
