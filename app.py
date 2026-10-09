from __future__ import annotations

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
    create_thread,
    delete_thread,
    list_documents,
    list_thread_messages,
    list_threads,
)
from study_guide.ingestion import (
    IngestionError,
    delete_document,
    ingest_pdf,
    reindex_document,
    retry_failed_document,
)


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
        "Your identity is used for access control. It is not sent to the AI provider."
    )


def render_account_controls(identity: Identity) -> None:
    role = "Admin" if identity.is_admin else "Student"
    st.sidebar.write(f"Signed in as {role}")
    st.sidebar.button("Log out", on_click=st.logout)


def render_study_page(settings: Settings, identity: Identity) -> None:
    st.title("Study")
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
        f"Ask about the course material (max {MAX_QUESTION_CHARS} characters)",
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
                )
                thread_id = selected_id
                created_thread = thread_id is None
                if created_thread:
                    thread_id = create_thread(client, identity.user_key, question)["id"]
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
    if st.button(
        "Upload and index",
        type="primary",
        disabled=uploaded is None or settings.gemini_api_key is None,
    ):
        try:
            with st.status("Indexing PDF", expanded=True) as status:
                outcome = ingest_pdf(
                    client,
                    settings.gemini_api_key or "",
                    uploaded.name,
                    uploaded.type,
                    uploaded.getvalue(),
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


def render_authenticated_app(settings: Settings, identity: Identity) -> None:
    render_account_controls(identity)
    pages: dict[str, list[st.Page]] = {
        "Student": [
            st.Page(
                lambda: render_study_page(settings, identity),
                title="Study",
                url_path="study",
                default=True,
            )
        ]
    }
    if identity.is_admin:
        pages["Admin"] = [
            st.Page(
                lambda: render_documents_page(settings),
                title="Documents",
                url_path="documents",
            )
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
