-- The Regatta game's races, for the site's /admin (the ryc-regatta repo: app/[lang]/admin, components/admin-stats.tsx):
-- where each race was sailed, how the game ran through it, and the numbers the page shows, summed up here.
--
--   venue: the race's venue (public/game/venues.js there: 'gocek', 'cowes' …), posted with the start (api/game.mjs).
--     A race from before the column is null.
--   perf: how the game ran (posted once a race, ev 'perf', checked by api/game.mjs perfOf): fps the middle frame's
--     rate and low the slow end's (the 95th percentile frame), stall the frames over 100 ms a minute, secs measured;
--     q0 and q the graphics level at the start and the end, gfx the setting (auto or a level), saver the battery
--     saver; dev (phone, tablet, desktop), tg (in Telegram), os, br (browser), dpr, cores, mem, gpu (the chip as WebGL
--     names it), w and h the size drawn, load the seconds from opening the page to the first race. It names no one.
--
-- regatta_admin_stats(days): for a regatta admin only (is_regatta_admin(), as the page's other settings), the races
-- started in the last `days` (1–365): per UTC day, and grouped by the class of yacht, the wind, the venue, the
-- course's shape, today's race or a free one, the device, the graphics chip, the level, the system and the browser,
-- and all of them together ('all'). Each group: races (n), finished (fin), disqualified (dsq), in the first three
-- (top3), players (who: a Telegram user or a site account; guests are one), the median fleet place as a share of the
-- way down it (0 first … 1 last), and of the races with a perf: how many (np), the median fps, low, stalls a minute
-- and load, how many under 30 fps (slow), the share with the battery saver on, and the level they ended on (high,
-- medium, low). A key not known (an old race's venue) is null.

alter table public.game_races add column if not exists venue text check (venue ~ '^[a-z][a-z0-9-]{1,23}$');
alter table public.game_races add column if not exists perf jsonb check (jsonb_typeof(perf) = 'object' and length(perf::text) < 2000);
create index if not exists game_races_perf on public.game_races (started_at) where perf is not null;

create or replace function public.regatta_admin_stats(days int default 30)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  since timestamptz := now() - make_interval(days => greatest(1, least(coalesce(days, 30), 365)));
  out jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;
  with r as (
    select coalesce(g.yacht, 'jpk1050') as yacht, g.wind, g.venue, coalesce(g.shape, 'wl') as shape,
           case when g.daily is not null then 'daily' else 'free' end as kind,
           g.finished_at is not null as fin, g.dsq, g.place, g.boats,
           coalesce(g.user_id::text, g.player::text) as who,
           (g.perf ->> 'fps')::real as fps, (g.perf ->> 'low')::real as low, (g.perf ->> 'stall')::real as stall,
           (g.perf ->> 'load')::real as load, (g.perf ->> 'saver')::int as saver, g.perf ->> 'q' as q,
           (g.perf ->> 'dev') || case when g.perf ->> 'tg' = '1' then ' tg' else '' end as dev,
           g.perf ->> 'gpu' as gpu, g.perf ->> 'os' as os, g.perf ->> 'br' as br
      from public.game_races g
     where g.started_at >= since
  ), grouped as (
    select case when grouping(yacht) = 0 then 'yacht' when grouping(wind) = 0 then 'wind' when grouping(venue) = 0 then 'venue'
                when grouping(shape) = 0 then 'shape' when grouping(kind) = 0 then 'kind' when grouping(dev) = 0 then 'dev'
                when grouping(gpu) = 0 then 'gpu' when grouping(q) = 0 then 'q' when grouping(os) = 0 then 'os'
                when grouping(br) = 0 then 'br' else 'all' end as k,
           case when grouping(yacht) = 0 then yacht when grouping(wind) = 0 then wind when grouping(venue) = 0 then venue
                when grouping(shape) = 0 then shape when grouping(kind) = 0 then kind when grouping(dev) = 0 then dev
                when grouping(gpu) = 0 then gpu when grouping(q) = 0 then q when grouping(os) = 0 then os
                when grouping(br) = 0 then br end as v,
           count(*) as n, count(*) filter (where fin) as fin, count(*) filter (where dsq) as dsq,
           count(*) filter (where place <= 3) as top3, count(distinct who) as who,
           percentile_cont(0.5) within group (order by (place - 1)::real / greatest(boats - 1, 1)) as down,
           count(fps) as np,
           percentile_cont(0.5) within group (order by fps) as fps, percentile_cont(0.5) within group (order by low) as low,
           percentile_cont(0.5) within group (order by stall) as stall, percentile_cont(0.5) within group (order by load) as load,
           count(*) filter (where fps < 30) as slow, avg(saver) as saver,
           count(*) filter (where q = 'high') as qh, count(*) filter (where q = 'medium') as qm, count(*) filter (where q = 'low') as ql
      from r
     group by grouping sets ((yacht), (wind), (venue), (shape), (kind), (dev), (gpu), (q), (os), (br), ())
  )
  select jsonb_build_object(
    'since', since,
    'groups', coalesce((select jsonb_agg(to_jsonb(grouped) order by k, n desc) from grouped where k = 'all' or v is not null or k = 'venue'), '[]'::jsonb),
    'days', coalesce((select jsonb_agg(jsonb_build_object('d', d, 'n', n, 'fin', fin, 'who', who, 'fps', fps) order by d)
                        from (select g.started_at::date as d, count(*) as n, count(g.finished_at) as fin,
                                     count(distinct coalesce(g.user_id::text, g.player::text)) as who,
                                     percentile_cont(0.5) within group (order by (g.perf ->> 'fps')::real) as fps
                                from public.game_races g where g.started_at >= since group by 1) d), '[]'::jsonb)
  ) into out;
  return out;
end $$;

revoke all on function public.regatta_admin_stats(int) from public, anon;
grant execute on function public.regatta_admin_stats(int) to authenticated;
