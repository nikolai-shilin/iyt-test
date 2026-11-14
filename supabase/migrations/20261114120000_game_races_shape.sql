-- The Regatta game's course shape: 'wl' up and down, 'tri' triangle, 'trap' trapezoid, 'wlu' up and down with an upwind
-- finish. Posted with the start (api/game.mjs); a race from before the column, or posted without it, is null, which
-- the rankings count as 'wl'. Until this is applied the API works as before: the column is written and read only when
-- it is there.
alter table public.game_races add column if not exists shape text;
