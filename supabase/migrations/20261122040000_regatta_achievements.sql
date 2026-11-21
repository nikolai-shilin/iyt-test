-- Achievements (release 7c of the 1-on-1 plan; the ryc-regatta repo: lib/achievements.ts names and words them,
-- components/achievements.tsx shows them on your player card). Each is a rule over what the database already holds: the
-- account's races (game_races: a site account's by its id in player, a Telegram account's by its Telegram id in
-- user_id), its log of today's race and the venues (auth.users user_metadata.log, which the site merges from every
-- device), and its 1-on-1 races and rating (regatta_duels, regatta_rating_change). The day each came is worked out from
-- that history and kept in regatta_achievement the first time it is seen, so every device shows the same ones on the
-- same days, and one once had is never lost.
--
-- regatta_achievements(): for the signed-in sailor, the rules run, new ones kept, and back: got (each key, the day it
-- came, a detail) and progress (for each not yet had that has a count: [have, need]).
--   today's race: first_race (a race finished), podium (top three of a day's ranking, ranked as the scores server ranks
--     it: each sailor's best, equal times sharing the better place), day_winner (first), week and month (a streak of 7
--     and 30 days as the site counts it: one day missed doesn't break it, two in a row do)
--   venues: venues_10 and venues_33 (raced at 10, and at 33 of the 66)
--   1-on-1: first_duel (one finished), first_win (a rated win), settled (five rated races), giant (a rated win over a
--     sailor 200 or more above), run_5 (five rated wins in a row), regional (1600 once settled), rival (ahead in the
--     head-to-head with a sailor raced ten times), hour_5 (1-on-1s on five days' duel hours, 19:00–20:00 UTC)

create table public.regatta_achievement (
  user_id uuid not null references auth.users (id) on delete cascade,
  key text not null,
  at timestamptz not null,
  detail jsonb not null default '{}'::jsonb,
  primary key (user_id, key)
);
alter table public.regatta_achievement enable row level security;
revoke all on public.regatta_achievement from public, anon, authenticated;

create function public.regatta_achievements()
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  meta jsonb;
  tg bigint;
  mykey text;
  best_run int := 0;
  venues int := 0;
  rated int := 0;
  rating int := 1500;
  win_run int := 0;
  most_met int := 0;
  hours int := 0;
begin
  if me is null then return null; end if;
  select a.raw_user_meta_data, case when a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,15}$' then (a.raw_app_meta_data ->> 'telegram_id')::bigint end
    into meta, tg from auth.users a where a.id = me;
  mykey := case when tg is not null then tg::text else 'a:' || me::text end;

  -- today's race and every race: the account's own races, and the days they finished today's race
  create temp table if not exists ach_mine (daily date, finished_at timestamptz, secs real) on commit drop;
  truncate pg_temp.ach_mine;
  insert into pg_temp.ach_mine select r.daily, r.finished_at, r.secs from public.game_races r
   where (case when tg is not null then r.user_id = tg else r.user_id is null and r.player = me end)
     and r.finished_at is not null and not coalesce(r.dsq, false) and r.secs > 0;

  insert into public.regatta_achievement (user_id, key, at)
    select me, 'first_race', min(m.finished_at) from pg_temp.ach_mine m having count(*) > 0
  on conflict do nothing;

  -- each day they ranked: their place, as the scores server ranks the day (keyed players' bests; equal times share)
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, k, (x.daily + time '12:00') at time zone 'UTC', jsonb_build_object('day', x.daily, 'place', x.place, 'of', x.n)
      from (
        select distinct on (k) k, y.daily, y.place, y.n
          from (
            select b.daily, b.who, rank() over (partition by b.daily order by b.s) as place, count(*) over (partition by b.daily) as n
              from (select r.daily, coalesce(r.user_id::text, 'a:' || r.player::text) as who, min(r.secs) as s
                      from public.game_races r
                     where r.daily in (select distinct m.daily from pg_temp.ach_mine m where m.daily is not null)
                       and r.finished_at is not null and not coalesce(r.dsq, false) and r.secs > 0 and (r.user_id is not null or r.player is not null)
                     group by 1, 2) b
          ) y
          cross join lateral (values ('podium', 3), ('day_winner', 1)) v(k, top)
         where y.who = mykey and y.place <= v.top
         order by k, y.daily
      ) x
  on conflict do nothing;

  -- the streak: the days of today's race (the log's, and the races'), in runs where no two days in a row are missed
  with days as (
    select distinct d::date as d from (
      select jsonb_object_keys(case when jsonb_typeof(meta -> 'log' -> 'd') = 'object' then meta -> 'log' -> 'd' else '{}'::jsonb end) as d
      union select m.daily::text from pg_temp.ach_mine m where m.daily is not null) x
    where d ~ '^\d{4}-\d{2}-\d{2}$'),
  gaps as (select d, case when d - lag(d) over (order by d) <= 2 then 0 else 1 end as starts from days),
  runs as (select d, sum(starts) over (order by d) as run from gaps),
  numbered as (select d, row_number() over (partition by run order by d) as n from runs),
  hits as (insert into public.regatta_achievement (user_id, key, at, detail)
             select me, v.k, (min(x.d) + time '12:00') at time zone 'UTC', jsonb_build_object('days', v.need)
               from numbered x cross join (values ('week', 7), ('month', 30)) v(k, need)
              where x.n = v.need group by v.k, v.need
           on conflict do nothing returning 1)
  select coalesce(max(n), 0) into best_run from numbered;

  -- the venues: the log's first race at each
  with v as (
    select (e.value)::text::numeric::bigint as ms from jsonb_each(case when jsonb_typeof(meta -> 'log' -> 'v') = 'object' then meta -> 'log' -> 'v' else '{}'::jsonb end) e
     where jsonb_typeof(e.value) = 'number'),
  o as (select ms, row_number() over (order by ms) as n from v)
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, 'venues_' || x.need, to_timestamp(o.ms / 1000.0), jsonb_build_object('venues', x.need)
      from o join (values (10), (33)) x(need) on o.n = x.need
  on conflict do nothing;
  select count(*) into venues from jsonb_object_keys(case when jsonb_typeof(meta -> 'log' -> 'v') = 'object' then meta -> 'log' -> 'v' else '{}'::jsonb end);

  -- 1-on-1: the races they finished, and the rated ones' changes
  insert into public.regatta_achievement (user_id, key, at)
    select me, 'first_duel', min(d.started_at) from public.regatta_duels d
     where (d.host_user = me or d.guest_user = me) and d.state = 'finished' having count(*) > 0
  on conflict do nothing;
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, 'first_win', c.at, jsonb_build_object('them', case when d.host_user = me then d.guest_name else d.host_name end, 'rating', c.opponent_before)
      from public.regatta_rating_change c join public.regatta_duels d on d.id = c.duel_id
     where c.user_id = me and c.won order by c.at limit 1
  on conflict do nothing;
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, 'settled', c.at, jsonb_build_object('rating', c.after) from public.regatta_rating_change c
     where c.user_id = me and c.races_before = 4 order by c.at limit 1
  on conflict do nothing;
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, 'giant', c.at, jsonb_build_object('them', case when d.host_user = me then d.guest_name else d.host_name end, 'rating', c.opponent_before, 'gap', c.opponent_before - c.before)
      from public.regatta_rating_change c join public.regatta_duels d on d.id = c.duel_id
     where c.user_id = me and c.won and c.opponent_before - c.before >= 200 order by c.at limit 1
  on conflict do nothing;
  insert into public.regatta_achievement (user_id, key, at, detail)
    select me, 'regional', c.at, jsonb_build_object('rating', c.after) from public.regatta_rating_change c
     where c.user_id = me and c.races_before >= 4 and c.after >= 1600 order by c.at limit 1
  on conflict do nothing;
  with w as (select c.at, c.won, sum(case when c.won then 0 else 1 end) over (order by c.at) as grp from public.regatta_rating_change c where c.user_id = me),
  r as (select at, won, row_number() over (partition by grp order by at) - case when bool_or(not won) over (partition by grp) then 1 else 0 end as n from w),
  hits as (insert into public.regatta_achievement (user_id, key, at, detail)
             select me, 'run_5', min(r.at), jsonb_build_object('wins', 5) from r where r.won and r.n = 5 having count(*) > 0
           on conflict do nothing returning 1)
  select coalesce(max(n), 0) into win_run from r where won;
  select count(*) into rated from public.regatta_rating_change c where c.user_id = me;
  select coalesce((select r.rating from public.regatta_rating r where r.user_id = me), 1500) into rating;

  -- the head-to-head: finished races with a winner against another account, in order; ten met and ahead
  with h as (
    select case when d.host_user = me then d.guest_user else d.host_user end as them,
           case when d.host_user = me then d.guest_name else d.host_name end as name, d.started_at,
           (d.winner = case when d.host_user = me then 'host' else 'guest' end) as won
      from public.regatta_duels d
     where (d.host_user = me or d.guest_user = me) and d.state = 'finished' and d.winner is not null
       and d.host_user is not null and d.guest_user is not null and d.host_user <> d.guest_user),
  c as (select them, name, started_at, count(*) over (partition by them order by started_at) as met,
               sum(case when won then 1 else -1 end) over (partition by them order by started_at) as lead from h),
  hits as (insert into public.regatta_achievement (user_id, key, at, detail)
             select me, 'rival', c.started_at, jsonb_build_object('them', c.name, 'met', c.met) from c
              where c.met >= 10 and c.lead > 0 order by c.started_at limit 1
           on conflict do nothing returning 1)
  select coalesce(max(cnt), 0) into most_met from (select count(*) as cnt from h group by them) x;

  -- the duel hour: days with a finished 1-on-1 begun between 19:00 and 20:00 UTC
  with hd as (select (d.started_at at time zone 'UTC')::date as day, min(d.started_at) as at from public.regatta_duels d
               where (d.host_user = me or d.guest_user = me) and d.state = 'finished'
                 and extract(hour from d.started_at at time zone 'UTC') = 19 group by 1),
  o as (select at, row_number() over (order by day) as n from hd),
  hits as (insert into public.regatta_achievement (user_id, key, at, detail)
             select me, 'hour_5', o.at, jsonb_build_object('hours', 5) from o where o.n = 5
           on conflict do nothing returning 1)
  select count(*) into hours from hd;

  return jsonb_build_object(
    'got', (select coalesce(jsonb_agg(jsonb_build_object('key', a.key, 'at', a.at, 'detail', a.detail) order by a.at), '[]'::jsonb)
              from public.regatta_achievement a where a.user_id = me),
    'progress', jsonb_build_object('week', jsonb_build_array(least(best_run, 7), 7), 'month', jsonb_build_array(least(best_run, 30), 30),
      'venues_10', jsonb_build_array(least(venues, 10), 10), 'venues_33', jsonb_build_array(least(venues, 33), 33),
      'settled', jsonb_build_array(least(rated, 5), 5), 'run_5', jsonb_build_array(least(win_run, 5), 5),
      'regional', case when rated >= 5 then jsonb_build_array(least(rating, 1600), 1600) end,
      'rival', jsonb_build_array(least(most_met, 10), 10), 'hour_5', jsonb_build_array(least(hours, 5), 5)));
end $$;
revoke all on function public.regatta_achievements() from public, anon;
grant execute on function public.regatta_achievements() to authenticated;
