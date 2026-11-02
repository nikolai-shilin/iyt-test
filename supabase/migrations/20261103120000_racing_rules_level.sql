-- Racing Rules of Sailing: a level that is not an IYT course, after the IYT ones. load_bank() (data/load.mjs) fills
-- its topics and questions from data/questions/racing-rules.json and sets it available.
insert into public.levels (id, prefix, link, title, sort, status) values
  ('racing-rules', 'rr', 'racing', 'Racing Rules of Sailing', 9, 'planned')
on conflict (id) do nothing;
