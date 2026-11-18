-- The Regatta game's players, added up here rather than in api/game.mjs, which read every race of every player (1000 a
-- page, and no more than 20 000 of them) for each page of /players and each player's card, and asked Supabase Auth for
-- each site account's name one request at a time.
--
-- regatta_names(ids): the display name and the boat each of these accounts keeps in its user_metadata.
-- regatta_players(): { players: [ one row a player, their races added up ], days: [ each player's best of each day of
-- the daily race ] }. The points are still worked out from the days by api/game.mjs (rankDay, monthTable).
-- Both for the server alone (the secret key).

create or replace function public.regatta_names(ids uuid[])
returns table (id uuid, display_name text, boat jsonb) language sql stable security definer set search_path = '' as $$
  select a.id, a.raw_user_meta_data ->> 'display_name', a.raw_user_meta_data -> 'boat'
    from auth.users a
   where a.id = any (ids)
$$;

create or replace function public.regatta_players()
returns jsonb language sql stable security definer set search_path = '' set timezone = 'UTC' as $$
  with r as (
    select user_id as u, case when user_id is null then player::text end as a, coalesce(user_id::text, 'a:' || player::text) as k,
           started_at, boats, secs, dsq, place, daily, flag, coalesce(yacht, 'jpk1050') as yacht, venue,
           finished_at is not null and not dsq as done
      from public.game_races
     where user_id is not null or player is not null
  ), yachts as (
    select k, jsonb_object_agg(yacht, c) as m from (select k, yacht, count(*) as c from r group by k, yacht) x group by k
  ), venues as (
    select k, jsonb_object_agg(venue, c) as m from (select k, venue, count(*) as c from r where venue <> '' group by k, venue) x group by k
  ), p as (
    select k, min(u) as u, min(a) as a, count(*) as n,
           count(*) filter (where done) as fin,
           count(*) filter (where done and place = 1) as wins,
           count(*) filter (where done and place <= 3) as podiums,
           count(*) filter (where dsq) as dsq,
           count(distinct started_at::date) as days,
           min(started_at) as first, max(started_at) as last,
           min(place) filter (where done) as best,
           (array_agg(boats order by place, boats desc nulls last) filter (where done and place is not null))[1] as fleet,
           count(*) filter (where done and daily is not null and secs > 0) as dn,
           (array_agg(flag order by started_at desc))[1] as flag
      from r group by k
  ), d as (
    select daily as d, min(u) as u, min(a) as a, min(secs) as s, min(place) as p, count(*) as n
      from r where done and daily is not null and secs > 0 group by daily, k
  )
  select jsonb_build_object(
    'players', coalesce((select jsonb_agg(to_jsonb(p) - 'k' || jsonb_build_object('yachts', coalesce(y.m, '{}'), 'venues', coalesce(v.m, '{}')))
                           from p left join yachts y using (k) left join venues v using (k)), '[]'),
    'days', coalesce((select jsonb_agg(to_jsonb(b)) from d as b), '[]'))
$$;

revoke all on function public.regatta_names(uuid[]) from public, anon, authenticated;
revoke all on function public.regatta_players() from public, anon, authenticated;
grant execute on function public.regatta_names(uuid[]) to service_role;
grant execute on function public.regatta_players() to service_role;
