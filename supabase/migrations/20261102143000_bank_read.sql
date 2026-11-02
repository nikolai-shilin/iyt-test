-- bank(level) and bank_overlay(level, lang): the catalogue as the apps read it, in the same shape as
-- data/questions/<level>.json and <level>.<lang>.json, so the mini app and the bot need one request per file.
-- Read-only and public (the catalogue already is); called as GET /rest/v1/rpc/bank?p_level=...

create or replace function public.bank(p_level text)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'level', l.id,
    'title', 'IYT ' || l.title,
    'lang', 'en',
    'passMark', l.pass_mark,
    'examQuestions', l.exam_questions,
    'examMinutes', l.exam_minutes,
    'version', l.version,
    'note', l.note,
    'topics', coalesce((
      select jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
               'id', t.id, 'title', t.title, 'icon', t.icon,
               'count', (select count(*) from public.questions q where q.level_id = t.level_id and q.topic_id = t.id and q.active)))
             order by t.sort)
      from public.topics t where t.level_id = l.id), '[]'::jsonb),
    'questions', coalesce((
      select jsonb_agg(jsonb_build_object(
               'id', q.id, 'topic', q.topic_id, 'difficulty', q.difficulty, 'q', q.q, 'figure', q.figure,
               'options', q.options, 'answer', q.answer, 'why', q.why, 'ref', q.ref)
             order by q.sort)
      from public.questions q where q.level_id = l.id and q.active), '[]'::jsonb))
  from public.levels l
  where l.id = p_level and l.status = 'available'
$$;

create or replace function public.bank_overlay(p_level text, p_lang text)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select jsonb_build_object(
    'level', ll.level_id,
    'lang', ll.lang,
    'source', ll.source_version,
    'note', ll.note,
    'topics', coalesce((select jsonb_object_agg(tt.topic_id, tt.title) from public.topic_translations tt
                        where tt.level_id = ll.level_id and tt.lang = ll.lang), '{}'::jsonb),
    'short', coalesce((select jsonb_object_agg(tt.topic_id, tt.short) from public.topic_translations tt
                       where tt.level_id = ll.level_id and tt.lang = ll.lang and tt.short is not null), '{}'::jsonb),
    'questions', coalesce((
      select jsonb_object_agg(qt.question_id, jsonb_strip_nulls(jsonb_build_object(
               'q', qt.q, 'options', qt.options, 'why', qt.why, 'ref', qt.ref, 'figure', qt.figure)))
      from public.question_translations qt
      join public.questions q on q.id = qt.question_id
      where q.level_id = ll.level_id and q.active and qt.lang = ll.lang), '{}'::jsonb))
  from public.level_languages ll
  where ll.level_id = p_level and ll.lang = p_lang
$$;

revoke execute on function public.bank(text), public.bank_overlay(text, text) from public;
grant execute on function public.bank(text), public.bank_overlay(text, text) to anon, authenticated, service_role;
