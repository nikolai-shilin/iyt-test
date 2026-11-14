-- The Regatta game's flag: the country flag the player's boat flies on her main (the boat page in the ryc-regatta repo,
-- lib/flags.ts there: a two-letter code, 'gb', or one with a region, 'gb-sct'), posted with the start (api/game.mjs).
-- The rankings show each player's flag beside their name, the one from their latest race. A race from before the
-- column, or a boat without a flag, is null. Until this is applied the API works as before: the column is written and
-- read only when it is there.
alter table public.game_races add column if not exists flag text check (flag ~ '^[a-z]{2}(-[a-z]{2,4})?$');
