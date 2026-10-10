# Product Requirements Document — Grounded Mathematics Study Guide

**Status:** APPROVED — user replied “yes” on 2026-10-09
**Date:** 2026-10-09
**Version:** 1.0 proposal

## 1. Product Objective

Provide approximately 120 Mathematics for AI/ML students with a web-based study assistant that answers in English using only teaching-assistant-approved PDFs, displays document/page citations, renders mathematics clearly, and refuses questions that the approved material cannot support.

## 2. Product Principles

1. **Evidence before fluency:** an incomplete refusal is preferable to a polished unsupported answer.
2. **Traceability:** students must be able to see which document pages support an answer.
3. **Least access:** students ask questions; only the teaching assistant manages source material.
4. **Minimal data:** identity is used for access control but is not sent to the AI provider.
5. **Small first release:** one course, one corpus, no web search, and no autonomous tools.

## 3. Users and Roles

### Student

- Signs in through the college identity provider.
- Must have a verified email under the approved college domain.
- Asks questions and views only their own chat history.
- Can delete their own chat threads.

### Admin / Teaching Assistant

- Is identified by a server-side allowlist.
- Uploads, views, re-indexes, and deletes approved PDFs.
- Sees document indexing state and errors.
- Cannot silently impersonate students.

## 4. Primary User Flows

### 4.1 Student Sign-In

1. Student opens the site and chooses the college identity provider.
2. The provider authenticates the student and returns a verified email claim.
3. The application checks the email against the exact approved college domain.
4. An allowed student enters the chat; all others see an access-denied message.

### 4.2 Admin Document Ingestion

1. Admin signs in and opens document management.
2. Admin uploads a text-based PDF.
3. The system validates the file, extracts page text, creates page-aware chunks and embeddings, and stores indexing status.
4. The document becomes searchable only after successful indexing.
5. Failed pages or documents remain unavailable and show a useful error.

### 4.3 Grounded Question Answering

1. Student submits a question.
2. The system retrieves the most relevant chunks from approved, successfully indexed documents.
3. If evidence is below the calibrated threshold, the system returns: “The provided material is insufficient to answer this question.”
4. Otherwise, the generator receives only the question, bounded conversation context, and retrieved excerpts.
5. The response is checked for citations that map to retrieved chunks.
6. The UI displays the answer with LaTeX and document/page citations.
7. The turn is stored in that student's private history.

## 5. Functional Requirements

### Authentication and Authorization

- **AUTH-01:** Users must authenticate through an approved OIDC identity provider.
- **AUTH-02:** Access must require a verified email from the exact configured college domain.
- **AUTH-03:** The admin role must be granted only through a server-side allowlist.
- **AUTH-04:** Unauthenticated and wrong-domain users must not access chat, history, documents, or admin functions.
- **AUTH-05:** A student must never read or modify another student's chat history.

### Document Management

- **DOC-01:** Only the admin can upload, re-index, or delete PDFs.
- **DOC-02:** Upload accepts PDF files only and rejects files beyond the documented deployment limit.
- **DOC-03:** The system records document name, stable document ID, PDF page number, ingestion status, and timestamps.
- **DOC-04:** Text must be extracted page by page so citations retain page provenance.
- **DOC-05:** A document is searchable only after all required indexing steps succeed.
- **DOC-06:** Deleting a document removes its stored file, extracted text, chunks, embeddings, and search availability.
- **DOC-07:** OCR for image-only pages is not required in Version 1; the system must report pages with little or no extractable text.

### Retrieval and Answering

- **RAG-01:** Retrieval must search only the active approved collection.
- **RAG-02:** The generator must receive only retrieved excerpts and bounded prior conversation needed to understand the current question.
- **RAG-03:** The product must not use web search, general browsing, or a second unapproved knowledge source.
- **RAG-04:** If retrieved evidence does not meet the calibrated support threshold, the system must return the standard insufficient-material response.
- **RAG-05:** Every non-refusal answer must include at least one citation mapped from retrieved metadata to a real document and PDF page.
- **RAG-06:** The model must not generate document names or page numbers that were not present in retrieved metadata.
- **RAG-07:** Retrieved PDF text and student questions must be treated as untrusted data, not system instructions.
- **RAG-08:** Answers must be in English and support browser-rendered LaTeX.
- **RAG-09:** When sources conflict or a formula condition is missing, the answer must state the uncertainty or refuse.
- **RAG-10:** Quota, timeout, parsing, and provider failures must produce a clear error without fabricating an answer.

