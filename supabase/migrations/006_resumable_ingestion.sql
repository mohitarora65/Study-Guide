create unique index ingestion_runs_one_processing_per_document_idx
    on public.ingestion_runs(document_id)
    where status = 'processing';

create or replace function public.save_voyage_embedding_batch(
    p_version_id uuid,
    p_chunks jsonb
) returns integer
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_saved integer;
begin
    if not exists (
        select 1 from public.document_versions v
        join public.ingestion_runs r on r.version_id = v.id
        where v.id = p_version_id and v.status = 'processing' and r.status = 'processing'
    ) then
        raise exception 'ingestion is not processing';
    end if;

    update public.chunks c
    set voyage_embedding = p.voyage_embedding
    from jsonb_to_recordset(p_chunks) as p(
        page_number integer,
        chunk_order integer,
        voyage_embedding extensions.vector(1024)
    )
    where c.version_id = p_version_id
      and c.page_number = p.page_number
      and c.chunk_order = p.chunk_order
      and c.voyage_embedding is null;
    get diagnostics v_saved = row_count;

    if v_saved <> jsonb_array_length(p_chunks) then
        raise exception 'embedding batch did not match pending chunks';
    end if;

    update public.ingestion_runs set updated_at = now()
    where version_id = p_version_id and status = 'processing';
    return v_saved;
end;
$$;

create or replace function public.claim_document_ingestion(
    p_document_id uuid,
    p_stale_seconds integer default 180
) returns table(version_id uuid, run_id uuid)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_run public.ingestion_runs%rowtype;
begin
    select r.* into v_run
    from public.ingestion_runs r
    join public.document_versions v on v.id = r.version_id
    where r.document_id = p_document_id
      and v.status in ('processing', 'failed')
      and r.status in ('processing', 'failed')
    order by r.created_at desc
    limit 1
    for update of r skip locked;

    if not found then
        raise exception 'no resumable ingestion';
    end if;
    if v_run.status = 'processing'
       and v_run.updated_at > now() - make_interval(secs => greatest(p_stale_seconds, 1)) then
        raise exception 'ingestion is still active';
    end if;

    update public.ingestion_runs
    set status = 'processing', safe_error = null, updated_at = now()
    where id = v_run.id;
    update public.document_versions
    set status = 'processing', embedding_model = 'voyage-4-lite', embedding_dimension = 1024
    where id = v_run.version_id;
    update public.documents
    set status = case when active_version_id is null then 'processing' else 'ready' end,
        safe_error = case when active_version_id is null then null else safe_error end,
        updated_at = now()
    where id = p_document_id and status <> 'deleting';

    return query select v_run.version_id, v_run.id;
end;
$$;

revoke all on function public.save_voyage_embedding_batch(uuid, jsonb) from public, anon, authenticated;
revoke all on function public.claim_document_ingestion(uuid, integer) from public, anon, authenticated;
grant execute on function public.save_voyage_embedding_batch(uuid, jsonb) to service_role;
grant execute on function public.claim_document_ingestion(uuid, integer) to service_role;
