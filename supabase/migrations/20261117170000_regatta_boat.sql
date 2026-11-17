-- The Regatta game's players' boats, for the site's /players (the ryc-regatta repo: components/players-view.tsx), served
-- by api/game.mjs GET ?player=<k>.
--
-- The site keeps a signed-in player's boat (her colours, deck, name, sail number, logo and flag: lib/boat.ts there) in
-- their account's user_metadata.boat. A race names its player by the Telegram id (game_races.user_id) for an account
-- made from Telegram (its app_metadata.telegram_id) and by the account (game_races.player) for any other, so the boat
-- is found by either. regatta_boat(tg, acct): that account's boat as it was saved, null for none (a player who never
-- signed in on the site, or never changed their boat). For the server alone (the secret key): nothing else about the
-- account leaves it, and api/game.mjs passes on only the boat's own fields.

create or replace function public.regatta_boat(tg bigint default null, acct uuid default null)
returns jsonb language sql stable security definer set search_path = '' as $$
  select a.raw_user_meta_data -> 'boat'
    from auth.users a
   where jsonb_typeof(a.raw_user_meta_data -> 'boat') = 'object'
     and ((acct is not null and a.id = acct)
       or (tg is not null and a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,18}$' and (a.raw_app_meta_data ->> 'telegram_id')::bigint = tg))
   order by a.updated_at desc nulls last
   limit 1
$$;

revoke all on function public.regatta_boat(bigint, uuid) from public, anon, authenticated;
grant execute on function public.regatta_boat(bigint, uuid) to service_role;
