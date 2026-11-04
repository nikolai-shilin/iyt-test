-- Yachtmaster Ocean gets its bank: the level row (seeded as 'planned' with no prefix or link) gets its question prefix and deep
-- link. load_bank() (data/load.mjs) fills topics and questions from data/questions/yachtmaster-ocean.json and sets it available.
update public.levels set prefix = 'yo', link = 'ocean', updated_at = now()
where id = 'yachtmaster-ocean';
