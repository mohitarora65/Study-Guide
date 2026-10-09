from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

from supabase import Client, create_client

from study_guide.config import Settings


class DatabaseError(RuntimeError):
    """Raised when a database or private-storage operation fails."""


def build_client(settings: Settings) -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


def check_connection(client: Any) -> None:
    try:
        client.table("documents").select("id").limit(1).execute()
    except Exception as exc:
        raise DatabaseError("Development database check failed") from exc


def _data(result: Any) -> Any:
    return getattr(result, "data", None)


def list_documents(client: Any) -> list[dict[str, Any]]:
    try:
        documents = _data(
            client.table("documents")
            .select(
                "id,display_name,status,safe_error,file_size_bytes,active_version_id,created_at,updated_at"
            )
            .order("updated_at", desc=True)
            .execute()
        ) or []
        active_ids = [row["active_version_id"] for row in documents if row["active_version_id"]]
        versions = []
        if active_ids:
            versions = _data(
                client.table("document_versions")
                .select(
                    "id,page_count,low_text_pages,extracted_character_count,embedding_model"
                )
                .in_("id", active_ids)
                .execute()
            ) or []
    except Exception as exc:
        raise DatabaseError("Documents could not be loaded") from exc

    versions_by_id = {row["id"]: row for row in versions}
    for document in documents:
        document["active_version"] = versions_by_id.get(document["active_version_id"])
    return documents


def search_active_chunks(
    client: Any,
    query_embedding: list[float],
    *,
    match_count: int = 8,
    min_similarity: float = 0.70,
) -> list[dict[str, Any]]:
    if (
        len(query_embedding) != 768
        or not all(math.isfinite(value) for value in query_embedding)
        or not any(value != 0 for value in query_embedding)
        or not 1 <= match_count <= 8
        or not 0 <= min_similarity <= 1
    ):
        raise DatabaseError("Course material could not be searched")
    try:
        rows = _data(
            client.rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": match_count,
                    "min_similarity": min_similarity,
                },
            ).execute()
        ) or []
        return rows
    except Exception as exc:
        raise DatabaseError("Course material could not be searched") from exc


def find_document_by_hash(client: Any, content_hash: str) -> dict[str, Any] | None:
    try:
        rows = _data(
            client.table("documents")
            .select("id,display_name,status")
            .eq("content_hash", content_hash)
            .limit(1)
            .execute()
        ) or []
    except Exception as exc:
        raise DatabaseError("Duplicate check failed") from exc
    return rows[0] if rows else None


def get_document(client: Any, document_id: str) -> dict[str, Any]:
    try:
        rows = _data(
            client.table("documents")
            .select("id,display_name,object_path,content_hash,status,active_version_id")
            .eq("id", document_id)
            .limit(1)
            .execute()
        ) or []
    except Exception as exc:
        raise DatabaseError("Document could not be loaded") from exc
    if not rows:
        raise DatabaseError("Document does not exist")
    return rows[0]


def upload_pdf(client: Any, object_path: str, data: bytes) -> None:
    try:
        client.storage.from_("course-pdfs").upload(
            object_path,
            data,
            {"content-type": "application/pdf", "upsert": "false"},
        )
    except Exception as exc:
        raise DatabaseError("Private PDF upload failed") from exc


def download_pdf(client: Any, object_path: str) -> bytes:
    try:
        return client.storage.from_("course-pdfs").download(object_path)
    except Exception as exc:
        raise DatabaseError("Private PDF download failed") from exc


def remove_pdf(client: Any, object_path: str) -> None:
    try:
        client.storage.from_("course-pdfs").remove([object_path])
    except Exception as exc:
        if getattr(exc, "status_code", None) == 404:
            return
        raise DatabaseError("Private PDF removal failed") from exc


def create_document_records(
    client: Any,
    *,
    document: dict[str, Any],
    version: dict[str, Any],
    run: dict[str, Any],
) -> None:
    try:
        client.table("documents").insert(document).execute()
        client.table("document_versions").insert(version).execute()
        client.table("ingestion_runs").insert(run).execute()
    except Exception as exc:
        try:
            client.table("documents").delete().eq("id", document["id"]).execute()
        except Exception:
            pass
        raise DatabaseError("Document records could not be created") from exc


def next_version_number(client: Any, document_id: str) -> int:
    try:
        rows = _data(
            client.table("document_versions")
            .select("version_number")
            .eq("document_id", document_id)
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        ) or []
    except Exception as exc:
        raise DatabaseError("Document versions could not be loaded") from exc
    return int(rows[0]["version_number"]) + 1 if rows else 1


def create_version_records(
    client: Any, *, version: dict[str, Any], run: dict[str, Any]
) -> None:
    try:
        client.table("document_versions").insert(version).execute()
        client.table("ingestion_runs").insert(run).execute()
    except Exception as exc:
        try:
            client.table("document_versions").delete().eq("id", version["id"]).execute()
        except Exception:
            pass
        raise DatabaseError("Document version could not be created") from exc


