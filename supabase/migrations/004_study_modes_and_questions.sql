alter table public.documents
    add column material_type text not null default 'theory'
        check (material_type in ('theory', 'questions')),
    add column study_scopes text[] not null default array['mid_sem', 'end_sem', 'quiz']::text[]
        check (
            cardinality(study_scopes) > 0
            and study_scopes <@ array['mid_sem', 'end_sem', 'quiz']::text[]
        );

create table public.question_candidates (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    version_id uuid not null references public.document_versions(id) on delete cascade,
    page_number integer not null check (page_number > 0),
    source_kind text not null check (source_kind in ('theory', 'questions')),
    prompt text not null check (char_length(btrim(prompt)) between 3 and 1000),
    options jsonb,
    correct_index integer,
    explanation text,
    difficulty text check (difficulty in ('easy', 'medium', 'hard')),
    topic_id uuid references public.quiz_topics(id) on delete set null,
    study_scopes text[] not null check (
        cardinality(study_scopes) > 0
        and study_scopes <@ array['mid_sem', 'end_sem', 'quiz']::text[]
    ),
    status text not null default 'draft' check (status in ('draft', 'approved', 'rejected')),
    content_hash text not null check (char_length(content_hash) = 64),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (version_id, content_hash),
    check (
        status <> 'approved'
        or (
            case when jsonb_typeof(options) = 'array'
                then jsonb_array_length(options) = 4
                else false
            end
            and correct_index between 0 and 3
            and coalesce(char_length(btrim(explanation)), 0) > 0
            and difficulty is not null
            and topic_id is not null
        )
    )
);

create index question_candidates_review_idx
    on public.question_candidates(status, updated_at desc);
create index question_candidates_quiz_idx
    on public.question_candidates(topic_id, status);

alter table public.question_candidates enable row level security;
revoke all on table public.question_candidates from public, anon, authenticated;
grant all on table public.question_candidates to service_role;

create or replace function public.match_chunks_by_scope(
    query_embedding extensions.vector(768),
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
           d.display_name, 1 - (c.embedding <=> query_embedding) as similarity
    from public.chunks c
    join public.document_versions v on v.id = c.version_id
    join public.documents d on d.id = v.document_id
    where d.status = 'ready'
      and d.active_version_id = v.id
      and v.status = 'ready'
      and study_scope = any(d.study_scopes)
      and 1 - (c.embedding <=> query_embedding) >= min_similarity
    order by c.embedding <=> query_embedding
    limit greatest(1, least(match_count, 50));
$$;

revoke all on function public.match_chunks_by_scope(extensions.vector, text, integer, double precision) from public, anon, authenticated;
grant execute on function public.match_chunks_by_scope(extensions.vector, text, integer, double precision) to service_role;
