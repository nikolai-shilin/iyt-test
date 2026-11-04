-- Yachtmaster Offshore gets its bank: the level row (seeded as 'soon2027' with no prefix or link) gets its question prefix and
-- deep link. load_bank() (data/load.mjs) fills topics and questions from data/questions/yachtmaster-offshore.json and sets it available.
update public.levels set prefix = 'yof', link = 'offshore', updated_at = now()
where id = 'yachtmaster-offshore';
