-- Charter Check-in: a level that is not an IYT course — taking over a bareboat at the base — after the Racing Rules.
-- load_bank() (data/load.mjs) fills its topics and questions from data/questions/charter-checkin.json and sets it available.
insert into public.levels (id, prefix, link, title, sort, status) values
  ('charter-checkin', 'ci', 'checkin', 'Charter Check-in', 10, 'planned')
on conflict (id) do nothing;
