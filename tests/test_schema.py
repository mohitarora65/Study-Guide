from pathlib import Path


SCHEMA = Path("supabase/migrations/001_initial.sql").read_text()
INGESTION_SCHEMA = Path("supabase/migrations/002_ingestion.sql").read_text()


def test_schema_contains_required_tables_and_vector_column() -> None:
    for table in (
        "documents",
        "document_versions",
        "chunks",
        "ingestion_runs",
        "threads",
        "messages",
    ):
        assert f"create table public.{table}" in SCHEMA

    assert "embedding extensions.vector(768) not null" in SCHEMA
    assert "page_number integer not null" in SCHEMA
    assert "user_key text not null" in SCHEMA
    assert "citations jsonb not null" in SCHEMA


def test_schema_denies_browser_roles_and_enables_rls() -> None:
    for table in (
        "documents",
        "document_versions",
        "chunks",
        "ingestion_runs",
        "threads",
        "messages",
    ):
        assert f"alter table public.{table} enable row level security" in SCHEMA
        assert f"revoke all on table public.{table} from anon, authenticated" in SCHEMA


def test_schema_has_ownership_and_deletion_constraints() -> None:
    assert "references public.threads(id) on delete cascade" in SCHEMA
    assert "references public.documents(id) on delete cascade" in SCHEMA
    assert "foreign key (id, active_version_id)" in SCHEMA
    assert "references public.document_versions(document_id, id)" in SCHEMA
    assert "unique (version_id, page_number, chunk_order)" in SCHEMA
    assert "retry_key text not null unique" in SCHEMA


def test_ingestion_schema_configures_private_pdf_bucket_and_metrics() -> None:
    assert "'course-pdfs', 'course-pdfs', false, 26214400" in INGESTION_SCHEMA
    assert "array['application/pdf']" in INGESTION_SCHEMA
    assert "file_size_bytes bigint" in INGESTION_SCHEMA
    assert "low_text_pages integer[]" in INGESTION_SCHEMA
    assert "extracted_character_count bigint" in INGESTION_SCHEMA


def test_ingestion_schema_activates_atomically_and_searches_only_active_ready_chunks() -> None:
    for function in (
        "activate_document_version",
        "mark_document_version_failed",
        "begin_document_delete",
        "match_chunks",
    ):
        assert f"function public.{function}" in INGESTION_SCHEMA
        assert f"grant execute on function public.{function}" in INGESTION_SCHEMA

    assert "d.status = 'ready'" in INGESTION_SCHEMA
    assert "d.active_version_id = v.id" in INGESTION_SCHEMA
    assert "v.status = 'ready'" in INGESTION_SCHEMA
    assert "p_embedding_dimension <> 768" in INGESTION_SCHEMA
    assert "status = 'deleting', active_version_id = null" in INGESTION_SCHEMA
