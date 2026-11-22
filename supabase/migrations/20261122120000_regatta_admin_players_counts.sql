-- regatta_admin_players(days): the counts over every player in the period, not only the 500 listed.
--
-- The list stops at 500 players, the last seen first, and the site's tiles (ryc-regatta components/admin-players.tsx)
-- counted that list: with 535 players in 30 days (22 November) they showed 500, and 98 of 104 site accounts and 7 of 31
-- Telegram users, the longest unseen falling off the end as each new guest played. Now the answer carries `counts`:
-- the players, those new in the period, and the Telegram users, site accounts and guests among them, all of them; the
-- list is as it was (20261117150000_regatta_admin_players.sql).

create or replace function public.regatta_admin_players(days int default 30)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  n_days int := greatest(1, least(coalesce(days, 30), 365));
  since timestamptz := now() - make_interval(days => n_days);
  out jsonb;
  counts jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;
  with ids as (   -- a browser's later sign-in: its races name both
    select distinct on (vid) vid, user_id, player
      from public.game_races where vid is not null and (user_id is not null or player is not null) order by vid, started_at desc
  ), races as (
    select g.*, coalesce(g.user_id, i.user_id) as tg_id, case when g.user_id is null then coalesce(g.player, i.player) end as acct,
           coalesce(g.user_id::text, g.player::text, i.user_id::text, i.player::text, g.vid::text) as who
      from public.game_races g left join ids i on i.vid = g.vid and g.user_id is null and g.player is null
  ), players as (
    select who, max(tg_id) as tg_id, (array_agg(acct) filter (where acct is not null))[1] as acct,
           (array_agg(vid) filter (where vid is not null))[1] as vid,
           min(started_at) as first_at, max(started_at) as last_at
      from races where who is not null group by who
  ), recent as (
    select * from races where who is not null and started_at >= since
  ), sums as (
    select who, count(*) as n, count(finished_at) as fin, count(*) filter (where place <= 3) as top3, count(*) filter (where dsq) as dsq,
           count(distinct started_at::date) as days,
           percentile_cont(0.5) within group (order by (place - 1)::real / greatest(boats - 1, 1)) filter (where place is not null) as down,
           min(secs) filter (where daily is not null and finished_at is not null and not dsq) as best,
           count(rating) as rated, avg(rating) as rating,
           (array_agg(coalesce(perf ->> 'dev', '') || case when perf ->> 'tg' = '1' then ' tg' else '' end order by started_at desc) filter (where perf ->> 'dev' is not null))[1] as dev
      from recent group by who
  ), listed as (
    select p.*, s.n, s.fin, s.top3, s.dsq, s.days, s.down, s.best, s.rated, s.rating, s.dev,
           case when p.tg_id is not null then 'tg' when p.acct is not null then 'acct' else 'guest' end as kind
      from sums s join players p using (who)
  )
  select
    (select jsonb_build_object('players', count(*), 'new', count(*) filter (where first_at >= since),
        'tg', count(*) filter (where kind = 'tg'), 'acct', count(*) filter (where kind = 'acct'), 'guest', count(*) filter (where kind = 'guest'))
       from listed),
    (select coalesce(jsonb_agg(x.j order by x.last_at desc), '[]'::jsonb) from (
      select r.last_at, jsonb_build_object(
          'who', r.who,
          'kind', r.kind,
          'name', coalesce(u.name, nullif(a.raw_user_meta_data ->> 'display_name', '')),
          'handle', coalesce(u.username, a.email),
          'first', r.first_at, 'last', r.last_at, 'new', r.first_at >= since,
          'n', r.n, 'fin', r.fin, 'top3', r.top3, 'dsq', r.dsq, 'days', r.days, 'down', r.down, 'best', r.best,
          'rated', r.rated, 'rating', r.rating, 'dev', r.dev) as j
        from listed r
        left join public.users u on u.id = r.tg_id
        left join auth.users a on a.id = r.acct
       order by r.last_at desc limit 500
    ) x)
  into counts, out;
  return jsonb_build_object('since', since, 'players', out, 'counts', counts);
end $$;

revoke all on function public.regatta_admin_players(int) from public, anon;
grant execute on function public.regatta_admin_players(int) to authenticated;
