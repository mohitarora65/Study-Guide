create extension if not exists vector with schema extensions;

create table public.documents (
    id uuid primary key default gen_random_uuid(),
    display_name text not null,
    object_path text not null unique,
    content_hash text not null unique,
    status text not null check (status in ('uploaded', 'processing', 'ready', 'failed', 'deleting')),
    active_version_id uuid,
    safe_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.document_versions (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    version_number integer not null check (version_number > 0),
    status text not null check (status in ('processing', 'ready', 'failed')),
    page_count integer check (page_count >= 0),
    embedding_model text not null,
    embedding_dimension integer not null check (embedding_dimension > 0),
    created_at timestamptz not null default now(),
    unique (document_id, version_number),
    unique (document_id, id)
);

alter table public.documents
    add constraint documents_active_version_fkey
    foreign key (id, active_version_id)
    references public.document_versions(document_id, id);

create table public.chunks (
    id uuid primary key default gen_random_uuid(),
    version_id uuid not null references public.document_versions(id) on delete cascade,
    page_number integer not null check (page_number > 0),
    chunk_order integer not null check (chunk_order >= 0),
    content text not null,
    content_hash text not null,
    embedding extensions.vector(768) not null,
    created_at timestamptz not null default now(),
    unique (version_id, page_number, chunk_order)
);

create table public.ingestion_runs (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    version_id uuid references public.document_versions(id) on delete cascade,
    retry_key text not null unique,
    status text not null check (status in ('processing', 'ready', 'failed')),
    processed_pages integer not null default 0 check (processed_pages >= 0),
    processed_chunks integer not null default 0 check (processed_chunks >= 0),
    safe_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.threads (
    id uuid primary key default gen_random_uuid(),
    user_key text not null,
    title text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.messages (
    id uuid primary key default gen_random_uuid(),
    thread_id uuid not null references public.threads(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    is_refusal boolean not null default false,
    citations jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index document_versions_document_id_idx
    on public.document_versions(document_id);
create index chunks_version_id_idx on public.chunks(version_id);
create index chunks_embedding_hnsw_idx
    on public.chunks using hnsw (embedding vector_cosine_ops);
create index ingestion_runs_document_id_idx
    on public.ingestion_runs(document_id);
create index threads_user_key_updated_at_idx
    on public.threads(user_key, updated_at desc);
create index messages_thread_id_created_at_idx
    on public.messages(thread_id, created_at);

alter table public.documents enable row level security;
alter table public.document_versions enable row level security;
alter table public.chunks enable row level security;
alter table public.ingestion_runs enable row level security;
alter table public.threads enable row level security;
alter table public.messages enable row level security;

revoke all on table public.documents from anon, authenticated;
revoke all on table public.document_versions from anon, authenticated;
revoke all on table public.chunks from anon, authenticated;
revoke all on table public.ingestion_runs from anon, authenticated;
revoke all on table public.threads from anon, authenticated;
revoke all on table public.messages from anon, authenticated;

grant usage on schema public to service_role;
grant select, insert, update, delete on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to service_role;

alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public grant select, insert, update, delete on tables to service_role;
alter default privileges in schema public grant usage, select on sequences to service_role;
