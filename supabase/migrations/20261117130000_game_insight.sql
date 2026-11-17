-- The Regatta game: what tells how the players like it, for the site's /admin (the ryc-regatta repo: components/admin-insight.tsx).
--
-- game_races, new columns (api/game.mjs writes them):
--   vid: the browser's random id (localStorage), so a guest who comes back another day counts once; visit: the page's
--     opening the race was begun in (game_visits.id). Neither names anyone.
--   ended: how the race ended for the player (ev 'end'): how ('finish', 'restart', 'change' to the set-up, 'menu' back
--     to the hub, 'close' the page left, 'hidden' put away, 'new' another begun), leg and legs, clock, place and boats,
--     done, inc (the incidents the race said: ocs, touched, aground …, counted), last and ago (the last of them and
--     how many seconds before), pens, mins (the minutes it lasted), use (what the player had set: cam, trim, sound …).
--   rating (1–5) and comment: how the player liked it, asked on the result page.
-- game_visits: one row a page opened (ev 'open', then ev 'visit'): the browser (vid), where from (ref), which race
--   (kind), Telegram, the device; when it loaded (and the seconds it took), failed (and why) or was given up while
--   loading (and how far it had got); the races begun and finished, the minutes on the page, how to play opened, a
--   drill, a ghost, its first errors and a lost WebGL context.
--
-- regatta_admin_insight(days): for a regatta admin alone (is_regatta_admin()), the last `days` (1–365):
--   exits: the races by how they ended; those left before the finish by how far they had got (stage), and by the last
--     incident if it came in the minute before; the minutes a race lasted (median, finished and left).
--   retention: the players first seen in each of the last days (a player: a Telegram user, a site account or a
--     browser; one who signed in later is still their browser before that) and how many came back on a later day: the
--     next day (d1), within 7 (d7) and 30 (d30) — each counted only over those first seen long enough ago.
--   ratings: how many, the average, each star's count, the average by yacht, and the latest 30 comments.
--   funnel: the visits opened, loaded, failed, given up while loading, that began a race and finished one; by device;
--     the median seconds to load, minutes on the page and races a visit; the reasons a load failed; the errors most
--     seen; how to play opened, drills and ghosts.
--   usage: what the players had set as their races ended, each setting's values counted.
--   difficulty: the races by how many each player had sailed before (the 1st, the 2nd–5th, 6th–20th, 21st on): finished,
--     top three, disqualified, the median place down the fleet and penalties.

alter table public.game_races add column if not exists vid uuid;
alter table public.game_races add column if not exists visit uuid;
alter table public.game_races add column if not exists ended jsonb check (jsonb_typeof(ended) = 'object' and length(ended::text) < 2000);
alter table public.game_races add column if not exists rating smallint check (rating between 1 and 5);
alter table public.game_races add column if not exists comment text check (length(comment) <= 500);
create index if not exists game_races_vid on public.game_races (vid) where vid is not null;

create table if not exists public.game_visits (
  id          uuid primary key,
  vid         uuid,
  opened_at   timestamptz not null default now(),
  ref         text check (ref in ('tg', 'site', 'other', 'direct')),
  kind        text check (kind in ('today', 'free', 'match', 'drill')),
  tg          smallint check (tg in (0, 1)),
  dev         text check (dev in ('phone', 'tablet', 'desktop')),
  loaded_at   timestamptz,
  load        real check (load >= 0 and load <= 3600),
  failed_at   timestamptz,
  why         text check (length(why) <= 140),
  gave_up_at  timestamptz,
  pct         smallint check (pct between 0 and 100),
  last_at     timestamptz,
  races       int check (races between 0 and 9999),
  finished    int check (finished between 0 and 9999),
  mins        real check (mins >= 0 and mins <= 1440),
  howto       smallint check (howto = 1),
  drill       smallint check (drill = 1),
  ghost       smallint check (ghost = 1),
  lost        smallint check (lost = 1),
  errors      jsonb check (jsonb_typeof(errors) = 'array' and length(errors::text) < 2000)
);
create index if not exists game_visits_opened_at on public.game_visits (opened_at);
create index if not exists game_visits_vid on public.game_visits (vid) where vid is not null;
alter table public.game_visits enable row level security;   -- no policies: only the server (secret key) reads and writes it
grant all on public.game_visits to service_role;