### Chat History

- **CHAT-01:** Each student can create and revisit basic chat threads.
- **CHAT-02:** Stored turns include user ID, thread ID, question, answer/refusal, citations, and timestamps.
- **CHAT-03:** Students can delete their own threads.
- **CHAT-04:** The application must not expose student chat content in admin analytics in Version 1.
- **CHAT-05:** An automatic retention period will be selected before architecture approval; until then, deletion capability is mandatory and indefinite retention is not approved.

### Admin Operations

- **OPS-01:** Admin can see each document's uploaded, processing, ready, or failed status.
- **OPS-02:** Admin can retry a failed ingestion without creating duplicate active chunks.
- **OPS-03:** The application shows a student-friendly message when AI or hosting quotas are unavailable.
- **OPS-04:** Logs must not contain secrets, identity tokens, or full PDF contents.

## 6. Non-Functional Requirements

### Security and Privacy

- HTTPS in deployment.
- Secrets stored outside source control and never returned to the browser.
- Server-side authorization on every protected data operation.
- Per-user database policies or equivalent enforcement for chat history.
- Identity and email excluded from embedding and generation requests.
- Only the minimum retrieved passages needed for a question are sent to the AI provider.
- No model-accessible tools for file changes, database writes, web access, or secret access.

### Reliability

- A failed ingestion cannot partially replace a previously usable document index.
- Bounded retry is allowed only for transient provider errors.
- Duplicate upload/retry operations must not create duplicate active chunks.
- Free-tier sleep, quota, and capacity limits must be disclosed in the README and UI where relevant.

### Performance Targets for the Pilot

- Typical cached page load: target under 3 seconds after free-host wake-up.
- Typical answer: target under 15 seconds, excluding a sleeping host's cold start.
- Initial corpus indexing may be asynchronous or admin-blocking, but progress and failure must be visible.
- Concurrent capacity is not assumed; it must be measured against the chosen free services before release.

### Accessibility and Usability

- Keyboard-usable login, chat input, submission, history navigation, upload, and delete actions.
- Visible labels, focus states, readable contrast, and non-color-only status indicators.
- Errors explain the next action without exposing implementation details.
- Mathematical notation remains readable on desktop and mobile-width screens.

## 7. Acceptance Criteria

### Access

- A verified allowed-domain test account can enter the app.
- A verified wrong-domain account and an unauthenticated browser cannot enter protected areas.
- A normal student cannot reach document management or another student's stored thread.

### Documents

- Admin can upload representative notes and at least one large text-based book.
- Sampled extracted pages preserve the correct PDF page number.
- Deleting a test document makes its chunks unavailable to retrieval.
- A scanned or corrupt test file fails clearly without becoming searchable.

### Grounding Evaluation

Before student release, the teaching assistant supplies a minimum 40-question evaluation set:

- at least 25 questions answerable from the PDFs, including definitions, derivations, formulas, and applied questions;
- at least 15 questions not answerable from the PDFs, including plausible questions from outside the syllabus.

Release thresholds for that set:

- **Citation validity:** 100% of shown citations resolve to an indexed document/page.
- **Citation support:** at least 90% of cited answers are judged by the teaching assistant to be supported by the cited passages.
- **Refusal recall:** at least 90% of unsupported questions receive the insufficient-material response.
- **Unsupported-answer rate:** no more than 10% on the unsupported subset, with every failure reviewed before release.
- **Formula fidelity:** all high-risk formula questions in the set are manually checked; any material error blocks release.

These are pilot thresholds, not a claim of zero hallucinations. Results must be recorded from actual tests.

### Failure Handling

- Simulated AI timeout, quota exhaustion, failed upload, and unavailable database each return a clear non-fabricated error.
- Secrets and identity tokens do not appear in logs or browser-visible errors.

## 8. Version 1 Exclusions

