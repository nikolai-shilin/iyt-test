-- The Regatta game's class of yacht: the race's yacht when it is not the club's 40-footer (public/game/classes.js in the
-- ryc-regatta repo: 'j70', 'rs21', 'ac75' …), posted with the start (api/game.mjs). A faster class gets her share of
-- the floor a finish's time is checked against (YACHT_FLOOR there): an AC75 sails a course in some 45% of the
-- 40-footer's time. A race from before the column, or in the 40-footer, is null. Until this is applied the API works as
-- before: the column is written and read only when it is there.
alter table public.game_races add column if not exists yacht text check (yacht ~ '^[a-z][a-z0-9]{1,15}$');
