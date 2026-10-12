alter table public.chunks
    alter column embedding drop not null,
    add column voyage_embedding extensions.vector(1024);

create index chunks_voyage_embedding_hnsw_idx
    on public.chunks using hnsw (voyage_embedding vector_cosine_ops)
    where voyage_embedding is not null;

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
    if p_page_count < 1
       or p_processed_chunks < 1
       or p_embedding_dimension not in (768, 1024)
       or (p_embedding_model = 'voyage-4-lite' and p_embedding_dimension <> 1024) then
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
       <> p_processed_chunks
       or (
           p_embedding_model = 'voyage-4-lite'
           and (select count(*) from public.chunks
                where version_id = p_version_id and voyage_embedding is not null)
               <> p_processed_chunks
       ) then
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

create or replace function public.match_chunks_voyage(
    query_embedding extensions.vector(1024),
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
           d.display_name, 1 - (c.voyage_embedding <=> query_embedding) as similarity
    from public.chunks c
    join public.document_versions v on v.id = c.version_id
    join public.documents d on d.id = v.document_id
    where d.status = 'ready'
      and d.active_version_id = v.id
      and v.status = 'ready'
      and c.voyage_embedding is not null
      and 1 - (c.voyage_embedding <=> query_embedding) >= min_similarity
    order by c.voyage_embedding <=> query_embedding
    limit greatest(1, least(match_count, 50));
$$;

create or replace function public.match_chunks_voyage_by_scope(
    query_embedding extensions.vector(1024),
    study_scope text,
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
           d.display_name, 1 - (c.voyage_embedding <=> query_embedding) as similarity
    from public.chunks c
    join public.document_versions v on v.id = c.version_id
    join public.documents d on d.id = v.document_id
    where d.status = 'ready'
      and d.active_version_id = v.id
      and v.status = 'ready'
      and study_scope = any(d.study_scopes)
      and c.voyage_embedding is not null
      and 1 - (c.voyage_embedding <=> query_embedding) >= min_similarity
    order by c.voyage_embedding <=> query_embedding
    limit greatest(1, least(match_count, 50));
$$;

revoke all on function public.match_chunks_voyage(extensions.vector, integer, double precision) from public, anon, authenticated;
revoke all on function public.match_chunks_voyage_by_scope(extensions.vector, text, integer, double precision) from public, anon, authenticated;
grant execute on function public.match_chunks_voyage(extensions.vector, integer, double precision) to service_role;
grant execute on function public.match_chunks_voyage_by_scope(extensions.vector, text, integer, double precision) to service_role;
