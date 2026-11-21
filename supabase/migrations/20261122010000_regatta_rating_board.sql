-- The 1-on-1 rating's own board, for the leaderboard on /race (release 6a of the 1-on-1 plan; the ryc-regatta repo:
-- components/race-board.tsx, lib/duel-board.ts).
--
-- regatta_rating_board(): anyone may read it (the page is built once for everyone): the sailors with a 1-on-1 rating,
-- those settled (five rated races or more) first by rating, then those still provisional by rating, fifty at most; each
-- with their name as the site shows it, rating, rated races, wins and losses; and how many are settled and provisional.

create function public.regatta_rating_board()
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'settled', (select count(*) from public.regatta_rating where races >= 5),
    'provisional', (select count(*) from public.regatta_rating where races between 1 and 4),
    'rows', coalesce((
      select jsonb_agg(jsonb_build_object('name', public.regatta_account_name(r.user_id), 'rating', r.rating, 'races', r.races,
          'wins', r.wins, 'losses', r.losses) order by (r.races >= 5) desc, r.rating desc, r.races desc)
        from (select * from public.regatta_rating where races >= 1 order by (races >= 5) desc, rating desc, races desc limit 50) r), '[]'::jsonb))
$$;

revoke all on function public.regatta_rating_board() from public;
grant execute on function public.regatta_rating_board() to anon, authenticated;
