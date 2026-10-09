alter table public.documents
    add column file_size_bytes bigint not null default 0 check (file_size_bytes >= 0);

alter table public.document_versions
    add column low_text_pages integer[] not null default '{}',
    add column extracted_character_count bigint not null default 0
        check (extracted_character_count >= 0);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('course-pdfs', 'course-pdfs', false, 26214400, array['application/pdf'])
on conflict (id) do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create or replace function public.activate_document_version(
    p_document_id uuid,
    p_version_id uuid,
    p_run_id uuid,
    p_page_count integer,
    p_low_text_pages integer[],
    p_extracted_character_count bigint,
    p_processed_chunks integer,
    p_embedding_model text,
    p_embedding_dimension integer
) returns void
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
    if p_page_count < 1 or p_processed_chunks < 1 or p_embedding_dimension <> 768 then
        raise exception 'invalid completed version metrics';
    end if;

    if not exists (
        select 1 from public.document_versions
        where id = p_version_id
          and document_id = p_document_id
          and status = 'processing'
          and embedding_model = p_embedding_model
          and embedding_dimension = p_embedding_dimension
    ) then
        raise exception 'version is not activatable';
    end if;

    if (select count(*) from public.chunks where version_id = p_version_id)
       <> p_processed_chunks then
        raise exception 'chunk count mismatch';
    end if;

    update public.document_versions
    set status = 'ready',
        page_count = p_page_count,
        low_text_pages = coalesce(p_low_text_pages, '{}'),
        extracted_character_count = p_extracted_character_count
    where id = p_version_id and document_id = p_document_id;

    update public.ingestion_runs
    set status = 'ready',
        processed_pages = p_page_count,
        processed_chunks = p_processed_chunks,
        safe_error = null,
        updated_at = now()
    where id = p_run_id
      and document_id = p_document_id
      and version_id = p_version_id
      and status = 'processing';

    if not found then
        raise exception 'ingestion run is not activatable';
    end if;

    update public.documents
    set active_version_id = p_version_id,
        status = 'ready',
        safe_error = null,
        updated_at = now()
    where id = p_document_id and status <> 'deleting';

    if not found then
        raise exception 'document is not activatable';
    end if;
end;
$$;

create or replace function public.mark_document_version_failed(
    p_document_id uuid,
    p_version_id uuid,
    p_run_id uuid,
    p_safe_error text
) returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    update public.document_versions
    set status = 'failed'
    where id = p_version_id and document_id = p_document_id;

    update public.ingestion_runs
    set status = 'failed', safe_error = p_safe_error, updated_at = now()
    where id = p_run_id and document_id = p_document_id and version_id = p_version_id;

    update public.documents
    set status = case when active_version_id is null then 'failed' else 'ready' end,
        safe_error = case when active_version_id is null then p_safe_error else null end,
        updated_at = now()
    where id = p_document_id and status <> 'deleting';
end;
$$;

create or replace function public.begin_document_delete(p_document_id uuid)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
    v_object_path text;
begin
    update public.documents
    set status = 'deleting', active_version_id = null, safe_error = null, updated_at = now()
    where id = p_document_id
    returning object_path into v_object_path;
    return v_object_path;
end;
$$;

create or replace function public.match_chunks(
    query_embedding extensions.vector(768),
    match_count integer default 8,
    min_similarity double precision default 0.0
) returns table (
    document_id uuid,
    version_id uuid,
    chunk_id uuid,
    page_number integer,
    chunk_order integer,
    content text,
    display_name text,
    similarity double precision
)
language sql stable
security definer
set search_path = public, extensions
as $$
    select d.id, v.id, c.id, c.page_number, c.chunk_order, c.content,
           d.display_name, 1 - (c.embedding <=> query_embedding) as similarity
    from public.chunks c
    join public.document_versions v on v.id = c.version_id
    join public.documents d on d.id = v.document_id
    where d.status = 'ready'
      and d.active_version_id = v.id
      and v.status = 'ready'
      and 1 - (c.embedding <=> query_embedding) >= min_similarity
    order by c.embedding <=> query_embedding
    limit greatest(1, least(match_count, 50));
$$;

revoke all on function public.activate_document_version(uuid, uuid, uuid, integer, integer[], bigint, integer, text, integer) from public, anon, authenticated;
revoke all on function public.mark_document_version_failed(uuid, uuid, uuid, text) from public, anon, authenticated;
revoke all on function public.begin_document_delete(uuid) from public, anon, authenticated;
revoke all on function public.match_chunks(extensions.vector, integer, double precision) from public, anon, authenticated;

grant execute on function public.activate_document_version(uuid, uuid, uuid, integer, integer[], bigint, integer, text, integer) to service_role;
grant execute on function public.mark_document_version_failed(uuid, uuid, uuid, text) to service_role;
grant execute on function public.begin_document_delete(uuid) to service_role;
grant execute on function public.match_chunks(extensions.vector, integer, double precision) to service_role;
