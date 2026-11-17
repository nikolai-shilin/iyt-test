-- The Regatta game's players, one by one, for the site's /admin/players (the ryc-regatta repo: components/admin-players.tsx).
--
-- regatta_admin_players(days): for a regatta admin alone (is_regatta_admin()), the players who began a race in the last
-- `days` (1–365), the last seen first, 500 at most. A player is a Telegram user (named by public.users: name and
-- @username), a site account (its user_metadata.display_name and email) or, for a guest, a browser (vid, unnamed); a
-- browser that later signed in is that player throughout, as regatta_admin_insight's retention counts them. For each:
-- when first and last seen (all time), whether first seen in the period, and in the period the races begun, finished,
-- in the top three and disqualified, the days played, the median place down the fleet (0 first, 1 last), the
-- best finish of today's race (seconds), the ratings given and their average, and the device of the latest race.
-- Old races with no player and no browser (before 17 November, a guest's) are left out.

create or replace function public.regatta_admin_players(days int default 30)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  n_days int := greatest(1, least(coalesce(days, 30), 365));
  since timestamptz := now() - make_interval(days => n_days);
  out jsonb;
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
  )
  select coalesce(jsonb_agg(x.j order by x.last_at desc), '[]'::jsonb) into out from (
    select p.last_at, jsonb_build_object(
        'who', p.who,
        'kind', case when p.tg_id is not null then 'tg' when p.acct is not null then 'acct' else 'guest' end,
        'name', coalesce(u.name, nullif(a.raw_user_meta_data ->> 'display_name', '')),
        'handle', coalesce(u.username, a.email),
        'first', p.first_at, 'last', p.last_at, 'new', p.first_at >= since,
        'n', s.n, 'fin', s.fin, 'top3', s.top3, 'dsq', s.dsq, 'days', s.days, 'down', s.down, 'best', s.best,
        'rated', s.rated, 'rating', s.rating, 'dev', s.dev) as j
      from sums s
      join players p using (who)
      left join public.users u on u.id = p.tg_id
      left join auth.users a on a.id = p.acct
     order by p.last_at desc limit 500
  ) x;
  return jsonb_build_object('since', since, 'players', out);
end $$;

revoke all on function public.regatta_admin_players(int) from public, anon;
grant execute on function public.regatta_admin_players(int) to authenticated;
