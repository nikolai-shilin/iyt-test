-- The game card's numbers in one question (api/game.mjs GET /api/game, ryc-regatta's lib/today.ts and Home): what the
-- API worked out from every race of the last 30 days, read a thousand at a time (seven round trips on 25 November, half
-- a second, and more each day), worked out here instead (api/game.mjs gameCard is the same reckoning in JavaScript,
-- kept for before this migration and for the tests).
--
-- regatta_game_card() →
--   { week: { races, players },
--     best: { w, l, c, n, sh, top: [ { u, a, s, p, fl } ] } | null,
--     daily: { d, w, sh, races, top: [ { u, a, s, p, fl } ] } | null }
-- week: races started in the last 7 days and their players (every guest together counts as one). best: the free course
-- (wind, laps, length, boats, shape) most finished on in the last 30 days, ties to the shape first in wl, tri, trap,
-- wlu, then to the one raced latest; its 3 fastest by their best time without a disqualification, guests counted as one
-- player. daily: today's (UTC) daily race: its wind (that of its first finish), its shape (the one most of its finishes
-- name, else wl), its finishes and its 3 fastest, guests left out. A top's player: u their Telegram id, a their account
-- id (for one without Telegram), s the best time, p the best place, fl the flag of their latest race of the 30 days;
-- equal times go to the one who raced latest. Names and pictures are the API's to add. Only the scores API asks (the
-- service role).

create function public.regatta_game_card()
returns jsonb language sql stable security definer set search_path = '' as $$
  with r as (
    select coalesce(user_id::text, 'a:' || player::text, 'anon') as k, user_id, player, started_at, finished_at, wind,
      coalesce(laps, 1) as laps, length, boats, secs, dsq, place, daily, shape, flag
    from public.game_races
    where started_at >= now() - interval '30 days'
  ),
  fin as (select * from r where finished_at is not null and not dsq and secs > 0),
  fl as (select distinct on (k) k, flag from r order by k, started_at desc),
  courses as (
    select wind, laps, length, boats, coalesce(shape, 'wl') as sh, count(*) as races, max(started_at) as last
    from fin
    where length is not null and boats is not null and daily is null
    group by 1, 2, 3, 4, 5
  ),
  course as (
    select * from courses
    order by races desc, coalesce(array_position(array['wl', 'tri', 'trap', 'wlu'], sh), 0), last desc
    limit 1
  ),
  cbest as (
    select f.k, min(f.secs) as s, min(f.place) as p, max(f.started_at) as last
    from fin f
    join course c on f.wind is not distinct from c.wind and f.laps = c.laps and f.length = c.length and f.boats = c.boats
      and coalesce(f.shape, 'wl') = c.sh
    where f.daily is null
    group by f.k
  ),
  drows as (select * from fin where daily = (now() at time zone 'utc')::date),
  dbest as (
    select k, min(secs) as s, min(place) as p, max(started_at) as last
    from drows where k <> 'anon' group by k
  ),
  dshape as (
    select shape from drows where shape is not null group by shape
    order by count(*) desc, coalesce(array_position(array['wl', 'tri', 'trap', 'wlu'], shape), 0), max(started_at) desc
    limit 1
  )
  select jsonb_build_object(
    'week', (select jsonb_build_object('races', count(*), 'players', count(distinct k)) from r where started_at >= now() - interval '7 days'),
    'best', (
      select jsonb_build_object('w', c.wind, 'l', c.laps, 'c', c.length, 'n', c.boats, 'sh', c.sh, 'top', (
        select coalesce(jsonb_agg(x.o order by x.s, x.last desc), '[]'::jsonb)
        from (
          select b.s, b.last, jsonb_build_object(
            'u', case when b.k ~ '^[0-9]+$' then b.k::bigint end, 'a', case when b.k like 'a:%' then substr(b.k, 3) end,
            's', b.s, 'p', b.p, 'fl', fl.flag) as o
          from cbest b left join fl using (k)
          order by b.s, b.last desc limit 3
        ) x))
      from course c),
    'daily', case when exists (select 1 from drows) then jsonb_build_object(
      'd', to_char((now() at time zone 'utc')::date, 'YYYY-MM-DD'),
      'w', (select wind from drows order by started_at limit 1),
      'sh', coalesce((select shape from dshape), 'wl'),
      'races', (select count(*) from drows),
      'top', (
        select coalesce(jsonb_agg(x.o order by x.s, x.last desc), '[]'::jsonb)
        from (
          select b.s, b.last, jsonb_build_object(
            'u', case when b.k ~ '^[0-9]+$' then b.k::bigint end, 'a', case when b.k like 'a:%' then substr(b.k, 3) end,
            's', b.s, 'p', b.p, 'fl', fl.flag) as o
          from dbest b left join fl using (k)
          order by b.s, b.last desc limit 3
        ) x)) end
  )
$$;

revoke all on function public.regatta_game_card() from public, anon, authenticated;
grant execute on function public.regatta_game_card() to service_role;
