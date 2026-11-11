-- The Regatta game's races, for the admins (the Game block on the Overview page of the mini app, api/admin.mjs).
--
-- One row per race the player started (miniapp/regatta/stats.js posts to api/game.mjs): when, in what wind and how
-- many laps; when they crossed the finish, their place among the boats (null when disqualified) and their time. A race
-- that was left (back to the menu, restarted, the app closed) keeps finished_at null. id is made by the game, so the
-- finish finds its start. user_id is the Telegram user when the game ran inside Telegram, null in a plain browser; it
-- is not a reference to public.users, since a player may never have written to the bot.
create table public.game_races (
  id          uuid primary key,
  user_id     bigint,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  wind        text check (wind in ('light', 'medium', 'strong')),
  laps        smallint check (laps between 1 and 9),
  boats       smallint check (boats between 1 and 20),
  place       smallint check (place between 1 and 20),
  secs        real check (secs >= 0 and secs < 86400),
  dsq         boolean not null default false
);
create index game_races_started_at on public.game_races (started_at);
create index game_races_user_id on public.game_races (user_id) where user_id is not null;
alter table public.game_races enable row level security;   -- no policies: only the server (secret key) reads and writes it
grant all on public.game_races to service_role;
