from __future__ import annotations

from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from study_guide.answering import (
    INSUFFICIENT_MATERIAL,
    MAX_QUESTION_CHARS,
    AnsweringError,
    answer_question,
)
from study_guide.auth import Identity, IdentityError, authenticate_claims
from study_guide.config import ConfigurationError, Settings, load_settings
from study_guide.database import (
    DatabaseError,
    append_turn,
    build_client,
    complete_quiz_attempt,
    create_quiz_topic,
    create_thread,
    delete_quiz_profile,
    delete_thread,
    get_topic_mastery,
    get_document,
    download_pdf,
    insert_question_candidates,
    list_approved_questions,
    list_approved_question_topic_ids,
    list_admin_quiz_progress,
    list_documents,
    list_question_candidates,
    list_quiz_topics,
    list_student_quiz_attempts,
    list_student_quiz_progress,
    list_thread_messages,
    list_threads,
    rename_thread,
    update_quiz_topic,
    update_document_classification,
    update_question_candidate,
)
from study_guide.ingestion import (
    IngestionError,
    delete_document,
    ingest_pdf,
    reindex_document,
    retry_failed_document,
    prepare_pdf,
)
from study_guide.question_extraction import candidate_rows, extract_question_candidates
from study_guide.question_bank import (
    generate_bank_quiz,
    generate_custom_bank_quiz,
    has_bank_topic,
)
from study_guide.quizzing import QuizError, grade_quiz
from study_guide.study_modes import STUDY_MODE_LABELS, STUDY_SCOPES, active_study_scope


def render_configuration_error() -> None:
    st.title("Mathematics Study Guide")
    st.error("The application is not configured yet.")
    st.info(
        "An operator must create `.streamlit/secrets.toml` from the provided "
        "example before sign-in is available."
    )


def render_sign_in() -> None:
    st.title("Mathematics Study Guide")
    st.write("Ask questions using the approved Mathematics for AI/ML material.")
    st.write("Only verified IIT Indore (`iiti.ac.in`) Google accounts are allowed.")
    st.button("Sign in with Google", type="primary", on_click=st.login)
    st.write(
        "Your identity is used for access control and quiz progress. Your email is visible "
        "to administrators but is not sent to the AI provider."
    )


def _clear_quiz_session() -> None:
    for key in ("active_quiz", "active_quiz_kind", "active_quiz_topic_id", "quiz_result"):
        st.session_state.pop(key, None)
    for number in range(1, 11):
        st.session_state.pop(f"quiz-answer-{number}", None)


def _log_out() -> None:
    _clear_quiz_session()
    st.logout()


def render_account_controls(identity: Identity) -> None:
    role = "Admin" if identity.is_admin else "Student"
    st.sidebar.write(f"Signed in as {role}")
    st.sidebar.selectbox(
        "Study mode",
        list(STUDY_MODE_LABELS),
        index=list(STUDY_MODE_LABELS).index("overall"),
        format_func=STUDY_MODE_LABELS.get,
        key="study_mode",
    )
    st.sidebar.button("Log out", on_click=_log_out)


