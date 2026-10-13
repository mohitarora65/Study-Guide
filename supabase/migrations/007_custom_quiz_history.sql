create table public.custom_quiz_attempts (
    id uuid primary key,
    user_key text not null references public.quiz_profiles(user_key) on delete cascade,
    topics text[] not null check (cardinality(topics) between 1 and 20),
    question_count integer not null check (question_count in (5, 7, 10)),
    correct_count integer not null check (
        correct_count between 0 and question_count
    ),
    score numeric(5,2) not null check (score between 0 and 100),
    difficulty_mix jsonb not null check (jsonb_typeof(difficulty_mix) = 'object'),
    completed_at timestamptz not null default now()
);

create index custom_quiz_attempts_user_completed_idx
    on public.custom_quiz_attempts(user_key, completed_at desc);

alter table public.custom_quiz_attempts enable row level security;
revoke all on table public.custom_quiz_attempts from public, anon, authenticated;
grant select, insert, update, delete on table public.custom_quiz_attempts to service_role;

create or replace function public.complete_custom_quiz_attempt(
    p_attempt_id uuid,
    p_user_key text,
    p_email text,
    p_topics text[],
    p_question_count integer,
    p_correct_count integer,
    p_difficulty_mix jsonb
) returns table (
    score numeric,
    duplicate boolean
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_score numeric(5,2);
    v_existing public.custom_quiz_attempts%rowtype;
    v_topic text;
begin
    if p_user_key is null or p_user_key = ''
       or p_email is null or p_email <> lower(btrim(p_email)) or p_email not like '%@%'
       or p_topics is null
       or cardinality(p_topics) not between 1 and 20
       or p_question_count is null
       or p_question_count not in (5, 7, 10)
       or p_correct_count is null
       or p_correct_count < 0 or p_correct_count > p_question_count
       or p_difficulty_mix is null
       or jsonb_typeof(p_difficulty_mix) <> 'object'
       or not p_difficulty_mix ?& array['easy', 'medium', 'hard']
       or p_difficulty_mix - array['easy', 'medium', 'hard'] <> '{}'::jsonb
       or coalesce((p_difficulty_mix ->> 'easy')::integer, -1) < 0
       or coalesce((p_difficulty_mix ->> 'medium')::integer, -1) < 0
       or coalesce((p_difficulty_mix ->> 'hard')::integer, -1) < 0
       or (p_difficulty_mix ->> 'easy')::integer
          + (p_difficulty_mix ->> 'medium')::integer
          + (p_difficulty_mix ->> 'hard')::integer <> p_question_count then
        raise exception 'invalid custom quiz attempt';
    end if;

    foreach v_topic in array p_topics loop
        if v_topic is null or v_topic <> btrim(v_topic)
           or char_length(v_topic) not between 1 and 100
           or v_topic ~ '[[:cntrl:]]' then
            raise exception 'invalid custom quiz topic';
        end if;
    end loop;

    if cardinality(array(select distinct unnest(p_topics))) <> cardinality(p_topics) then
        raise exception 'duplicate custom quiz topic';
    end if;

    insert into public.quiz_profiles (user_key, email)
    values (p_user_key, p_email)
    on conflict (user_key) do update
    set email = excluded.email, updated_at = now();

    select * into v_existing
    from public.custom_quiz_attempts
    where id = p_attempt_id;

    if found then
        if v_existing.user_key <> p_user_key then
            raise exception 'attempt identifier conflict';
        end if;
        return query select v_existing.score, true;
        return;
    end if;

    v_score := round(p_correct_count * 100.0 / p_question_count, 2);
    insert into public.custom_quiz_attempts (
        id, user_key, topics, question_count, correct_count, score, difficulty_mix
    ) values (
        p_attempt_id, p_user_key, p_topics, p_question_count,
        p_correct_count, v_score, p_difficulty_mix
    );

    return query select v_score, false;
end;
$$;

revoke all on function public.complete_custom_quiz_attempt(
    uuid, text, text, text[], integer, integer, jsonb
) from public, anon, authenticated;
grant execute on function public.complete_custom_quiz_attempt(
    uuid, text, text, text[], integer, integer, jsonb
) to service_role;
