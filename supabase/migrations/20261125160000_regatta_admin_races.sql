-- The Regatta races for the admins' Overview page (api/admin.mjs gameRaces) in one question: the page read every race
-- of the last 91 days a thousand at a time, one page after another (seven round trips and some 1.3 MB on 25 November,
-- and more each day, up to 20,000 races), and made each one the short record the app counts. This makes the same
-- records here.
--
-- regatta_admin_races(days) → [ { at, u, w, l, c, f, p, n, s, d, sh } ], the races started in the last `days` days
-- (1 to 366), the latest first, at most 20,000: at = when it started (ms since 1970), u = the Telegram user (null: not
-- in Telegram), w = the wind, l = laps, c = the course length, f = when the player finished (ms, 0 = not finished),
-- p = their place, n = boats in the race, s = their time (s), d = disqualified, sh = the course's shape ('wl' for a race
-- from before it was kept). The same as api/admin.mjs header says. Only the admin API asks (the service role).

create function public.regatta_admin_races(days int default 91)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object(
      'at', floor(extract(epoch from x.started_at) * 1000)::bigint, 'u', x.user_id, 'w', x.wind, 'l', x.laps, 'c', x.length,
      'f', coalesce(floor(extract(epoch from x.finished_at) * 1000)::bigint, 0), 'p', x.place, 'n', x.boats, 's', x.secs,
      'd', coalesce(x.dsq, false), 'sh', coalesce(x.shape, 'wl'))
    order by x.started_at desc), '[]'::jsonb)
  from (
    select started_at, finished_at, user_id, wind, laps, length, place, boats, secs, dsq, shape
    from public.game_races
    where started_at >= now() - make_interval(days => greatest(1, least(coalesce(days, 91), 366)))
    order by started_at desc
    limit 20000
  ) x
$$;

revoke all on function public.regatta_admin_races(int) from public, anon, authenticated;
grant execute on function public.regatta_admin_races(int) to service_role;
