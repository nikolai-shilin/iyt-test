-- load_bank(bank, overlays): upserts one level from data/questions/<level>.json and its <level>.<lang>.json
-- overlays. Called by data/load.mjs with the secret key; nobody else may run it.
-- Questions missing from the bank are marked active = false (answers still point at them), not deleted.

grant select on public.levels, public.topics, public.questions, public.level_languages,
  public.topic_translations, public.question_translations to anon, authenticated;
grant all on all tables in schema public to service_role;

create or replace function public.load_bank(p_bank jsonb, p_overlays jsonb default '[]'::jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_level   text := p_bank ->> 'level';
  v_ids     text[];
  v_ov      jsonb;
  v_lang    text;
  n_changed int;
  n_retired int;
  n_rows    int;
  v_langs   jsonb := '{}'::jsonb;
begin
  if v_level is null or jsonb_typeof(p_bank -> 'questions') is distinct from 'array'
     or jsonb_typeof(p_bank -> 'topics') is distinct from 'array' then
    raise exception 'load_bank: not a bank file';
  end if;
  if not exists (select 1 from public.levels where id = v_level) then
    raise exception 'load_bank: unknown level % (add it to public.levels first)', v_level;
  end if;

  update public.levels set
    status         = 'available',
    pass_mark      = (p_bank ->> 'passMark')::smallint,
    exam_questions = (p_bank ->> 'examQuestions')::smallint,
    exam_minutes   = (p_bank ->> 'examMinutes')::smallint,
    version        = p_bank ->> 'version',
    note           = p_bank ->> 'note',
    updated_at     = now()
  where id = v_level;

  insert into public.topics (level_id, id, title, icon, sort)
  select v_level, t ->> 'id', t ->> 'title', t ->> 'icon', ord::smallint
  from jsonb_array_elements(p_bank -> 'topics') with ordinality as x (t, ord)
  on conflict (level_id, id) do update
    set title = excluded.title, icon = excluded.icon, sort = excluded.sort;

  insert into public.questions as cur (id, level_id, topic_id, sort, difficulty, q, figure, options, answer, why, ref, active)
  select q ->> 'id', v_level, q ->> 'topic', ord::int, (q ->> 'difficulty')::smallint, q ->> 'q',
         nullif(q -> 'figure', 'null'::jsonb), q -> 'options', (q ->> 'answer')::smallint, q ->> 'why', q ->> 'ref', true
  from jsonb_array_elements(p_bank -> 'questions') with ordinality as x (q, ord)
  on conflict (id) do update
    set level_id = excluded.level_id, topic_id = excluded.topic_id, sort = excluded.sort,
        difficulty = excluded.difficulty, q = excluded.q, figure = excluded.figure, options = excluded.options,
        answer = excluded.answer, why = excluded.why, ref = excluded.ref, active = true, updated_at = now()
    where (cur.level_id, cur.topic_id, cur.sort, cur.difficulty, cur.q, cur.figure, cur.options, cur.answer,
           cur.why, cur.ref, cur.active)
      is distinct from (excluded.level_id, excluded.topic_id, excluded.sort, excluded.difficulty, excluded.q,
           excluded.figure, excluded.options, excluded.answer, excluded.why, excluded.ref, true);
  get diagnostics n_changed = row_count;

  select array_agg(q ->> 'id') into v_ids from jsonb_array_elements(p_bank -> 'questions') as q;
  update public.questions set active = false, updated_at = now()
  where level_id = v_level and active and id <> all (v_ids);
  get diagnostics n_retired = row_count;

  for v_ov in select * from jsonb_array_elements(coalesce(p_overlays, '[]'::jsonb)) loop
    v_lang := v_ov ->> 'lang';
    if v_lang is null or v_ov ->> 'level' is distinct from v_level then
      raise exception 'load_bank: overlay % does not belong to %', v_ov ->> 'level', v_level;
    end if;

    insert into public.level_languages (level_id, lang, source_version, note)
    values (v_level, v_lang, v_ov ->> 'source', v_ov ->> 'note')
    on conflict (level_id, lang) do update set source_version = excluded.source_version, note = excluded.note;

    insert into public.topic_translations (level_id, topic_id, lang, title, short)
    select v_level, e.key, v_lang, e.value, v_ov -> 'short' ->> e.key
    from jsonb_each_text(coalesce(v_ov -> 'topics', '{}'::jsonb)) as e
    where exists (select 1 from public.topics t where t.level_id = v_level and t.id = e.key)
    on conflict (level_id, topic_id, lang) do update set title = excluded.title, short = excluded.short;

    delete from public.question_translations qt
    using public.questions q
    where qt.question_id = q.id and q.level_id = v_level and qt.lang = v_lang
      and not (coalesce(v_ov -> 'questions', '{}'::jsonb) ? qt.question_id);

    insert into public.question_translations (question_id, lang, q, options, why, ref, figure)
    select e.key, v_lang, e.value ->> 'q', e.value -> 'options', e.value ->> 'why', e.value ->> 'ref', e.value -> 'figure'
    from jsonb_each(coalesce(v_ov -> 'questions', '{}'::jsonb)) as e
    where exists (select 1 from public.questions q where q.id = e.key and q.level_id = v_level)
    on conflict (question_id, lang) do update
      set q = excluded.q, options = excluded.options, why = excluded.why, ref = excluded.ref, figure = excluded.figure;
    get diagnostics n_rows = row_count;
    v_langs := v_langs || jsonb_build_object(v_lang, n_rows);
  end loop;

  return jsonb_build_object('level', v_level, 'questions', jsonb_array_length(p_bank -> 'questions'),
                            'changed', n_changed, 'retired', n_retired, 'translations', v_langs);
end
$$;

revoke execute on function public.load_bank(jsonb, jsonb) from public, anon, authenticated;
grant execute on function public.load_bank(jsonb, jsonb) to service_role;