- Multiple courses, classes, or document collections.
- Student uploads.
- Web search or general-knowledge fallback.
- OCR-first support for scanned books.
- Quizzes, automatic grading, recommendations, analytics, and instructor dashboards.
- Voice, mobile apps, multilingual output, and collaborative chats.
- Guaranteed uptime or support for all 120 students asking questions simultaneously on free tiers.

## 9. Dependencies and Open Decisions

G3 must compare and obtain user approval for:

- Streamlit authentication using the college's Google Workspace or Microsoft Entra OIDC setup;
- hosting choices and free-tier capacity;
- database, object storage, and vector retrieval options;
- generation and embedding providers, including rate limits and whether submitted content is used for product improvement;
- an achievable file-size limit based on the actual books;
- the automatic chat-retention period.

G4 must define:

- trust boundaries and authorization enforcement;
- ingestion and question-answer data flows;
- citation generation and grounding checks;
- failure recovery and deletion behavior;
- student and admin interface states.

## 10. Release Definition

Version 1 is ready for a controlled student pilot only when the approved requirements are implemented, the acceptance tests are run with real course material, no critical security issue remains, free-tier limits are documented, and the user explicitly approves release and deployment.

## 11. Version 2 Proposal — Adaptive Quiz Agent

**Status:** APPROVED — user replied “yes” on 2026-10-09
**Scope:** Add one PDF-grounded adaptive MCQ workflow without changing the Version 1 study assistant.

### 11.1 Roles

#### Student

- Chooses an active admin-managed topic.
- Starts a seven-question MCQ attempt adapted from prior mastery for that topic.
- Answers all questions before seeing results.
- Sees score, mastery, correct answers, explanations and document/page citations after submission.
- Sees their own summary history and topic mastery only.

#### Admin

- Creates, renames, activates and deactivates topic names.
- Views student-level summary history and mastery by institutional email.
- Deletes a student's quiz profile, attempt summaries and mastery at course end or when access should be removed.
- Does not see full generated questions or selected answers after the student's results session ends.

### 11.2 Primary Flows

#### Topic Management

1. Admin enters a unique topic name.
2. The server validates and stores the normalized name.
3. Active topics appear in the student quiz selector.
4. Deactivation prevents new attempts while preserving existing summary history.

#### Quiz Creation

1. Student selects an active topic and starts a quiz.
2. The server loads that student's current mastery for the topic.
3. The mastery band selects the required easy/medium/hard mix.
4. The server samples the required mix from the exact topic's bundled, source-checked bank.
5. Question and option order are randomized while the answer key remains correct.
6. If the topic or mastery mix lacks enough reviewed questions, creation stops with a clear message and stores nothing.
7. The complete quiz is kept in the authenticated Streamlit session until submission or session loss.

#### Submission and Mastery Update

1. Student submits answers for all seven questions.
2. The server grades locally using the validated answer key.
3. The database atomically stores one summary row and updates the student's topic mastery.
4. The results page shows all seven outcomes, explanations and citations.
5. No second AI call occurs during grading.

### 11.3 Functional Requirements

#### Topics

- **QUIZ-TOPIC-01:** Only configured admins can create, rename, activate or deactivate topics.
- **QUIZ-TOPIC-02:** Topic names must be trimmed, bounded, case-insensitively unique and free of control characters.
- **QUIZ-TOPIC-03:** Students can start quizzes only for active topics.
- **QUIZ-TOPIC-04:** An active topic must exactly match a bundled question-bank topic before students can start it.

#### Quiz Generation

- **QUIZ-GEN-01:** Each attempt contains exactly seven multiple-choice questions sampled locally without a live provider request.
- **QUIZ-GEN-02:** Each question has exactly four distinct options and exactly one correct option.
- **QUIZ-GEN-03:** Each question records one of `easy`, `medium` or `hard`, an explanation and an approved document/page citation.
- **QUIZ-GEN-04:** Every citation must be fixed in the reviewed bank and point to the approved course PDF.
- **QUIZ-GEN-05:** Questions must be unique within an attempt after normalization.
- **QUIZ-GEN-06:** Bank content is bounded and test-validated for types, lengths, option indexes, citations, difficulty capacity and duplicates.
- **QUIZ-GEN-07:** Selection is local and makes zero generation or embedding requests.
- **QUIZ-GEN-08:** If a topic or difficulty pool is unavailable, no quiz is created.
- **QUIZ-GEN-09:** Questions are sampled without replacement within an attempt; cross-attempt repetition is possible.

