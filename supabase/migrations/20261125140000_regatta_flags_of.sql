-- The flag a rating's players fly (api/game.mjs flyingFlags, for GET ?day=, ?day=&brief and ?month=): the flag of each
-- one's latest race of any kind in the last 30 days (a start they didn't finish, a free race), as the game card reads
-- it (public.regatta_game_card). The API read every race of those 30 days for it, a thousand at a time (seven round
-- trips on 25 November) to find the flags of the ten or hundred players on a board; this reads only theirs.
--
-- regatta_flags_of(tgs, accts) → [ { user_id, player, started_at, flag } ]: each asked player's latest race of the 30
-- days, by their Telegram id (tgs) or, for a player without one, their account id (accts; races with no Telegram id
-- only, as api/game.mjs who() keys them); none for a player with no race that recent. Only the scores API asks (the
-- service role).

create function public.regatta_flags_of(tgs bigint[] default '{}', accts uuid[] default '{}')
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('user_id', x.user_id, 'player', x.player, 'started_at', x.started_at, 'flag', x.flag)), '[]'::jsonb)
  from (
    select distinct on (coalesce(user_id::text, 'a:' || player::text)) user_id, player, started_at, flag
    from public.game_races
    where started_at >= now() - interval '30 days'
      and (user_id = any(tgs) or (user_id is null and player = any(accts)))
    order by coalesce(user_id::text, 'a:' || player::text), started_at desc
  ) x
$$;

revoke all on function public.regatta_flags_of(bigint[], uuid[]) from public, anon, authenticated;
grant execute on function public.regatta_flags_of(bigint[], uuid[]) to service_role;
