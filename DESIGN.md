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