def get_failed_attempt(client: Any, document_id: str) -> tuple[str, str]:
    try:
        versions = _data(
            client.table("document_versions")
            .select("id")
            .eq("document_id", document_id)
            .eq("status", "failed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ) or []
        if not versions:
            raise DatabaseError("No failed ingestion is available to retry")
        version_id = versions[0]["id"]
        runs = _data(
            client.table("ingestion_runs")
            .select("id")
            .eq("document_id", document_id)
            .eq("version_id", version_id)
            .eq("status", "failed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ) or []
        if not runs:
            raise DatabaseError("No failed ingestion is available to retry")
        client.table("chunks").delete().eq("version_id", version_id).execute()
        client.table("document_versions").update({"status": "processing"}).eq(
            "id", version_id
        ).execute()
        client.table("ingestion_runs").update(
            {
                "status": "processing",
                "processed_pages": 0,
                "processed_chunks": 0,
                "safe_error": None,
            }
        ).eq("id", runs[0]["id"]).execute()
        client.table("documents").update(
            {"status": "processing", "safe_error": None}
        ).eq("id", document_id).is_("active_version_id", "null").execute()
    except DatabaseError:
        raise
    except Exception as exc:
        raise DatabaseError("Failed ingestion could not be reset") from exc
    return version_id, runs[0]["id"]


def insert_chunks(client: Any, rows: list[dict[str, Any]]) -> None:
    try:
        for offset in range(0, len(rows), 100):
            client.table("chunks").insert(rows[offset : offset + 100]).execute()
    except Exception as exc:
        raise DatabaseError("Embedded chunks could not be stored") from exc


def activate_version(client: Any, parameters: dict[str, Any]) -> None:
    try:
        client.rpc("activate_document_version", parameters).execute()
    except Exception as exc:
        raise DatabaseError("Document version could not be activated") from exc


def mark_version_failed(
    client: Any,
    document_id: str,
    version_id: str,
    run_id: str,
    safe_error: str,
) -> None:
    try:
        client.rpc(
            "mark_document_version_failed",
            {
                "p_document_id": document_id,
                "p_version_id": version_id,
                "p_run_id": run_id,
                "p_safe_error": safe_error,
            },
        ).execute()
    except Exception as exc:
        raise DatabaseError("Failure state could not be recorded") from exc


def begin_document_delete(client: Any, document_id: str) -> str:
    try:
        object_path = _data(
            client.rpc(
                "begin_document_delete", {"p_document_id": document_id}
            ).execute()
        )
    except Exception as exc:
        raise DatabaseError("Document could not be made unavailable") from exc
    if not object_path:
        raise DatabaseError("Document does not exist")
    return str(object_path)


def delete_document_record(client: Any, document_id: str) -> None:
    try:
        client.table("documents").delete().eq("id", document_id).execute()
    except Exception as exc:
        raise DatabaseError("Document cleanup failed") from exc


def list_threads(client: Any, user_key: str) -> list[dict[str, Any]]:
    if not user_key:
        raise DatabaseError("Chat history could not be loaded")
    try:
        return _data(
            client.table("threads")
            .select("id,title,created_at,updated_at")
            .eq("user_key", user_key)
            .order("updated_at", desc=True)
            .limit(50)
            .execute()
        ) or []
    except Exception as exc:
        raise DatabaseError("Chat history could not be loaded") from exc


def list_thread_messages(
    client: Any, user_key: str, thread_id: str
) -> list[dict[str, Any]]:
    """Return messages only after confirming the thread belongs to the caller."""
    try:
        owned = _data(
            client.table("threads")
            .select("id")
            .eq("id", thread_id)
            .eq("user_key", user_key)
            .limit(1)
            .execute()
        ) or []
        if not owned:
            return []
        return _data(
            client.table("messages")
            .select("id,role,content,is_refusal,citations,created_at")
            .eq("thread_id", thread_id)
            .order("created_at")
            .limit(200)
            .execute()
        ) or []
    except Exception as exc:
        raise DatabaseError("Chat history could not be loaded") from exc


def create_thread(client: Any, user_key: str, title: str) -> dict[str, Any]:
    title = title.strip()[:80]
    if not user_key or not title:
        raise DatabaseError("Chat could not be created")
    try:
        rows = _data(
            client.table("threads")
            .insert({"user_key": user_key, "title": title})
            .select("id,title,created_at,updated_at")
            .execute()
        ) or []
        if not rows:
            raise ValueError("missing created thread")
        return rows[0]
    except Exception as exc:
        raise DatabaseError("Chat could not be created") from exc


def append_turn(
    client: Any,
    user_key: str,
    thread_id: str,
    *,
    question: str,
    answer: str,
    is_refusal: bool,
    citations: list[dict[str, Any]],
) -> None:
    if (
        not question.strip()
        or not answer.strip()
        or len(question) > 1_000
        or len(answer) > 8_000
        or not isinstance(citations, list)
    ):
        raise DatabaseError("Chat response could not be saved")
    try:
        owned = _data(
            client.table("threads")
            .select("id")
            .eq("id", thread_id)
            .eq("user_key", user_key)
            .limit(1)
            .execute()
        ) or []
        if not owned:
            raise DatabaseError("Chat response could not be saved")
        client.table("threads").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", thread_id).eq("user_key", user_key).execute()
        client.table("messages").insert(
            [
                {
                    "thread_id": thread_id,
                    "role": "user",
                    "content": question.strip(),
                    "is_refusal": False,
                    "citations": [],
                },
                {
                    "thread_id": thread_id,
                    "role": "assistant",
                    "content": answer.strip(),
                    "is_refusal": is_refusal,
                    "citations": citations,
                },
            ]
        ).execute()
    except DatabaseError:
        raise
    except Exception as exc:
        raise DatabaseError("Chat response could not be saved") from exc


def delete_thread(client: Any, user_key: str, thread_id: str) -> None:
    if not user_key or not thread_id:
        return
    try:
        client.table("threads").delete().eq("id", thread_id).eq(
            "user_key", user_key
        ).execute()
    except Exception as exc:
        raise DatabaseError("Chat could not be deleted") from exc
