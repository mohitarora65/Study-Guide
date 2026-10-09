# Project Brief — Grounded Mathematics Study Guide

**Status:** APPROVED — user replied “yes” on 2026-10-09  
**Date:** 2026-10-09

## Problem

Students in a Mathematics for AI/ML course need a study assistant that answers questions strictly from instructor-approved material. General-purpose AI assistants may introduce unsupported information, so this product must cite the supplied PDFs and clearly refuse when the material is insufficient.

## Users

- **Teaching assistant/admin:** uploads and manages the approved course PDFs.
- **Students:** approximately 120 students who register with an allowed college email domain and ask questions.

## Version 1 Goal

Deploy a usable, low-cost web application for one course and one shared collection of approved PDFs as soon as practical.

## Core Student Journey

1. A student registers or signs in using an email from the allowed college domain.
2. The student asks a Mathematics for AI/ML question in English.
3. The system retrieves relevant passages only from the approved PDFs.
4. It answers with rendered LaTeX and PDF/page citations when the material supports an answer.
5. It responds that the provided material is insufficient when it cannot support an answer.
6. The student can view basic chat history.

## Version 1 Scope

### Must Have

- Individual student accounts restricted to the college email domain.
- Admin-only PDF upload and management.
- One Mathematics for AI/ML course and one shared document collection.
- Support for mostly text-searchable notes and one or two large books.
- Retrieval-augmented answers grounded only in uploaded material.
- Source document and page citations.
- Explicit insufficient-material response instead of unsupported answers.
- English answers with LaTeX-rendered mathematics.
- Basic per-student chat history.
- Deployment for approximately 120 students.

### Out of Scope for Version 1

- Student PDF uploads.
- Multiple courses or separate knowledge collections.
- Open public registration or non-college email accounts.
- Web search or answers from general internet sources.
- OCR-first processing for predominantly scanned books.
- Quizzes, grading, analytics, discussion forums, or mobile apps.

## Constraints and Approved Assumptions

- Monthly operating budget target: free tier / near zero cost.
- Delivery priority: as soon as practical, without skipping security or grounding checks needed for real student use.
- Preferred development skills: Python and Streamlit.
- Third-party AI processing is allowed.
- The teaching assistant has permission to upload and make the selected materials searchable for the students.
- Approved college email domain: `iiti.ac.in`.

## Success Criteria

- Unauthorized email domains cannot create student accounts.
- Only the admin can add or remove source PDFs.
- Supported answers contain traceable document/page citations.
- Unsupported questions receive an insufficient-material response rather than a fabricated answer.
- Mathematical notation is readable in the browser.
- Core login, upload, indexing, question-answering, citation, refusal, and history flows work for the initial class.
- The chosen free tiers are documented with their limits; the system must fail clearly if a quota is exhausted.

## Project Classification

- **State:** New project; no application source code exists in this workspace.
- **Type:** Real-user educational web application.
- **Mode:** Learning / Production, with a tightly limited Version 1 because it will handle real student accounts and course material.

## Decisions Still Pending in Later Gates

- Evidence-based RAG approach and measurable grounding evaluation.
- Hosting, authentication, database, file storage, vector search, and AI provider choices.
- Data retention and deletion policy.
- Detailed architecture, interface design, roadmap, and implementation phases.

