-- The Regatta game's races keep to what api/game.mjs writes, so a bad post or a later bug can't leave a row the
-- rankings would misread. Every row in the table passed each of these when they were written (2026-11-15).
--
--   shape: one of the four course shapes the API takes (null: a race from before the shapes, counted as 'wl').
--   place: within the fleet; a disqualified race has none (the rankings skip it by dsq, and the admins' places too).
--   an unfinished race has no place, time or disqualification: only the finish fills them in, all at once.
--   a race is the Telegram user's or the site account's, never both (who() in api/game.mjs reads user_id first).
alter table public.game_races
  add constraint game_races_shape check (shape in ('wl', 'tri', 'trap', 'wlu')),
  add constraint game_races_place_in_fleet check (place <= boats),
  add constraint game_races_dsq_no_place check (not (dsq and place is not null)),
  add constraint game_races_unfinished_blank check (finished_at is not null or (place is null and secs is null and not dsq)),
  add constraint game_races_one_player check (num_nonnulls(user_id, player) <= 1);