#### Grading and Feedback

- **QUIZ-GRADE-01:** All seven questions must be answered before submission.
- **QUIZ-GRADE-02:** The server grades deterministically from the validated answer key without another provider call.
- **QUIZ-GRADE-03:** Feedback remains hidden until successful submission.
- **QUIZ-GRADE-04:** Results show score, correct option, selected option, explanation and document/page citations for every question.
- **QUIZ-GRADE-05:** Repeated submission of the same in-session quiz must not create duplicate summaries or update mastery twice.

#### Adaptation

- **QUIZ-ADAPT-01:** Attempt score is `correct / 7 × 100`.
- **QUIZ-ADAPT-02:** First-attempt mastery equals that attempt score.
- **QUIZ-ADAPT-03:** Later mastery is `0.60 × latest score + 0.40 × previous mastery`, rounded to a whole percentage.
- **QUIZ-ADAPT-04:** Mastery `0–49` requests four easy and three medium questions.
- **QUIZ-ADAPT-05:** Mastery `50–79` requests two easy, four medium and one hard question.
- **QUIZ-ADAPT-06:** Mastery `80–100` requests one easy, three medium and three hard questions.
- **QUIZ-ADAPT-07:** The UI explains that mastery is a quiz-personalization indicator rather than an official course grade.

#### Persistence and Analytics

- **QUIZ-DATA-01:** Persist only student key, normalized institutional email, topic, correct count, score, mastery before/after, requested difficulty mix and completion timestamp.
- **QUIZ-DATA-02:** Full question text, option text, correct answers, selected answers, explanations and citations are not stored after the active results session.
- **QUIZ-DATA-03:** A student can read only their own mastery and summaries.
- **QUIZ-DATA-04:** Only a configured admin can list student emails and class progress.
- **QUIZ-DATA-05:** Email is never sent to the embedding or answer-generation provider and never written to application logs.
- **QUIZ-DATA-06:** Admin deletion removes the student's stored email, attempt summaries and mastery atomically.
- **QUIZ-DATA-07:** Operations documentation requires admin deletion at course end; automatic scheduled deletion is outside this proposal.

### 11.4 Non-Functional Requirements

- Existing question answering, citations, document ingestion and chat history must continue to work.
- Quiz generation must use one embedding request, one retrieval and normally one generation request per attempt.
- An invalid or failed generation must not modify mastery.
- Quiz submission and mastery update must be transactional and idempotent.
- All new tables must deny browser roles; protected access occurs through the authenticated Streamlit server.
- Institutional email must be encrypted in transit, excluded from logs/provider prompts and visible only in the admin dashboard.
- Controls and results must be keyboard usable and readable at mobile width.

### 11.5 Acceptance Criteria

- Admin can create an active topic and it appears in the student selector.
- A topic with sufficient evidence produces exactly seven valid MCQs matching the required difficulty mix.
- A topic without sufficient evidence produces no quiz and no stored attempt.
- Invalid options, duplicate questions, fabricated citations and incomplete sets are rejected.
- A student cannot submit with unanswered questions.
- A known answer selection receives the exact deterministic score and complete feedback after submission.
- Duplicate submission cannot double-count the attempt.
- The weighted mastery formula produces the documented value across at least three attempts and changes the next difficulty mix at each boundary.
- Cross-student read/write attempts fail; admin summary access succeeds only after server-side admin authorization.
- Admin deletion removes the target email, summaries and mastery without affecting other students.
- A human-reviewed quiz evaluation confirms each sampled question, correct answer, explanation and citation is supported by the cited PDF pages.
- Existing Version 1 regression checks continue to pass.

### 11.6 Release Limits

- Mastery is a transparent heuristic, not a psychometric assessment or official grade.
- Difficulty labels are generated targets and require pilot review; they are not formally calibrated.
- Questions may be similar across separate attempts because full question history is intentionally not retained.
- Results disappear if the active Streamlit session is lost after submission because full quiz content is not persisted.
- The admin is responsible for deleting quiz profiles at course end.
