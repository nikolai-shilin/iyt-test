-- For the admins (api/admin.mjs → the Admin pages in the mini app).

-- 1. The Overview charts: per UTC hour or day (p_unit 'hour' | 'day') over the last p_count of them, how many people
--    joined (public.users.created_at), how many answers were given and how many of them were wrong (public.answers).
--    Every bucket of the range is there, with zeros on the quiet ones, oldest first. The app asks for 24 hours and
--    91 days and cuts its 24h / 7d / 30d / 3m views out of them.
create or replace function public.admin_series(p_unit text, p_count int)
returns table (at timestamptz, joined bigint, answers bigint, wrong bigint)
language sql
stable
security invoker
set search_path = ''
as $$
  with b as (
    select g as at
    from generate_series(
      date_trunc(p_unit, now(), 'UTC') - (least(greatest(p_count, 1), 400) - 1) * ('1 ' || p_unit)::interval,
      date_trunc(p_unit, now(), 'UTC'),
      ('1 ' || p_unit)::interval) g
    where p_unit in ('hour', 'day')
  ), j as (
    select date_trunc(p_unit, u.created_at, 'UTC') as at, count(*) as n
    from public.users u
    where u.created_at >= (select min(at) from b)
    group by 1
  ), a as (
    select date_trunc(p_unit, x.at, 'UTC') as at, count(*) as n, count(*) filter (where not x.correct) as bad
    from public.answers x
    where x.at >= (select min(at) from b)
    group by 1
  )
  select b.at, coalesce(j.n, 0), coalesce(a.n, 0), coalesce(a.bad, 0)
  from b left join j using (at) left join a using (at)
  order by b.at;
$$;

revoke execute on function public.admin_series(text, int) from public, anon, authenticated;
grant execute on function public.admin_series(text, int) to service_role;

-- 2. Flags an admin took off a student's question: kind 'flags' (marked to come back to) or 'wrong' (reported as having
--    a mistake). The student's progress is one JSON state that the app overwrites on every sync (newest wins), so the
--    server cannot simply edit it: api/progress.mjs hands these rows to the app, the app drops the flag and syncs, and
--    the row is deleted once a synced state no longer has that flag. Until then api/admin.mjs leaves it out.
create table public.flag_clears (
  user_id     bigint not null references public.users (id) on delete cascade,
  question_id text not null,
  kind        text not null check (kind in ('flags', 'wrong')),
  by_user     bigint,                               -- the admin who took the flag off
  at          timestamptz not null default now(),
  primary key (user_id, question_id, kind)
);
alter table public.flag_clears enable row level security;   -- no policies: only the server (secret key) reads it
grant all on public.flag_clears to service_role;
