create table public.quiz_topics (
    id uuid primary key default gen_random_uuid(),
    name text not null check (
        name = btrim(name)
        and char_length(name) between 1 and 100
        and name !~ '[[:cntrl:]]'
    ),
    normalized_name text generated always as (lower(name)) stored,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (normalized_name)
);

create table public.quiz_profiles (
    user_key text primary key,
    email text not null unique check (
        email = lower(btrim(email))
        and char_length(email) between 3 and 320
        and email like '%@%'
    ),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.topic_mastery (
    user_key text not null references public.quiz_profiles(user_key) on delete cascade,
    topic_id uuid not null references public.quiz_topics(id),
    mastery_score integer not null check (mastery_score between 0 and 100),
    attempt_count integer not null check (attempt_count > 0),
    latest_score numeric(5,2) not null check (latest_score between 0 and 100),
    updated_at timestamptz not null default now(),
    primary key (user_key, topic_id)
);

create table public.quiz_attempts (
    id uuid primary key,
    user_key text not null references public.quiz_profiles(user_key) on delete cascade,
    topic_id uuid not null references public.quiz_topics(id),
    correct_count integer not null check (correct_count between 0 and 7),
    score numeric(5,2) not null check (score between 0 and 100),
    mastery_before integer check (mastery_before between 0 and 100),
    mastery_after integer not null check (mastery_after between 0 and 100),
    difficulty_mix jsonb not null check (jsonb_typeof(difficulty_mix) = 'object'),
    completed_at timestamptz not null default now()
);

create index topic_mastery_user_updated_idx
    on public.topic_mastery(user_key, updated_at desc);
create index quiz_attempts_user_completed_idx
    on public.quiz_attempts(user_key, completed_at desc);
create index quiz_attempts_topic_completed_idx
    on public.quiz_attempts(topic_id, completed_at desc);

alter table public.quiz_topics enable row level security;
alter table public.quiz_profiles enable row level security;
alter table public.topic_mastery enable row level security;
alter table public.quiz_attempts enable row level security;

revoke all on table public.quiz_topics from anon, authenticated;
revoke all on table public.quiz_profiles from anon, authenticated;
revoke all on table public.topic_mastery from anon, authenticated;
revoke all on table public.quiz_attempts from anon, authenticated;

grant select, insert, update, delete on table public.quiz_topics to service_role;
grant select, insert, update, delete on table public.quiz_profiles to service_role;
grant select, insert, update, delete on table public.topic_mastery to service_role;
grant select, insert, update, delete on table public.quiz_attempts to service_role;

create or replace function public.complete_quiz_attempt(
    p_attempt_id uuid,
    p_user_key text,
    p_email text,
    p_topic_id uuid,
    p_correct_count integer,
    p_difficulty_mix jsonb
) returns table (
    score numeric,
    mastery_before integer,
    mastery_after integer,
    attempt_count integer,
    duplicate boolean
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_score numeric(5,2);
    v_before integer;
    v_after integer;
    v_count integer;
    v_existing public.quiz_attempts%rowtype;
begin
    if p_user_key is null or p_user_key = ''
       or p_email is null or p_email <> lower(btrim(p_email)) or p_email not like '%@%'
       or p_correct_count < 0 or p_correct_count > 7
       or jsonb_typeof(p_difficulty_mix) <> 'object'
       or coalesce((p_difficulty_mix ->> 'easy')::integer, -1) < 0
       or coalesce((p_difficulty_mix ->> 'medium')::integer, -1) < 0
       or coalesce((p_difficulty_mix ->> 'hard')::integer, -1) < 0
       or (p_difficulty_mix ->> 'easy')::integer
          + (p_difficulty_mix ->> 'medium')::integer
          + (p_difficulty_mix ->> 'hard')::integer <> 7 then
        raise exception 'invalid quiz attempt';
    end if;

    if not exists (select 1 from public.quiz_topics where id = p_topic_id) then
        raise exception 'quiz topic does not exist';
    end if;

    insert into public.quiz_profiles (user_key, email)
    values (p_user_key, p_email)
    on conflict (user_key) do update
    set email = excluded.email, updated_at = now();

    insert into public.topic_mastery (
        user_key, topic_id, mastery_score, attempt_count, latest_score
    ) values (p_user_key, p_topic_id, 0, 1, 0)
    on conflict (user_key, topic_id) do nothing;

    select tm.mastery_score, tm.attempt_count
    into v_before, v_count
    from public.topic_mastery as tm
    where tm.user_key = p_user_key and tm.topic_id = p_topic_id
    for update;

    select * into v_existing
    from public.quiz_attempts
    where id = p_attempt_id;

    if found then
        if v_existing.user_key <> p_user_key or v_existing.topic_id <> p_topic_id then
            raise exception 'attempt identifier conflict';
        end if;
        return query select
            v_existing.score,
            v_existing.mastery_before,
            v_existing.mastery_after,
            v_count,
            true;
        return;
    end if;

    v_score := round(p_correct_count * 100.0 / 7.0, 2);
    if v_count = 1 and v_before = 0 and not exists (
        select 1 from public.quiz_attempts
        where user_key = p_user_key and topic_id = p_topic_id
    ) then
        v_before := null;
        v_after := round(v_score);
        v_count := 1;
    else
        v_after := round(0.60 * v_score + 0.40 * v_before);
        v_count := v_count + 1;
    end if;

    insert into public.quiz_attempts (
        id, user_key, topic_id, correct_count, score,
        mastery_before, mastery_after, difficulty_mix
    ) values (
        p_attempt_id, p_user_key, p_topic_id, p_correct_count, v_score,
        v_before, v_after, p_difficulty_mix
    );

    update public.topic_mastery
    set mastery_score = v_after,
        attempt_count = v_count,
        latest_score = v_score,
        updated_at = now()
    where user_key = p_user_key and topic_id = p_topic_id;

    return query select v_score, v_before, v_after, v_count, false;
end;
$$;

create or replace function public.delete_quiz_profile(p_user_key text)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
    delete from public.quiz_profiles where user_key = p_user_key;
    return found;
end;
$$;

revoke all on function public.complete_quiz_attempt(uuid, text, text, uuid, integer, jsonb) from public, anon, authenticated;
revoke all on function public.delete_quiz_profile(text) from public, anon, authenticated;
grant execute on function public.complete_quiz_attempt(uuid, text, text, uuid, integer, jsonb) to service_role;
grant execute on function public.delete_quiz_profile(text) to service_role;
