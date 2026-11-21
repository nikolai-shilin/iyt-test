-- The 1-on-1 page as it was designed (the design canvas "1-on-1 races", board "The 1-on-1 page"; the ryc-regatta repo:
-- components/duel-finder.tsx, app/connect/seek, app/connect/rating/near). Two things it shows that nothing read yet:
--   regatta_calls_open(): for a signed-in sailor, the open calls they could take now (open: not taken, not closed, and
--     its poster still looking), the nearest rating first, twenty at most: the code, the poster's name, rating and races,
--     the call's band and its wishes, how long ago it was posted, whether it's their own and whether their rating is in
--     the band (taking one is regatta_call_take, as from the call's own page).
--   regatta_rating_near(): for a signed-in sailor, the 1-on-1 rating around them: the settled ratings (five rated races or
--     more) from three places above to three below theirs, placed as regatta_my_rating places them (one more than those
--     rated higher, so equal ratings share a place); a sailor not settled yet gets the top seven. Their place and how many
--     are settled with it.

create function public.regatta_calls_open()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  mine int;
begin
  if me is null then return '[]'::jsonb; end if;
  select r.rating into mine from public.regatta_rating r where r.user_id = me;
  mine := coalesce(mine, 1500);
  return coalesce((
    select jsonb_agg(y.j order by y.gap, y.at desc)
      from (select jsonb_build_object('code', c.code, 'name', c.name, 'rating', c.rating, 'races', c.races, 'lo', c.lo, 'hi', c.hi,
                     'venue', nullif(c.wishes ->> 'venue', ''), 'yacht', nullif(c.wishes ->> 'yacht', ''),
                     'ago', floor(extract(epoch from now() - c.created_at))::int, 'mine', c.user_id = me, 'in_band', mine between c.lo and c.hi) as j,
                   abs(c.rating - mine) as gap, c.created_at as at
              from public.regatta_call c
             where c.closes_at > now() and public.regatta_call_state(c) = 'open'
             order by abs(c.rating - mine), c.created_at desc limit 20) y), '[]'::jsonb);
end $$;
revoke all on function public.regatta_calls_open() from public, anon;
grant execute on function public.regatta_calls_open() to authenticated;

create function public.regatta_rating_near()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  my_place int;
  my_n int;
begin
  if me is null then return null; end if;
  select s.place, s.n into my_place, my_n
    from (select r.user_id, (select count(*) + 1 from public.regatta_rating x where x.races >= 5 and x.rating > r.rating) as place,
                 row_number() over (order by r.rating desc, r.races desc, r.user_id) as n
            from public.regatta_rating r where r.races >= 5) s where s.user_id = me;
  return jsonb_build_object('place', my_place, 'of', (select count(*) from public.regatta_rating where races >= 5),
    'rows', coalesce((
      select jsonb_agg(jsonb_build_object('place', s.place, 'name', public.regatta_account_name(s.user_id), 'rating', s.rating, 'races', s.races,
               'wins', s.wins, 'losses', s.losses, 'me', s.user_id = me) order by s.n)
        from (select r.*, (select count(*) + 1 from public.regatta_rating x where x.races >= 5 and x.rating > r.rating) as place,
                     row_number() over (order by r.rating desc, r.races desc, r.user_id) as n
                from public.regatta_rating r where r.races >= 5) s
       where case when my_n is null then s.n <= 7 else s.n between my_n - 3 and my_n + 3 end), '[]'::jsonb));
end $$;
revoke all on function public.regatta_rating_near() from public, anon;
grant execute on function public.regatta_rating_near() to authenticated;
