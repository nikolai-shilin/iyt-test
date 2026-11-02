-- Student progress on the server (api/progress.mjs). The mini app keeps its whole state in one JSON object
-- (mastery per question, answers per day, exams, settings — see `fresh()` in miniapp/app.js); the server keeps the
-- newest copy per user, so progress survives a new phone and can later be shown on the website.
-- Every answer is also appended to public.answers, the history the state alone cannot give (when, which option, mode).

create table public.progress (
  user_id    bigint primary key references public.users (id) on delete cascade,
  state      jsonb not null,
  ts         bigint not null,          -- the app's state.ts (ms) when it was saved; the newer copy wins
  updated_at timestamptz not null default now()
);
alter table public.progress enable row level security;   -- no policies: only the server (secret key) reads it
grant all on public.progress to service_role;

-- The same answer sent twice (a retried request) must not count twice: one user, question and moment = one answer.
drop index public.answers_user_question_idx;
create unique index answers_user_question_at_key on public.answers (user_id, question_id, at desc);

-- One call per sync: remembers the user, appends the answers, keeps the newer state, and returns the server's
-- state only when it is newer than the one sent (or when nothing was sent), so a push costs no download.
create or replace function public.sync_progress(
  p_user bigint, p_name text, p_username text, p_lang text,
  p_state jsonb default null, p_ts bigint default null, p_answers jsonb default '[]'::jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  n_answers int := 0;
  v_ts      bigint;
  v_state   jsonb;
begin
  insert into public.users (id, name, username, lang) values (p_user, p_name, p_username, coalesce(p_lang, 'en'))
  on conflict (id) do update set name = excluded.name, username = excluded.username, updated_at = now()
    where (users.name, users.username) is distinct from (excluded.name, excluded.username);

  insert into public.answers (user_id, question_id, option, correct, mode, at)
  select p_user, a ->> 'q', (a ->> 'o')::smallint, (a ->> 'ok')::boolean, a ->> 'm', (a ->> 'at')::timestamptz
  from jsonb_array_elements(coalesce(p_answers, '[]'::jsonb)) as a
  where exists (select 1 from public.questions q where q.id = a ->> 'q')
  on conflict (user_id, question_id, at) do nothing;
  get diagnostics n_answers = row_count;

  if p_state is not null and p_ts is not null then
    insert into public.progress as p (user_id, state, ts) values (p_user, p_state, p_ts)
    on conflict (user_id) do update set state = excluded.state, ts = excluded.ts, updated_at = now()
      where p.ts < excluded.ts;
  end if;

  select p.ts, case when p.ts > coalesce(p_ts, -1) then p.state end into v_ts, v_state
  from public.progress p where p.user_id = p_user;
  return jsonb_build_object('ts', coalesce(v_ts, 0), 'state', v_state, 'answers', n_answers);
end
$$;

revoke execute on function public.sync_progress(bigint, text, text, text, jsonb, bigint, jsonb) from public, anon, authenticated;
grant execute on function public.sync_progress(bigint, text, text, text, jsonb, bigint, jsonb) to service_role;
