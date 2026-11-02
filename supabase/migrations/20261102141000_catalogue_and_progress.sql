-- IYT Test database (Supabase project iyt-test). See docs/data-model.md.
-- Catalogue: levels, topics, questions and their translations, filled from data/questions/*.json by data/load.mjs.
-- Progress: users, answers, flags, exam sessions, reports — empty until the apps log in through Telegram.

-- ---------- catalogue ----------

create table public.levels (
  id             text primary key,                 -- 'bareboat-skipper'
  prefix         text unique,                      -- question id prefix: 'bs' → bs-001
  link           text unique,                      -- deep-link name: ?level=bareboat
  title          text not null,
  sort           smallint not null,                -- IYT course progression order
  status         text not null default 'planned'
                 check (status in ('available', 'planned', 'soon', 'soon2027')),
  pass_mark      smallint check (pass_mark between 1 and 100),
  exam_questions smallint check (exam_questions > 0),
  exam_minutes   smallint check (exam_minutes > 0),
  version        text,                             -- bank version; apps cache the catalogue by it
  note           text,
  updated_at     timestamptz not null default now()
);

create table public.topics (
  level_id text not null references public.levels (id) on delete cascade,
  id       text not null,
  title    text not null,
  icon     text,
  sort     smallint not null,
  primary key (level_id, id)
);

create table public.questions (
  id         text primary key,                     -- 'bs-001'
  level_id   text not null references public.levels (id) on delete cascade,
  topic_id   text not null,
  sort       int not null,                         -- position in the bank file
  difficulty smallint not null check (difficulty between 1 and 3),
  q          text not null,
  figure     jsonb,                                -- spec for docs/design/figures.js; null = text question
  options    jsonb not null check (jsonb_typeof(options) = 'array' and jsonb_array_length(options) = 4),
  answer     smallint not null check (answer between 0 and 3),
  why        text not null,
  ref        text,
  active     boolean not null default true,        -- false once dropped from the bank (answers keep pointing at it)
  updated_at timestamptz not null default now(),
  foreign key (level_id, topic_id) references public.topics (level_id, id) on update cascade
);
create index questions_level_topic_idx on public.questions (level_id, topic_id);

-- One row per translated level and language (the overlay file's header).
create table public.level_languages (
  level_id       text not null references public.levels (id) on delete cascade,
  lang           text not null,
  source_version text,                             -- bank version the overlay was made from
  note           text,
  primary key (level_id, lang)
);

create table public.topic_translations (
  level_id text not null,
  topic_id text not null,
  lang     text not null,
  title    text not null,
  short    text,                                   -- short name for chips and tabs
  primary key (level_id, topic_id, lang),
  foreign key (level_id, topic_id) references public.topics (level_id, id) on delete cascade on update cascade
);

-- Overlay of one question: any field left null falls back to English. figure holds only the translated text
-- fields of the figure spec (e.g. note), merged over the English figure by the app.
create table public.question_translations (
  question_id text not null references public.questions (id) on delete cascade,
  lang        text not null,
  q           text,
  options     jsonb check (options is null or (jsonb_typeof(options) = 'array' and jsonb_array_length(options) = 4)),
  why         text,
  ref         text,
  figure      jsonb,
  primary key (question_id, lang)
);

-- ---------- progress (filled by the apps once Telegram login is in place) ----------

create table public.users (
  id             bigint primary key,               -- Telegram user id
  name           text,
  username       text,
  lang           text not null default 'en',
  theme          text not null default 'auto' check (theme in ('auto', 'light', 'dark')),
  level_id       text references public.levels (id),
  shuffle        boolean not null default true,
  feedback       boolean not null default true,    -- show the answer after each question in practice
  daily_question boolean not null default true,
  reminder       boolean not null default true,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index users_level_id_idx on public.users (level_id);

create table public.exam_sessions (
  id           uuid primary key default gen_random_uuid(),
  user_id      bigint not null references public.users (id) on delete cascade,
  level_id     text not null references public.levels (id),
  question_ids text[] not null,
  flags        text[] not null default '{}',
  started_at   timestamptz not null default now(),
  paused_at    timestamptz,
  submitted_at timestamptz,
  score        smallint,
  passed       boolean
);
create index exam_sessions_user_idx on public.exam_sessions (user_id, started_at desc);
create index exam_sessions_level_id_idx on public.exam_sessions (level_id);

create table public.answers (
  id          bigint generated always as identity primary key,
  user_id     bigint not null references public.users (id) on delete cascade,
  question_id text not null references public.questions (id),
  option      smallint check (option between 0 and 3),   -- null = left unanswered in an exam
  correct     boolean not null,
  mode        text not null check (mode in ('practice', 'exam', 'daily')),
  exam_id     uuid references public.exam_sessions (id) on delete cascade,
  at          timestamptz not null default now()
);
create index answers_user_question_idx on public.answers (user_id, question_id, at desc);  -- mastery: last two answers
create index answers_user_at_idx on public.answers (user_id, at);                          -- streak, answers per day
create index answers_question_id_idx on public.answers (question_id);
create index answers_exam_id_idx on public.answers (exam_id) where exam_id is not null;

create table public.flags (
  user_id     bigint not null references public.users (id) on delete cascade,
  question_id text not null references public.questions (id),
  at          timestamptz not null default now(),
  primary key (user_id, question_id)
);
create index flags_question_id_idx on public.flags (question_id);

create table public.reports (
  id          bigint generated always as identity primary key,
  user_id     bigint references public.users (id) on delete set null,
  question_id text not null references public.questions (id),
  text        text not null check (length(text) between 1 and 2000),
  at          timestamptz not null default now(),
  resolved_at timestamptz
);
create index reports_user_id_idx on public.reports (user_id);
create index reports_question_id_idx on public.reports (question_id);

-- ---------- access ----------
-- Catalogue: anyone may read it with the publishable key. Progress: no policies yet, so only the server
-- (service role / secret key) can touch it; per-user policies come with the Telegram initData login.

alter table public.levels                enable row level security;
alter table public.topics                enable row level security;
alter table public.questions             enable row level security;
alter table public.level_languages       enable row level security;
alter table public.topic_translations    enable row level security;
alter table public.question_translations enable row level security;
alter table public.users                 enable row level security;
alter table public.exam_sessions         enable row level security;
alter table public.answers               enable row level security;
alter table public.flags                 enable row level security;
alter table public.reports               enable row level security;

create policy "catalogue is public" on public.levels                for select to anon, authenticated using (true);
create policy "catalogue is public" on public.topics                for select to anon, authenticated using (true);
create policy "catalogue is public" on public.questions             for select to anon, authenticated using (true);
create policy "catalogue is public" on public.level_languages       for select to anon, authenticated using (true);
create policy "catalogue is public" on public.topic_translations    for select to anon, authenticated using (true);
create policy "catalogue is public" on public.question_translations for select to anon, authenticated using (true);

-- ---------- levels in IYT course-progression order (same list as LEVELS in miniapp/app.js) ----------

insert into public.levels (id, prefix, link, title, sort, status) values
  ('vhf-radio-operator',   'vhf', 'vhf',      'VHF Radio Operator',   1, 'planned'),
  ('international-crew',   'ic',  'crew',     'International Crew',   2, 'planned'),
  ('flotilla-skipper',     'fs',  'flotilla', 'Flotilla Skipper',     3, 'planned'),
  ('bareboat-skipper',     'bs',  'bareboat', 'Bareboat Skipper',     4, 'planned'),
  ('icc',                  null,  null,       'ICC',                  5, 'planned'),
  ('yachtmaster-coastal',  null,  null,       'Yachtmaster Coastal',  6, 'soon'),
  ('yachtmaster-offshore', null,  null,       'Yachtmaster Offshore', 7, 'soon2027'),
  ('yachtmaster-ocean',    null,  null,       'Yachtmaster Ocean',    8, 'planned');
