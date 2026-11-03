-- Yachtmaster Coastal gets its bank: the level row (seeded as 'soon' with no prefix or link) gets its question prefix and
-- deep link. load_bank() (data/load.mjs) fills topics and questions from data/questions/yachtmaster-coastal.json and sets it available.
update public.levels set prefix = 'yc', link = 'coastal', updated_at = now()
where id = 'yachtmaster-coastal';
