-- The 1-on-1 rating on the players' table (ryc-regatta: components/players-view.tsx, lib/players.ts; api/game.mjs
-- ?players and ?player= here).
--
-- regatta_ratings_of(tgs, accts): the 1-on-1 rating (rating, rated races) of the players asked for, by their Telegram id
-- (an account that signed in with Telegram, as api/game.mjs counts it) or their account id (one that didn't); only those
-- with a rated race. [ { tg, acct, rating, races } ], tg null for an account with no Telegram. Only the scores API asks
-- (the service role), twenty players at a time.

create function public.regatta_ratings_of(tgs bigint[] default '{}', accts uuid[] default '{}')
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('tg', x.tg, 'acct', x.id, 'rating', r.rating, 'races', r.races)), '[]'::jsonb)
  from (
    select a.id, case when a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,15}$' then (a.raw_app_meta_data ->> 'telegram_id')::bigint end as tg
    from auth.users a
    where a.id = any(accts)
       or (a.raw_app_meta_data ->> 'telegram_id') = any(array(select t::text from unnest(tgs) t))
  ) x
  join public.regatta_rating r on r.user_id = x.id
  where r.races >= 1
$$;

revoke all on function public.regatta_ratings_of(bigint[], uuid[]) from public, anon, authenticated;
grant execute on function public.regatta_ratings_of(bigint[], uuid[]) to service_role;