def render_study_page(settings: Settings, identity: Identity) -> None:
    st.title("Let’s resolve your doubt")
    answering_enabled = bool(settings.gemini_api_key and settings.ai_star_api_key)
    if not answering_enabled:
        st.info("Question answering is not configured yet. Your saved chats remain private and available below.")
    client = build_client(settings)
    try:
        threads = list_threads(client, identity.user_key)
    except DatabaseError as exc:
        st.error(str(exc))
        return

    if not threads:
        st.info("You have no saved chats yet.")

    thread_by_id = {thread["id"]: thread for thread in threads}
    active_id = st.session_state.get("active_chat_id")
    if active_id not in thread_by_id:
        active_id = next(iter(thread_by_id), None)
    options = [None, *thread_by_id]
    index = options.index(active_id) if active_id in options else 0
    selected_id = st.selectbox(
        "Saved chats",
        options,
        format_func=lambda thread_id: "New chat" if thread_id is None else thread_by_id[thread_id]["title"],
        index=index,
        key=f"history_chat_selector_{active_id or 'new'}",
    )
    st.session_state["active_chat_id"] = selected_id
    new_chat_title = ""
    if selected_id is None:
        new_chat_title = st.text_input(
            "Chat name (optional)",
            max_chars=80,
            placeholder="Leave blank to use your first question",
        )
    else:
        with st.expander("Rename chat"):
            renamed_title = st.text_input(
                "Chat name",
                value=thread_by_id[selected_id]["title"],
                max_chars=80,
                key=f"rename-chat-title-{selected_id}",
            )
            if st.button("Save chat name", key=f"rename-chat-{selected_id}"):
                try:
                    rename_thread(client, identity.user_key, selected_id, renamed_title)
                    st.rerun()
                except DatabaseError as exc:
                    st.error(str(exc))
    if selected_id is not None and st.button("Delete this chat…", key=f"delete-chat-{selected_id}"):
        st.session_state["confirm_chat_delete"] = selected_id
        st.rerun()
    if selected_id is not None and st.session_state.get("confirm_chat_delete") == selected_id:
        st.warning("Permanently delete this chat and its messages?")
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm delete chat", type="primary"):
            try:
                delete_thread(client, identity.user_key, selected_id)
                st.session_state.pop("confirm_chat_delete", None)
                st.session_state["active_chat_id"] = None
                st.rerun()
            except DatabaseError as exc:
                st.error(str(exc))
        if cancel.button("Cancel", key=f"cancel-chat-delete-{selected_id}"):
            st.session_state.pop("confirm_chat_delete", None)
            st.rerun()

    messages: list[dict[str, object]] = []
    if selected_id is not None:
        try:
            messages = list_thread_messages(client, identity.user_key, selected_id)
        except DatabaseError as exc:
            st.error(str(exc))
            return
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                for citation in message.get("citations") or []:
                    if isinstance(citation, dict) and isinstance(citation.get("page_number"), int):
                        st.write(
                            f"{citation.get('display_name', 'Course material')} · "
                            f"PDF page {citation['page_number']}"
                        )

    question = st.chat_input(
        "Ask a question from your course material…",
        max_chars=MAX_QUESTION_CHARS,
        disabled=not answering_enabled,
    )
    if question:
        try:
            with st.spinner("Searching course material and preparing a cited answer…"):
                answer = answer_question(
                    question,
                    gemini_api_key=settings.gemini_api_key,
                    ai_star_api_key=settings.ai_star_api_key,
                    database_client=client,
                    user_key=identity.user_key,
                    history=messages,
                    study_scope=active_study_scope(st.session_state.get("study_mode")),
                )
                thread_id = selected_id
                created_thread = thread_id is None
                if created_thread:
                    thread_id = create_thread(
                        client, identity.user_key, new_chat_title or question
                    )["id"]
                try:
                    append_turn(
                        client,
                        identity.user_key,
                        thread_id,
                        question=question,
                        answer=answer.text,
                        is_refusal=answer.text == INSUFFICIENT_MATERIAL,
                        citations=list(answer.citations),
                    )
                except DatabaseError:
                    if created_thread:
                        try:
                            delete_thread(client, identity.user_key, thread_id)
                        except DatabaseError:
                            pass
                    raise
            st.session_state["active_chat_id"] = thread_id
            st.session_state.pop("confirm_chat_delete", None)
            st.rerun()
        except (AnsweringError, DatabaseError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("The response could not be prepared. Please try again.")


def render_quiz_page(settings: Settings, identity: Identity) -> None:
    st.title("Let’s test")
    client = build_client(settings)
    try:
        try:
            extracted_topic_ids = list_approved_question_topic_ids(
                client, active_study_scope(st.session_state.get("study_mode"))
            )
        except DatabaseError:
            extracted_topic_ids = set()
        topics = [
            topic for topic in list_quiz_topics(client)
            if has_bank_topic(topic.get("name")) or topic.get("id") in extracted_topic_ids
        ]
    except DatabaseError as exc:
        st.error(str(exc))
        return
    if not topics:
        st.info("No reviewed quiz topics are available yet.")
        return

    topic_by_id = {topic["id"]: topic for topic in topics}
    active = "active_quiz" in st.session_state
    quiz_type = st.radio(
        "Quiz type",
        ("Quick Quiz", "Create Custom Quiz"),
        horizontal=True,
        disabled=active,
    )
    if quiz_type == "Quick Quiz":
        selected_topic_id = st.selectbox(
            "Topic",
            list(topic_by_id),
            format_func=lambda topic_id: topic_by_id[topic_id]["name"],
            disabled=active,
        )
        if st.button("Start 7-question quiz", type="primary", disabled=active):
            try:
                _clear_quiz_session()
                mastery = get_topic_mastery(client, identity.user_key, selected_topic_id)
                try:
                    reviewed = list_approved_questions(
                        client,
                        selected_topic_id,
                        active_study_scope(st.session_state.get("study_mode")),
                    )
                except DatabaseError:
                    reviewed = []
                with st.spinner("Preparing a reviewed quiz from the course material…"):
                    st.session_state.active_quiz = generate_bank_quiz(
                        topic_by_id[selected_topic_id]["name"],
                        mastery,
                        source_questions=reviewed,
                    )
                st.session_state.active_quiz_kind = "quick"
                st.session_state.active_quiz_topic_id = selected_topic_id
                st.rerun()
            except (DatabaseError, QuizError) as exc:
                st.error(str(exc))
    else:
        selected_topic_ids = st.multiselect(
            "Topics",
            list(topic_by_id),
            default=[next(iter(topic_by_id))],
            format_func=lambda topic_id: topic_by_id[topic_id]["name"],
            disabled=active,
        )
        question_count = st.selectbox(
            "Number of questions", (5, 7, 10), index=1, disabled=active
        )
        difficulties = st.multiselect(
            "Difficulty",
            ("easy", "medium", "hard"),
            default=("easy", "medium", "hard"),
            format_func=str.title,
            disabled=active,
        )
        st.caption("Custom quizzes are practice-only and do not change mastery.")
        if st.button("Create custom quiz", type="primary", disabled=active):
            try:
                _clear_quiz_session()
                topic_sources = {}
                for topic_id in selected_topic_ids:
                    try:
                        reviewed = list_approved_questions(
                            client,
                            topic_id,
                            active_study_scope(st.session_state.get("study_mode")),
                        )
                    except DatabaseError:
                        reviewed = []
                    topic_sources[topic_by_id[topic_id]["name"]] = reviewed
                with st.spinner("Preparing a custom quiz from reviewed questions…"):
                    st.session_state.active_quiz = generate_custom_bank_quiz(
                        topic_sources,
                        question_count,
                        tuple(difficulties),
                    )
                st.session_state.active_quiz_kind = "custom"
                st.rerun()
            except (DatabaseError, QuizError) as exc:
                st.error(str(exc))

    quiz = st.session_state.get("active_quiz")
    if quiz is None:
        return
    if st.button("Discard quiz"):
        _clear_quiz_session()
        st.rerun()

    st.subheader(quiz.topic)
    st.caption(
        "Difficulty: "
        + ", ".join(f"{count} {level}" for level, count in quiz.difficulty_mix.items() if count)
    )
    result = st.session_state.get("quiz_result")
    if result:
        total = len(quiz.questions)
        summary = (
            f"Score: {result['correct_count']}/{total} ({result['score']}%) · "
            f"Correct: {result['correct_count']} · Incorrect: {total - result['correct_count']}"
        )
        if result.get("mastery_after") is not None:
            summary += f" · Updated mastery: {result['mastery_after']}%"
        st.success(summary)
        st.write(
            "Difficulty: " + " · ".join(
                f"{level.title()} {values['correct']}/{values['total']}"
                for level, values in result["difficulty_breakdown"].items()
                if values["total"]
            )
        )
        for number, (question, answer) in enumerate(
            zip(quiz.questions, result["answers"], strict=True), start=1
        ):
            st.markdown(f"**{number}. {question.prompt}**")
            if answer == question.correct_index:
                st.write(f"Correct: {question.options[question.correct_index]}")
            else:
                st.write(f"Your answer: {question.options[answer]}")
                st.write(f"Correct answer: {question.options[question.correct_index]}")
            st.write(question.explanation)
            for citation in question.citations:
                st.caption(f"{citation['display_name']} · PDF page {citation['page_number']}")
        return

    with st.form("quiz-answers"):
        answers = [
            st.radio(
                f"{number}. {question.prompt}",
                range(4),
                index=None,
                format_func=lambda option, question=question: question.options[option],
                key=f"quiz-answer-{number}",
            )
            for number, question in enumerate(quiz.questions, start=1)
        ]
        submitted = st.form_submit_button("Submit all answers", type="primary")
    if submitted:
        if any(answer is None for answer in answers):
            st.error("Answer every question before submitting.")
            return
        try:
            selected_answers = [int(answer) for answer in answers]
            correct_count = grade_quiz(quiz, selected_answers)
            difficulty_breakdown = {
                level: {
                    "correct": sum(
                        answer == question.correct_index
                        for question, answer in zip(
                            quiz.questions, selected_answers, strict=True
                        )
                        if question.difficulty == level
                    ),
                    "total": sum(question.difficulty == level for question in quiz.questions),
                }
                for level in ("easy", "medium", "hard")
            }
            if st.session_state.get("active_quiz_kind") == "custom":
                saved = {
                    "score": round(correct_count * 100 / len(quiz.questions), 2),
                    "mastery_after": None,
                }
            else:
                saved = complete_quiz_attempt(
                    client,
                    attempt_id=str(uuid4()),
                    user_key=identity.user_key,
                    email=identity.email,
                    topic_id=st.session_state.active_quiz_topic_id,
                    correct_count=correct_count,
                    difficulty_mix=quiz.difficulty_mix,
                )
            st.session_state.quiz_result = {
                **saved,
                "correct_count": correct_count,
                "answers": selected_answers,
                "difficulty_breakdown": difficulty_breakdown,
            }
            st.rerun()
        except (DatabaseError, QuizError) as exc:
            st.error(str(exc))


def render_quiz_progress_page(settings: Settings, identity: Identity) -> None:
    st.title("Quiz progress")
    client = build_client(settings)
    try:
        progress = list_student_quiz_progress(client, identity.user_key)
        attempts = list_student_quiz_attempts(client, identity.user_key)
    except DatabaseError as exc:
        st.error(str(exc))
        return
    if not progress:
        st.info("Complete a quiz to begin tracking topic mastery.")
        return
    st.subheader("Topic mastery")
    st.dataframe(
        [
            {
                "Topic": row["topic"],
                "Mastery": f"{row['mastery_score']}%",
                "Latest score": f"{row['latest_score']}%",
                "Attempts": row["attempt_count"],
            }
            for row in progress
        ],
        hide_index=True,
        width="stretch",
    )
    st.subheader("Quiz summaries")
    st.dataframe(
        [
            {
                "Topic": row["topic"],
                "Score": f"{row['correct_count']}/7 ({row['score']}%)",
                "Mastery after": f"{row['mastery_after']}%",
                "Completed": row["completed_at"],
            }
            for row in attempts
        ],
        hide_index=True,
        width="stretch",
    )


def render_quiz_topics_page(settings: Settings) -> None:
    st.title("Quiz topics")
    client = build_client(settings)
    with st.form("new-quiz-topic", clear_on_submit=True):
        name = st.text_input("New topic name", max_chars=100)
        add = st.form_submit_button("Add topic", type="primary")
    if add:
        try:
            create_quiz_topic(client, name)
            st.rerun()
        except DatabaseError as exc:
            st.error(str(exc))
    try:
        topics = list_quiz_topics(client, active_only=False)
    except DatabaseError as exc:
        st.error(str(exc))
        return
    for topic in topics:
        with st.form(f"topic-{topic['id']}"):
            updated_name = st.text_input("Topic", value=topic["name"], key=f"topic-name-{topic['id']}")
            active = st.checkbox("Available to students", value=topic["active"], key=f"topic-active-{topic['id']}")
            if st.form_submit_button("Save"):
                try:
                    update_quiz_topic(client, topic["id"], name=updated_name, active=active)
                    st.rerun()
                except DatabaseError as exc:
                    st.error(str(exc))


def render_admin_quiz_progress_page(settings: Settings) -> None:
    st.title("Student quiz progress")
    client = build_client(settings)
    try:
        rows = list_admin_quiz_progress(client)
    except DatabaseError as exc:
        st.error(str(exc))
        return
    query = st.text_input("Filter by institutional email").strip().casefold()
    visible = [row for row in rows if query in row["email"].casefold()]
    if visible:
        st.dataframe(
            [
                {
                    "Email": row["email"],
                    "Topic": row["topic"],
                    "Mastery": f"{row['mastery_score']}%",
                    "Latest score": f"{row['latest_score']}%",
                    "Attempts": row["attempt_count"],
                    "Updated": row["updated_at"],
                }
                for row in visible
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No matching quiz progress.")
    profiles = {row["user_key"]: row["email"] for row in rows}
    if profiles:
        selected_user = st.selectbox(
            "Student profile to delete",
            list(profiles),
            format_func=profiles.get,
        )
        if st.button("Delete quiz profile…"):
            st.session_state.confirm_quiz_profile_delete = selected_user
        if st.session_state.get("confirm_quiz_profile_delete") == selected_user:
            st.warning(f"Permanently delete all quiz progress for {profiles[selected_user]}?")
            confirm, cancel = st.columns(2)
            if confirm.button("Confirm profile deletion", type="primary"):
                try:
                    delete_quiz_profile(client, selected_user)
                    st.session_state.pop("confirm_quiz_profile_delete", None)
                    st.rerun()
                except DatabaseError as exc:
                    st.error(str(exc))
            if cancel.button("Cancel"):
                st.session_state.pop("confirm_quiz_profile_delete", None)
                st.rerun()


def render_documents_page(settings: Settings) -> None:
    st.title("Documents")
    st.write("Private PDF ingestion · one file at a time · 25 MiB maximum")
    client = build_client(settings)

    flash = st.session_state.pop("document_flash", None)
    if flash:
        (st.info if flash[0] == "info" else st.success)(flash[1])

    if not settings.gemini_api_key:
        st.warning(
            "Gemini is not configured. Add `gemini.api_key` to the local secrets file "
            "to upload, retry or re-index documents."
        )

    uploaded = st.file_uploader(
        "Upload course material",
        type=["pdf"],
        accept_multiple_files=False,
        help="Text-based, unencrypted PDFs only. Scanned pages are not OCRed.",
    )
    material_type = st.radio(
        "Material type",
        ("theory", "questions"),
        format_func=lambda value: value.title(),
        horizontal=True,
    )
    study_scopes = st.multiselect(
        "Coverage",
        list(STUDY_SCOPES),
        default=list(STUDY_SCOPES),
        format_func=lambda value: STUDY_MODE_LABELS[value],
    )
    if st.button(
        "Upload and index",
        type="primary",
        disabled=uploaded is None or settings.gemini_api_key is None or not study_scopes,
    ):
        try:
            with st.status("Indexing PDF", expanded=True) as status:
                outcome = ingest_pdf(
                    client,
                    settings.gemini_api_key or "",
                    uploaded.name,
                    uploaded.type,
                    uploaded.getvalue(),
                    material_type=material_type,
                    study_scopes=tuple(study_scopes),
                    progress=status.write,
                )
                status.update(label="Indexing complete", state="complete")
            if outcome.duplicate:
                st.session_state.document_flash = (
                    "info",
                    f"{outcome.display_name} is already in the library.",
                )
            else:
                st.session_state.document_flash = (
                    "success",
                    f"{outcome.display_name} is ready with {outcome.chunk_count} page-linked chunks.",
                )
            st.rerun()
        except (IngestionError, DatabaseError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("The document could not be indexed. Try again.")

    st.subheader("Library")
    try:
        documents = list_documents(client)
    except DatabaseError as exc:
        st.error(str(exc))
        return

    if not documents:
        st.info("No course PDFs have been added yet.")
        return

    error_messages = {
        "EMBEDDING_FAILED": "Embedding failed. Retry when the provider is available.",
        "INVALID_EMBEDDING_RESPONSE": "The embedding response was invalid. Retry later.",
        "INGESTION_FAILED": "Indexing failed. Retry this document.",
    }
    for document in documents:
        with st.container(border=True):
            st.markdown(f"**{document['display_name']}**")
            st.write(f"Status: {document['status']}")
            st.caption(
                f"{document.get('material_type', 'theory').title()} · "
                + ", ".join(STUDY_MODE_LABELS[scope] for scope in document.get("study_scopes") or STUDY_SCOPES)
            )
            with st.expander("Classification"):
                current_type = document.get("material_type", "theory")
                current_scopes = document.get("study_scopes") or list(STUDY_SCOPES)
                with st.form(f"classification-{document['id']}"):
                    edited_type = st.radio(
                        "Material type",
                        ("theory", "questions"),
                        index=("theory", "questions").index(current_type),
                        format_func=lambda value: value.title(),
                        horizontal=True,
                    )
                    edited_scopes = st.multiselect(
                        "Coverage",
                        list(STUDY_SCOPES),
                        default=current_scopes,
                        format_func=lambda value: STUDY_MODE_LABELS[value],
                    )
                    save_classification = st.form_submit_button("Save classification")
                if save_classification:
                    try:
                        update_document_classification(
                            client, document["id"], edited_type, tuple(edited_scopes)
                        )
                        st.rerun()
                    except DatabaseError as exc:
                        st.error(str(exc))
            version = document.get("active_version")
            if version:
                st.write(
                    f"{version['page_count']} pages · "
                    f"{version['extracted_character_count']:,} extracted characters · "
                    f"{version['embedding_model']}"
                )
                low_pages = version.get("low_text_pages") or []
                if low_pages:
                    st.warning(
                        "Low extracted text on PDF page(s): "
                        + ", ".join(str(page) for page in low_pages)
                        + ". OCR was not performed."
                    )
            if document.get("safe_error"):
                st.error(
                    error_messages.get(
                        document["safe_error"], "Indexing failed. Retry this document."
                    )
                )

            first, second = st.columns(2)
            if document["status"] == "failed":
                if first.button(
                    "Retry indexing",
                    key=f"retry-{document['id']}",
                    disabled=settings.gemini_api_key is None,
                ):
                    try:
                        with st.status("Retrying PDF", expanded=True) as status:
                            retry_failed_document(
                                client,
                                settings.gemini_api_key or "",
                                document["id"],
                                progress=status.write,
                            )
                            status.update(label="Document is ready", state="complete")
                        st.session_state.document_flash = (
                            "success",
                            f"{document['display_name']} is ready.",
                        )
                        st.rerun()
                    except (IngestionError, DatabaseError) as exc:
                        st.error(str(exc))
            elif document["status"] == "ready":
                if first.button(
                    "Re-index",
                    key=f"reindex-{document['id']}",
                    disabled=settings.gemini_api_key is None,
                ):
                    try:
                        with st.status("Re-indexing PDF", expanded=True) as status:
                            reindex_document(
                                client,
                                settings.gemini_api_key or "",
                                document["id"],
                                progress=status.write,
                            )
                            status.update(label="New version is ready", state="complete")
                        st.session_state.document_flash = (
                            "success",
                            f"{document['display_name']} was re-indexed.",
                        )
                        st.rerun()
                    except (IngestionError, DatabaseError) as exc:
                        st.error(str(exc))
                if st.button("Extract question drafts", key=f"extract-{document['id']}"):
                    try:
                        source = get_document(client, document["id"])
                        prepared = prepare_pdf(
                            source["display_name"],
                            "application/pdf",
                            download_pdf(client, source["object_path"]),
                        )
                        extracted = extract_question_candidates(
                            prepared.pages, source.get("material_type", "theory")
                        )
                        rows = candidate_rows(
                            extracted,
                            document_id=source["id"],
                            version_id=source["active_version_id"],
                            material_type=source.get("material_type", "theory"),
                            study_scopes=tuple(source.get("study_scopes") or STUDY_SCOPES),
                        )
                        saved = insert_question_candidates(client, rows)
                        st.session_state.document_flash = (
                            "success",
                            f"Saved {saved} new question draft(s) for review.",
                        )
                        st.rerun()
                    except (IngestionError, DatabaseError, ValueError) as exc:
                        st.error(str(exc))

            if second.button("Delete…", key=f"delete-{document['id']}"):
                st.session_state.confirm_delete = document["id"]
                st.rerun()

            if st.session_state.get("confirm_delete") == document["id"]:
                st.warning(
                    f"Delete {document['display_name']}? It will immediately stop appearing in retrieval."
                )
                confirm, cancel = st.columns(2)
                if confirm.button(
                    "Confirm delete", type="primary", key=f"confirm-{document['id']}"
                ):
                    try:
                        delete_document(client, document["id"])
                        st.session_state.pop("confirm_delete", None)
                        st.session_state.document_flash = (
                            "success",
                            f"{document['display_name']} was deleted.",
                        )
                        st.rerun()
                    except DatabaseError as exc:
                        st.error(str(exc))
                if cancel.button("Cancel", key=f"cancel-{document['id']}"):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()


def render_question_review_page(settings: Settings) -> None:
    st.title("Question review")
    st.write("Complete and approve extracted MCQs before students can use them.")
    client = build_client(settings)
    try:
        candidates = list_question_candidates(client)
        topics = list_quiz_topics(client)
    except DatabaseError as exc:
        st.error(str(exc))
        return
    if not candidates:
        st.info("No question drafts are waiting for review.")
        return
    topic_by_id = {topic["id"]: topic for topic in topics}
    for candidate in candidates:
        with st.expander(
            f"{candidate['display_name']} · PDF page {candidate['page_number']}",
            expanded=False,
        ):
            with st.form(f"review-{candidate['id']}"):
                prompt = st.text_area("Question", candidate["prompt"], max_chars=1000)
                existing = candidate.get("options") or ["", "", "", ""]
                options = [
                    st.text_input(f"Option {letter}", existing[index])
                    for index, letter in enumerate("ABCD")
                ]
                correct_index = st.selectbox(
                    "Correct option", range(4),
                    index=candidate.get("correct_index") or 0,
                    format_func=lambda index: "ABCD"[index],
                )
                explanation = st.text_area("Explanation", candidate.get("explanation") or "")
                difficulty = st.selectbox(
                    "Difficulty", ("easy", "medium", "hard"),
                    index=("easy", "medium", "hard").index(candidate.get("difficulty") or "easy"),
                )
                topic_id = st.selectbox(
                    "Topic", list(topic_by_id),
                    index=(list(topic_by_id).index(candidate["topic_id"]) if candidate.get("topic_id") in topic_by_id else 0),
                    format_func=lambda value: topic_by_id[value]["name"],
                ) if topic_by_id else None
                scopes = st.multiselect(
                    "Coverage", list(STUDY_SCOPES),
                    default=candidate.get("study_scopes") or list(STUDY_SCOPES),
                    format_func=lambda value: STUDY_MODE_LABELS[value],
                )
                save = st.form_submit_button("Save draft")
                approve = st.form_submit_button("Approve", type="primary")
                reject = st.form_submit_button("Reject")
            if save or approve or reject:
                if approve and (
                    not prompt.strip() or len({option.strip() for option in options if option.strip()}) != 4
                    or not explanation.strip() or not topic_id or not scopes
                ):
                    st.error("Approval requires a question, four distinct options, answer, explanation, topic and coverage.")
                    continue
                try:
                    update_question_candidate(
                        client,
                        candidate["id"],
                        {
                            "prompt": prompt.strip(),
                            "options": [option.strip() for option in options],
                            "correct_index": correct_index,
                            "explanation": explanation.strip() or None,
                            "difficulty": difficulty,
                            "topic_id": topic_id,
                            "study_scopes": scopes,
                            "status": "approved" if approve else "rejected" if reject else "draft",
                        },
                    )
                    st.rerun()
                except DatabaseError as exc:
                    st.error(str(exc))


def render_authenticated_app(settings: Settings, identity: Identity) -> None:
    render_account_controls(identity)
    pages: dict[str, list[st.Page]] = {
        "Student": [
            st.Page(
                lambda: render_study_page(settings, identity),
                title="Study",
                url_path="study",
                default=True,
            ),
            st.Page(
                lambda: render_quiz_page(settings, identity),
                title="Adaptive quiz",
                url_path="quiz",
            ),
            st.Page(
                lambda: render_quiz_progress_page(settings, identity),
                title="Quiz progress",
                url_path="progress",
            ),
        ]
    }
    if identity.is_admin:
        pages["Admin"] = [
            st.Page(
                lambda: render_documents_page(settings),
                title="Documents",
                url_path="documents",
            ),
            st.Page(
                lambda: render_question_review_page(settings),
                title="Question review",
                url_path="question-review",
            ),
            st.Page(
                lambda: render_quiz_topics_page(settings),
                title="Quiz topics",
                url_path="quiz-topics",
            ),
            st.Page(
                lambda: render_admin_quiz_progress_page(settings),
                title="Student progress",
                url_path="student-progress",
            ),
        ]
    st.navigation(pages).run()


def main() -> None:
    st.set_page_config(
        page_title="Mathematics Study Guide",
        page_icon="📐",
        layout="wide",
    )
    try:
        settings = load_settings(st.secrets)
    except (ConfigurationError, StreamlitSecretNotFoundError):
        render_configuration_error()
        return

    if not getattr(st.user, "is_logged_in", False):
        render_sign_in()
        return

    try:
        identity = authenticate_claims(st.user, settings)
    except IdentityError:
        st.error("Access denied. Sign in with a verified IIT Indore Google account.")
        st.button("Log out", on_click=st.logout)
        return

    render_authenticated_app(settings, identity)


if __name__ == "__main__":
    main()