create or replace function public.regatta_admin_insight(days int default 30)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  n_days int := greatest(1, least(coalesce(days, 30), 365));
  since timestamptz := now() - make_interval(days => n_days);
  out jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;
  with races as (
    select g.*, coalesce(g.user_id::text, g.player::text, g.vid::text) as who,
           g.ended ->> 'how' as how, (g.ended ->> 'leg')::int as leg, (g.ended ->> 'legs')::int as legs,
           (g.ended ->> 'ago')::real as ago, g.ended ->> 'last' as last, (g.ended ->> 'mins')::real as mins, (g.ended ->> 'pens')::int as pens
      from public.game_races g
  ), recent as (
    select * from races where started_at >= since
  ), left_early as (
    select *, case when leg is null or legs is null then 'unknown' when leg = 0 then 'before the start'
                   when leg = 1 then 'first leg' when leg >= legs then 'last leg' else 'middle legs' end as stage
      from recent where finished_at is null and how is not null and how <> 'finish'
  ),
  -- a browser's later sign-in: its races name both, so its visits count as that player
  ids as (
    select distinct on (vid) vid, coalesce(user_id::text, player::text) as who
      from public.game_races where vid is not null and coalesce(user_id::text, player::text) is not null order by vid, started_at desc
  ), activity as (
    select distinct who, started_at::date as d from races where who is not null
    union
    select distinct coalesce(i.who, v.vid::text), v.opened_at::date from public.game_visits v left join ids i on i.vid = v.vid where v.vid is not null
  ), firsts as (
    select who, min(d) as d0 from activity group by who
  ), cohort as (
    select f.who, f.d0,
           exists (select 1 from activity a where a.who = f.who and a.d = f.d0 + 1) as d1,
           exists (select 1 from activity a where a.who = f.who and a.d > f.d0 and a.d <= f.d0 + 7) as d7,
           exists (select 1 from activity a where a.who = f.who and a.d > f.d0 and a.d <= f.d0 + 30) as d30
      from firsts f where f.d0 >= since::date
  ), ordinal as (
    select r.*, row_number() over (partition by r.who order by r.started_at) as nth from races r where r.who is not null
  ), visits as (
    select v.*, coalesce(v.races, 0) > 0 or exists (select 1 from public.game_races g where g.visit = v.id) as raced from public.game_visits v where v.opened_at >= since
  )
  select jsonb_build_object(
    'since', since,
    'exits', jsonb_build_object(
      'how', coalesce((select jsonb_object_agg(k, n) from (select coalesce(case when finished_at is not null then 'finish' else how end, 'unknown') as k, count(*) as n from recent group by 1) x), '{}'::jsonb),
      'stage', coalesce((select jsonb_object_agg(stage, n) from (select stage, count(*) as n from left_early group by 1) x), '{}'::jsonb),
      'last', coalesce((select jsonb_object_agg(last, n) from (select last, count(*) as n from left_early where last is not null and ago <= 60 group by 1) x), '{}'::jsonb),
      'left', (select count(*) from left_early),
      'mins_left', (select percentile_cont(0.5) within group (order by mins) from left_early),
      'mins_fin', (select percentile_cont(0.5) within group (order by mins) from recent where finished_at is not null)
    ),
    'retention', jsonb_build_object(
      'new', (select count(*) from cohort),
      'd1', (select count(*) filter (where d1) from cohort where d0 <= current_date - 1), 'd1of', (select count(*) from cohort where d0 <= current_date - 1),
      'd7', (select count(*) filter (where d7) from cohort where d0 <= current_date - 7), 'd7of', (select count(*) from cohort where d0 <= current_date - 7),
      'd30', (select count(*) filter (where d30) from cohort where d0 <= current_date - 30), 'd30of', (select count(*) from cohort where d0 <= current_date - 30),
      'back', (select count(distinct a.who) from activity a join firsts f using (who) where a.d >= since::date and a.d > f.d0),
      'active', (select count(distinct who) from activity where d >= since::date)
    ),
    'ratings', jsonb_build_object(
      'n', (select count(rating) from recent), 'avg', (select avg(rating) from recent),
      'stars', (select jsonb_build_array(count(*) filter (where rating = 1), count(*) filter (where rating = 2), count(*) filter (where rating = 3), count(*) filter (where rating = 4), count(*) filter (where rating = 5)) from recent),
      'yacht', coalesce((select jsonb_object_agg(y, jsonb_build_object('n', n, 'avg', a)) from (select coalesce(yacht, 'jpk1050') as y, count(rating) as n, avg(rating) as a from recent where rating is not null group by 1) x), '{}'::jsonb),
      'comments', coalesce((select jsonb_agg(c order by at desc) from (
          select jsonb_build_object('at', started_at, 'rating', rating, 'comment', comment, 'yacht', coalesce(yacht, 'jpk1050'), 'venue', venue, 'wind', wind,
                                    'place', place, 'boats', boats, 'dsq', dsq, 'dev', perf ->> 'dev', 'how', how) as c, started_at as at
            from recent where comment is not null order by started_at desc limit 30) x), '[]'::jsonb)
    ),
    'funnel', jsonb_build_object(
      'opened', (select count(*) from visits), 'loaded', (select count(loaded_at) from visits), 'failed', (select count(failed_at) from visits where loaded_at is null),
      'gave_up', (select count(*) from visits where loaded_at is null and failed_at is null and gave_up_at is not null),
      'raced', (select count(*) from visits where raced), 'finished', (select count(*) from visits where finished > 0),
      'load', (select percentile_cont(0.5) within group (order by load) from visits), 'mins', (select percentile_cont(0.5) within group (order by mins) from visits where loaded_at is not null),
      'races', (select percentile_cont(0.5) within group (order by races) from visits where loaded_at is not null),
      'dev', coalesce((select jsonb_object_agg(coalesce(dev, '?') || case when tg = 1 then ' tg' else '' end, jsonb_build_object('opened', n, 'loaded', l, 'gave_up', g, 'failed', f, 'raced', r))
                         from (select dev, tg, count(*) as n, count(loaded_at) as l, count(*) filter (where loaded_at is null and failed_at is null and gave_up_at is not null) as g,
                                      count(failed_at) filter (where loaded_at is null) as f, count(*) filter (where raced) as r from visits group by 1, 2) x), '{}'::jsonb),
      'why', coalesce((select jsonb_agg(jsonb_build_object('why', why, 'n', n) order by n desc) from (select why, count(*) as n from visits where why is not null group by 1 order by 2 desc limit 10) x), '[]'::jsonb),
      'errors', coalesce((select jsonb_agg(jsonb_build_object('m', m, 'src', src, 'n', n, 'visits', v) order by v desc, n desc) from (
          select e ->> 'm' as m, e ->> 'src' as src, sum((e ->> 'n')::int) as n, count(*) as v from visits, jsonb_array_elements(coalesce(errors, '[]'::jsonb)) e group by 1, 2 order by 4 desc, 3 desc limit 15) x), '[]'::jsonb),
      'lost', (select count(lost) from visits), 'howto', (select count(howto) from visits), 'drill', (select count(drill) from visits), 'ghost', (select count(ghost) from visits)
    ),
    'usage', coalesce((select jsonb_object_agg(k, vals) from (
        select k, jsonb_object_agg(v, n) as vals from (
          select u.key as k, u.value as v, count(*) as n from recent, jsonb_each_text(coalesce(ended -> 'use', '{}'::jsonb)) u group by 1, 2) y group by k) x), '{}'::jsonb),
    'difficulty', coalesce((select jsonb_agg(to_jsonb(x) order by x.b) from (
        select case when nth = 1 then 1 when nth <= 5 then 2 when nth <= 20 then 3 else 4 end as b, count(*) as n, count(finished_at) as fin,
               count(*) filter (where place <= 3) as top3, count(*) filter (where dsq) as dsq, count(distinct who) as who,
               percentile_cont(0.5) within group (order by (place - 1)::real / greatest(boats - 1, 1)) as down,
               avg(pens) filter (where finished_at is not null) as pens
          from ordinal where started_at >= since group by 1) x), '[]'::jsonb)
  ) into out;
  return out;
end $$;

revoke all on function public.regatta_admin_insight(int) from public, anon;
grant execute on function public.regatta_admin_insight(int) to authenticated;
