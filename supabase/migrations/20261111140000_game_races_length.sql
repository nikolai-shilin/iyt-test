-- The Regatta game got a course length (short, medium, long: the legs 1×, 2× and 3.4× as long) and a fleet of 4, 7 or
-- 10 boats. With wind and laps they make the course, and a best time compares only on the same one (the admins'
-- Best times by course, miniapp/app.js). length is kept from the start of the race; boats (the fleet) is now kept
-- from the start too, not only at the finish. Races recorded before this have no length.
alter table public.game_races add column length text check (length in ('short', 'medium', 'long'));
