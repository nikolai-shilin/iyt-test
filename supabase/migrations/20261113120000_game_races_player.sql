-- The Regatta game's players who sign in on the site (regatta.rycrentals.com) rather than inside Telegram, and the
-- result page's record of a race, for a shared link.
--
-- player is the race's Regatta account (this project's Supabase Auth user) when the game ran on the site signed in
-- with Google or an email code; user_id stays the Telegram user, also for a site account made from Telegram (its
-- app_metadata.telegram_id). api/game.mjs ranks a player by either, and names a site account by its
-- user_metadata.display_name. Not a reference to auth.users: a deleted account leaves its races as a guest's would.
--
-- result is what the game's result page shows (public/game/main.js finishToPage in the ryc-regatta repo): the course,
-- every boat's thinned track and the debrief, some 25 kB. It is posted once, after the finish, and read back by
-- GET /api/game?race=<id> when the result link is opened on another device.
alter table public.game_races add column player uuid;
alter table public.game_races add column result jsonb;
create index game_races_player on public.game_races (player) where player is not null;
