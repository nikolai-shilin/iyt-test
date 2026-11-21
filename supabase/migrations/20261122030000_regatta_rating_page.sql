-- The 1-on-1 rating's own page (release 7b of the 1-on-1 plan; the ryc-regatta repo: app/[lang]/duel/rating,
-- lib/rating-page.ts). regatta_rating_page(): for the signed-in sailor, their rating, record, best and lowest; their
-- place among the settled sailors (five rated races or more), how many those are and how many of them are below; the
-- points the day's rated races moved it (UTC); how many settled sailors hold each of the seven levels (lib/levels.ts);
-- the spread of all settled ratings in bins of 50; and every rated race of theirs, the earliest first (the latest 500):
-- when, before and after, the change, won or lost, K and the chance it was worked out from, how many rated races came
-- before it, the other sailor's name and rating then, the margin, a forfeit, the venue and the yacht. Nobody else's.

create function public.regatta_rating_page()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  r public.regatta_rating;
  settled int;
begin
  if me is null then return null; end if;
  select count(*) into settled from public.regatta_rating x where x.races >= 5;
  select * into r from public.regatta_rating where user_id = me;
  return jsonb_build_object(
    'rating', coalesce(r.rating, 1500), 'races', coalesce(r.races, 0), 'wins', coalesce(r.wins, 0), 'losses', coalesce(r.losses, 0),
    'best', coalesce(r.best, 1500), 'lowest', coalesce(r.lowest, 1500),
    'place', case when r.races >= 5 then (select count(*) + 1 from public.regatta_rating x where x.races >= 5 and x.rating > r.rating) end,
    'of', settled,
    'below', case when r.races >= 5 then (select count(*) from public.regatta_rating x where x.races >= 5 and x.rating < r.rating) end,
    'today', (select coalesce(sum(c.delta), 0) from public.regatta_rating_change c
               where c.user_id = me and c.at >= date_trunc('day', now() at time zone 'UTC') at time zone 'UTC'),
    'levels', (select jsonb_agg((select count(*) from public.regatta_rating x where x.races >= 5 and x.rating >= b.lo and x.rating < b.hi) order by b.lo)
                 from (values (-100000, 1200), (1200, 1400), (1400, 1600), (1600, 1800), (1800, 2000), (2000, 2200), (2200, 100000)) b(lo, hi)),
    'spread', (select coalesce(jsonb_agg(jsonb_build_object('at', g.bin, 'n', g.n) order by g.bin), '[]'::jsonb)
                 from (select (floor(x.rating / 50.0) * 50)::int as bin, count(*) as n from public.regatta_rating x where x.races >= 5 group by 1) g),
    'history', (select coalesce(jsonb_agg(jsonb_build_object('at', c.at, 'before', c.before, 'after', c.after, 'delta', c.delta, 'won', c.won,
                   'k', c.k, 'chance', round(c.chance::numeric, 4), 'n', c.races_before,
                   'them', case when d.host_user = me then d.guest_name else d.host_name end, 'them_before', c.opponent_before,
                   'margin', d.margin, 'forfeit', d.forfeited is not null, 'venue', d.venue, 'yacht', d.yacht) order by c.at), '[]'::jsonb)
                  from (select * from public.regatta_rating_change c where c.user_id = me order by c.at desc limit 500) c
                  join public.regatta_duels d on d.id = c.duel_id));
end $$;
revoke all on function public.regatta_rating_page() from public, anon;
grant execute on function public.regatta_rating_page() to authenticated;
