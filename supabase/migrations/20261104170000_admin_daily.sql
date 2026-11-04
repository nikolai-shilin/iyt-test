-- The admins' charts (api/admin.mjs → the Overview page in the mini app): per UTC day over the last p_days days,
-- how many people joined (public.users.created_at), how many answers were given and how many of them were wrong
-- (public.answers). Every day of the range is there, with zeros on the quiet ones, oldest first.

create or replace function public.admin_daily(p_days int default 30)
returns table (day date, joined bigint, answers bigint, wrong bigint)
language sql
stable
security invoker
set search_path = ''
as $$
  with days as (
    select generate_series((now() at time zone 'utc')::date - (least(greatest(p_days, 1), 366) - 1),
                           (now() at time zone 'utc')::date, interval '1 day')::date as day
  ), j as (
    select (u.created_at at time zone 'utc')::date as day, count(*) as n
    from public.users u
    where u.created_at >= ((select min(day) from days)::timestamp at time zone 'utc')
    group by 1
  ), a as (
    select (x.at at time zone 'utc')::date as day, count(*) as n, count(*) filter (where not x.correct) as bad
    from public.answers x
    where x.at >= ((select min(day) from days)::timestamp at time zone 'utc')
    group by 1
  )
  select d.day, coalesce(j.n, 0), coalesce(a.n, 0), coalesce(a.bad, 0)
  from days d left join j using (day) left join a using (day)
  order by d.day;
$$;

revoke execute on function public.admin_daily(int) from public, anon, authenticated;
grant execute on function public.admin_daily(int) to service_role;
