from pathlib import Path


SCHEMA = Path("supabase/migrations/001_initial.sql").read_text()
INGESTION_SCHEMA = Path("supabase/migrations/002_ingestion.sql").read_text()
QUIZ_SCHEMA = Path("supabase/migrations/003_adaptive_quiz.sql").read_text()
V3_SCHEMA = Path("supabase/migrations/004_study_modes_and_questions.sql").read_text()
VOYAGE_SCHEMA = Path("supabase/migrations/005_voyage_embeddings.sql").read_text()
RESUMABLE_SCHEMA = Path("supabase/migrations/006_resumable_ingestion.sql").read_text()
CUSTOM_QUIZ_SCHEMA = Path("supabase/migrations/007_custom_quiz_history.sql").read_text()


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


def test_quiz_schema_is_private_and_stores_summaries_only() -> None:
    for table in ("quiz_topics", "quiz_profiles", "topic_mastery", "quiz_attempts"):
        assert f"create table public.{table}" in QUIZ_SCHEMA
        assert f"alter table public.{table} enable row level security" in QUIZ_SCHEMA
        assert f"revoke all on table public.{table} from anon, authenticated" in QUIZ_SCHEMA

    assert "question" not in QUIZ_SCHEMA
    assert "p_email text" in QUIZ_SCHEMA
    assert "on delete cascade" in QUIZ_SCHEMA
    assert "function public.complete_quiz_attempt" in QUIZ_SCHEMA
    assert "function public.delete_quiz_profile" in QUIZ_SCHEMA
    assert "select tm.mastery_score, tm.attempt_count" in QUIZ_SCHEMA


def test_v3_schema_keeps_drafts_private_and_scopes_retrieval() -> None:
    assert "add column material_type" in V3_SCHEMA
    assert "add column study_scopes" in V3_SCHEMA
    assert "create table public.question_candidates" in V3_SCHEMA
    assert "status <> 'approved'" in V3_SCHEMA
    assert "alter table public.question_candidates enable row level security" in V3_SCHEMA
    assert "revoke all on table public.question_candidates from public, anon, authenticated" in V3_SCHEMA
    assert "function public.match_chunks_by_scope" in V3_SCHEMA
    assert "study_scope = any(d.study_scopes)" in V3_SCHEMA


def test_voyage_schema_is_additive_private_and_1024_dimensional() -> None:
    assert "alter column embedding drop not null" in VOYAGE_SCHEMA
    assert "add column voyage_embedding extensions.vector(1024)" in VOYAGE_SCHEMA
    assert "drop column embedding" not in VOYAGE_SCHEMA
    assert "p_embedding_dimension not in (768, 1024)" in VOYAGE_SCHEMA
    assert "security definer" in VOYAGE_SCHEMA
    assert "set search_path = public, extensions" in VOYAGE_SCHEMA
    assert "function public.match_chunks_voyage" in VOYAGE_SCHEMA
    assert "function public.match_chunks_voyage_by_scope" in VOYAGE_SCHEMA
    assert "c.voyage_embedding is not null" in VOYAGE_SCHEMA
    assert VOYAGE_SCHEMA.count("from public, anon, authenticated") == 2
    assert VOYAGE_SCHEMA.count("to service_role") == 2


def test_resumable_ingestion_schema_persists_batches_and_claims_stale_runs() -> None:
    assert "where status = 'processing'" in RESUMABLE_SCHEMA
    assert "function public.save_voyage_embedding_batch" in RESUMABLE_SCHEMA
    assert "function public.claim_document_ingestion" in RESUMABLE_SCHEMA
    assert "updated_at = now()" in RESUMABLE_SCHEMA
    assert "for update of r skip locked" in RESUMABLE_SCHEMA
    assert RESUMABLE_SCHEMA.count("to service_role") == 2
    assert RESUMABLE_SCHEMA.count("from public, anon, authenticated") == 2


def test_custom_quiz_history_schema_is_private_and_summary_only() -> None:
    assert "create table public.custom_quiz_attempts" in CUSTOM_QUIZ_SCHEMA
    assert "references public.quiz_profiles(user_key) on delete cascade" in CUSTOM_QUIZ_SCHEMA
    assert "function public.complete_custom_quiz_attempt" in CUSTOM_QUIZ_SCHEMA
    assert "alter table public.custom_quiz_attempts enable row level security" in CUSTOM_QUIZ_SCHEMA
    assert "from public, anon, authenticated" in CUSTOM_QUIZ_SCHEMA
    assert "to service_role" in CUSTOM_QUIZ_SCHEMA
    assert "question text" not in CUSTOM_QUIZ_SCHEMA
    assert "mastery" not in CUSTOM_QUIZ_SCHEMA
