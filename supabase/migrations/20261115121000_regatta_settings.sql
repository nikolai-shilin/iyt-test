-- The Regatta site's admin settings (the ryc-regatta repo: /admin, /sponsor): the ad on every boat's jib and the words
-- on the plane's banner. They were made in the dashboard's SQL editor and lived in no migration; this writes them down
-- as they are, so a new project or a branch gets the same, and running it on this project changes only what is new
-- below (the stamp trigger and the value check).
--
--   regatta_admins: the admins' emails, lower case. Only the database's owner edits it (no policies: RLS lets no one
--     else read or write it). is_regatta_admin() reads it for the signed-in user's email.
--   regatta_settings: one row a key. Everyone reads it (the game's /sponsor); only an admin writes it.
--   storage bucket regatta-ads: the jib's pictures, public to read, only an admin uploads or removes.

create table if not exists public.regatta_admins (
  email text primary key check (email = lower(email))
);
alter table public.regatta_admins enable row level security;

create table if not exists public.regatta_settings (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now(),
  updated_by uuid default auth.uid()
);
alter table public.regatta_settings enable row level security;

create or replace function public.is_regatta_admin()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.regatta_admins a where a.email = lower(coalesce(auth.jwt() ->> 'email', '')));
$$;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'regatta_settings' and policyname = 'regatta settings are public') then
    create policy "regatta settings are public" on public.regatta_settings for select to anon, authenticated using (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'regatta_settings' and policyname = 'regatta admins add settings') then
    create policy "regatta admins add settings" on public.regatta_settings for insert to authenticated with check ((select public.is_regatta_admin()));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'regatta_settings' and policyname = 'regatta admins change settings') then
    create policy "regatta admins change settings" on public.regatta_settings for update to authenticated
      using ((select public.is_regatta_admin())) with check ((select public.is_regatta_admin()));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'regatta_settings' and policyname = 'regatta admins remove settings') then
    create policy "regatta admins remove settings" on public.regatta_settings for delete to authenticated using ((select public.is_regatta_admin()));
  end if;
end $$;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('regatta-ads', 'regatta-ads', true, 2097152, array['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'])
on conflict (id) do nothing;

do $$ begin
  if not exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'regatta admins list ads') then
    create policy "regatta admins list ads" on storage.objects for select to authenticated
      using (bucket_id = 'regatta-ads' and (select public.is_regatta_admin()));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'regatta admins upload ads') then
    create policy "regatta admins upload ads" on storage.objects for insert to authenticated
      with check (bucket_id = 'regatta-ads' and (select public.is_regatta_admin()));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'regatta admins replace ads') then
    create policy "regatta admins replace ads" on storage.objects for update to authenticated
      using (bucket_id = 'regatta-ads' and (select public.is_regatta_admin()));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'regatta admins remove ads') then
    create policy "regatta admins remove ads" on storage.objects for delete to authenticated
      using (bucket_id = 'regatta-ads' and (select public.is_regatta_admin()));
  end if;
end $$;

-- New: who changed a setting and when, stamped by the database. The admin page upserts without updated_by, and
-- a column default only applies to an insert, so after the first save updated_by kept the first writer (or none) and
-- updated_at was the admin's browser clock.
create or replace function public.regatta_settings_stamp()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  new.updated_by := auth.uid();
  return new;
end $$;
drop trigger if exists regatta_settings_stamp on public.regatta_settings;
create trigger regatta_settings_stamp before insert or update on public.regatta_settings
  for each row execute function public.regatta_settings_stamp();

-- New: each key's value is the shape /sponsor reads (it checks the rest itself); a key it doesn't know is free.
alter table public.regatta_settings drop constraint if exists regatta_settings_value;
alter table public.regatta_settings add constraint regatta_settings_value check (case key
  when 'jib_ad' then jsonb_typeof(value -> 'url') = 'string'
  when 'plane_banner' then jsonb_typeof(value -> 'lines') = 'array'
  else true end);
