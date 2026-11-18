-- What went wrong for whom, for the site's /admin/logs (the ryc-regatta repo: components/admin-logs.tsx).
--
-- regatta_admin_logs(days, person): for a regatta admin alone (is_regatta_admin()), over the last `days` (1–365):
--   totals: the visits of the game's page, those with a problem, and of them the loads that failed, the loads given up,
--           the visits that lost the 3D and those with an error on the page; the players they came to.
--   people: the players with a problem, the latest first, 200 at most. A problem is one of those visits, a race that ran
--           under 24 frames a second or one rated two stars or fewer. A player is as regatta_admin_players has them: a
--           Telegram user, a site account or, for a guest, a browser; a browser that later signed in is that player.
--   report: for `person` (a `who` of people or of regatta_admin_players), their visits (100 at most) and their races (200
--           at most), the latest first, with all that was kept of each but the result page's record. null without one.

create or replace function public.regatta_admin_logs(days int default 30, person text default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  n_days int := greatest(1, least(coalesce(days, 30), 365));
  since timestamptz := now() - make_interval(days => n_days);
  answer jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;
  with ids as (   -- a browser's later sign-in: its races name both
    select distinct on (vid) vid, user_id, player
      from public.game_races where vid is not null and (user_id is not null or player is not null) order by vid, started_at desc
  ), all_races as (
    select g.*, coalesce(g.user_id::text, g.player::text, i.user_id::text, i.player::text, g.vid::text) as who,
           case when jsonb_typeof(g.perf -> 'fps') = 'number' then (g.perf ->> 'fps')::real < 24 else false end as is_slow,
           coalesce(g.rating <= 2, false) as is_low
      from public.game_races g left join ids i on i.vid = g.vid and g.user_id is null and g.player is null
  ), by_visit as (   -- the player a visit raced as, before the one its browser came to be
    select distinct on (visit) visit, who from all_races where visit is not null and who is not null order by visit, started_at desc
  ), all_visits as (
    select v.*, coalesce(b.who, i.user_id::text, i.player::text, v.vid::text, v.id::text) as who,
           v.failed_at is not null as is_failed, v.gave_up_at is not null as is_gave, coalesce(v.lost, 0) = 1 as is_lost,
           case when jsonb_typeof(v.errors) = 'array' then jsonb_array_length(v.errors) > 0 else false end as is_err
      from public.game_visits v left join by_visit b on b.visit = v.id left join ids i on i.vid = v.vid
  ), v_sum as (
    select who, count(*) as n,
           count(*) filter (where is_failed or is_gave or is_lost or is_err) as bad,
           count(*) filter (where is_failed) as failed, count(*) filter (where is_gave) as gave_up,
           count(*) filter (where is_lost) as lost, count(*) filter (where is_err) as errs,
           max(coalesce(failed_at, gave_up_at, last_at, opened_at)) filter (where is_failed or is_gave or is_lost or is_err) as at,
           (array_agg(dev || case when tg = 1 then ' tg' else '' end order by opened_at desc) filter (where dev is not null))[1] as dev
      from all_visits where opened_at >= since group by who
  ), r_sum as (
    select who, count(*) filter (where is_slow) as slow, count(*) filter (where is_low) as low,
           max(started_at) filter (where is_slow or is_low) as at
      from all_races where who is not null and started_at >= since group by who
  ), people as (
    select who, coalesce(v.n, 0) as visits, coalesce(v.bad, 0) as bad, coalesce(v.failed, 0) as failed, coalesce(v.gave_up, 0) as gave_up,
           coalesce(v.lost, 0) as lost, coalesce(v.errs, 0) as errs, coalesce(r.slow, 0) as slow, coalesce(r.low, 0) as low,
           greatest(v.at, r.at) as last_at, v.dev
      from v_sum v full join r_sum r using (who)
     where coalesce(v.bad, 0) + coalesce(r.slow, 0) + coalesce(r.low, 0) > 0
  ), shown as (
    select * from people order by last_at desc nulls last limit 200
  ), labels as (
    select p.who,
           case when u.id is not null or p.who ~ '^\d{1,18}$' then 'tg' when a.id is not null then 'acct' else 'guest' end as kind,
           coalesce(u.name, nullif(a.raw_user_meta_data ->> 'display_name', '')) as name,
           coalesce(u.username, a.email) as handle
      from (select who from shown union select person where person is not null) p
      left join public.users u on u.id = case when p.who ~ '^\d{1,18}$' then p.who::bigint end
      left join auth.users a on a.id = case when p.who ~ '^[0-9a-fA-F-]{36}$' then p.who::uuid end
  )
  select jsonb_build_object(
    'since', since,
    'totals', jsonb_build_object(
      'visits', (select count(*) from all_visits where opened_at >= since),
      'bad', (select coalesce(sum(bad), 0) from people), 'failed', (select coalesce(sum(failed), 0) from people),
      'gave_up', (select coalesce(sum(gave_up), 0) from people), 'lost', (select coalesce(sum(lost), 0) from people),
      'errors', (select coalesce(sum(errs), 0) from people), 'slow', (select coalesce(sum(slow), 0) from people),
      'low', (select coalesce(sum(low), 0) from people), 'people', (select count(*) from people)),
    'people', coalesce((select jsonb_agg(jsonb_build_object(
        'who', s.who, 'kind', l.kind, 'name', l.name, 'handle', l.handle, 'last', s.last_at, 'visits', s.visits, 'bad', s.bad,
        'failed', s.failed, 'gave_up', s.gave_up, 'lost', s.lost, 'errors', s.errs, 'slow', s.slow, 'low', s.low, 'dev', s.dev
      ) order by s.last_at desc nulls last) from shown s join labels l using (who)), '[]'::jsonb),
    'report', case when person is null then null else jsonb_build_object(
      'who', person,
      'kind', (select kind from labels where who = person), 'name', (select name from labels where who = person),
      'handle', (select handle from labels where who = person),
      'first', least((select min(opened_at) from all_visits where who = person), (select min(started_at) from all_races where who = person)),
      'last', greatest((select max(opened_at) from all_visits where who = person), (select max(started_at) from all_races where who = person)),
      'visits', coalesce((select jsonb_agg(to_jsonb(x) order by x.at desc) from (
        select id, opened_at as at, kind, ref, tg, dev, load, loaded_at, failed_at, why, gave_up_at, pct, last_at, races, finished, mins,
               howto, drill, ghost, lost, errors
          from all_visits where who = person and opened_at >= since order by opened_at desc limit 100) x), '[]'::jsonb),
      'races', coalesce((select jsonb_agg(to_jsonb(x) order by x.at desc) from (
        select id, visit, started_at as at, finished_at, wind, laps, length, boats, place, secs, dsq, daily, shape, yacht, venue, perf, ended, rating, comment
          from all_races where who = person and started_at >= since order by started_at desc limit 200) x), '[]'::jsonb)
    ) end
  ) into answer;
  return answer;
end $$;

revoke all on function public.regatta_admin_logs(int, text) from public, anon;
grant execute on function public.regatta_admin_logs(int, text) to authenticated;
