-- The Regatta game's daily race: on a given day everyone sails the same course in the same wind (the game makes the
-- wind from the date), so its times compare fairly, unlike races on the player's own settings, whose wind shifts and
-- gusts differ every time. daily is that day (UTC) for a daily race, null for any other. api/game.mjs ranks the day's
-- best times on the game card on Home; a free race no longer mixes into them.
alter table public.game_races add column daily date;
create index game_races_daily on public.game_races (daily) where daily is not null;
