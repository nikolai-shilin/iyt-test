-- Errors, logged for the admins (the Errors chart on the Overview page of the mini app, api/admin.mjs).

-- 1. One row per error: 'app' = an error the mini app did not catch (sent by the app to api/log.mjs), 'api' = a
--    failure in a server function (logError in api/settings.mjs, next to its console.error). user_id is the Telegram
--    user when known; it is not a reference to public.users, since an error can come before that row exists.
create table public.errors (
  id      bigint generated always as identity primary key,
  at      timestamptz not null default now(),
  source  text not null check (source in ('app', 'api')),
  place   text,                                         -- where: a function, or file:line in the app
  message text not null,
  user_id bigint
);
create index errors_at on public.errors (at);
alter table public.errors enable row level security;   -- no policies: only the server (secret key) reads and writes it
grant all on public.errors to service_role;

-- 2. The Overview charts now count the errors too: the same function as in 20261104190000_admin_series_flag_clears.sql
--    with one more column. The return type changes, so the old one is dropped first.
drop function if exists public.admin_series(text, int);
create function public.admin_series(p_unit text, p_count int)
returns table (at timestamptz, joined bigint, answers bigint, wrong bigint, errors bigint)
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
  ), e as (
    select date_trunc(p_unit, x.at, 'UTC') as at, count(*) as n
    from public.errors x
    where x.at >= (select min(at) from b)
    group by 1
  )
  select b.at, coalesce(j.n, 0), coalesce(a.n, 0), coalesce(a.bad, 0), coalesce(e.n, 0)
  from b left join j using (at) left join a using (at) left join e using (at)
  order by b.at;
$$;

revoke execute on function public.admin_series(text, int) from public, anon, authenticated;
grant execute on function public.admin_series(text, int) to service_role;
