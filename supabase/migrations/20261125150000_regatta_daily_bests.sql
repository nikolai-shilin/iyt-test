-- Each player's best of each day of the daily race between two days (api/game.mjs playerMonth, GET ?month=&k=): what
-- the API added up itself from every finished daily race of the month (bests), read a thousand at a time (two round
-- trips and some 1,850 rows on 25 November), added up here instead. The points are still worked out by api/game.mjs
-- (rankDay, monthTable), as for regatta_players' days.
--
-- regatta_daily_bests(since, until) → [ { d, u, a, s, p, n, at, fl } ]: for each day d from since to until and each
-- player who is somebody (guests are never ranked) with a finished race on it (no disqualification, a time): u their
-- Telegram id, a their account id (for one without Telegram, as api/game.mjs who() keys them), s their best time, p
-- their best place (null for none), n the races they finished, at their latest start that day and fl that race's flag
-- (for the flag they fly when they have no race in the last 30 days). Only the scores API asks (the service role).

create function public.regatta_daily_bests(since date, until date)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('d', to_char(x.d, 'YYYY-MM-DD'), 'u', x.u, 'a', x.a, 's', x.s, 'p', x.p, 'n', x.n, 'at', x.at, 'fl', x.fl)
                            order by x.d, x.at desc), '[]'::jsonb)
  from (
    select daily as d, min(user_id) as u, case when min(user_id) is null then min(player::text) end as a,
      min(secs) as s, min(place) as p, count(*) as n, max(started_at) as at,
      (array_agg(flag order by started_at desc))[1] as fl
    from public.game_races
    where daily between since and until and finished_at is not null and not dsq and secs > 0
      and (user_id is not null or player is not null)
    group by daily, coalesce(user_id::text, 'a:' || player::text)
  ) x
$$;

revoke all on function public.regatta_daily_bests(date, date) from public, anon, authenticated;
grant execute on function public.regatta_daily_bests(date, date) to service_role;
