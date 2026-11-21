-- "A sailor at your level is looking" (release 8c of the 1-on-1 plan: release 7's leftovers, For you's live message; the
-- ryc-regatta repo: lib/push-send.ts sendLookPing, app/connect/seek). When a sailor starts looking and nobody near their
-- rating is looking too, up to three sailors within 100 of them are told, by the browsers tied to their account and from
-- the Telegram bot, with a tap that challenges them at once. Only sailors who:
--   - have raced a 1-on-1 in the last fourteen days, and aren't looking already;
--   - take messages that way (regatta_msg), and aren't in their quiet hours;
--   - haven't put "ready" out of their For you this week (regatta_suggest);
--   - haven't been told in the last day (one a day at most).
-- A searcher sets it off once in thirty minutes at most. regatta_ping keeps who was told, for whom and when.
-- regatta_ping_due(key, seeker): the messages to send, with the daily reminder's key (vault regatta_push_key); nothing
-- unless the seeker is looking now and unpaired.

create table public.regatta_ping (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  seeker uuid not null references auth.users (id) on delete cascade,
  at timestamptz not null default now()
);
create index regatta_ping_user_idx on public.regatta_ping (user_id, at desc);
create index regatta_ping_seeker_idx on public.regatta_ping (seeker, at desc);
alter table public.regatta_ping enable row level security;
revoke all on public.regatta_ping from public, anon, authenticated;

create function public.regatta_ping_due(p_key text, p_seeker uuid)
returns table (kind text, endpoint text, p256dh text, auth text, telegram_id bigint, lang text, them_name text, them_rating int, them_races int, handle text)
language plpgsql volatile security definer set search_path = '' as $$
declare s public.regatta_seek; h text;
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select * into s from public.regatta_seek x where x.user_id = p_seeker and x.pair_id is null and public.regatta_seek_live(x, interval '10 seconds');
  if not found then return; end if;
  if exists (select 1 from public.regatta_ping p where p.seeker = p_seeker and p.at > now() - interval '30 minutes') then return; end if;
  h := public.regatta_seek_handle(p_seeker);
  return query
    with told as (
      insert into public.regatta_ping (user_id, seeker)
        select c.user_id, p_seeker from (
          select rr.user_id from public.regatta_rating rr
           where rr.user_id <> p_seeker and abs(rr.rating - s.rating) <= 100
             and exists (select 1 from public.regatta_duels d where (d.host_user = rr.user_id or d.guest_user = rr.user_id) and d.started_at > now() - interval '14 days')
             and not exists (select 1 from public.regatta_seek x where x.user_id = rr.user_id and public.regatta_seek_live(x, interval '10 seconds'))
             and not exists (select 1 from public.regatta_ping p where p.user_id = rr.user_id and p.at > now() - interval '1 day')
             and not public.regatta_msg_quiet(rr.user_id)
             and not exists (select 1 from public.regatta_suggest g where g.user_id = rr.user_id and g.kind = 'ready' and g.out_until > now())
             and ((public.regatta_msg_on(rr.user_id, 'push') and exists (select 1 from public.regatta_push p where p.user_id = rr.user_id))
                  or (public.regatta_msg_on(rr.user_id, 'telegram') and public.regatta_tg_writable(rr.user_id) is not null))
           order by abs(rr.rating - s.rating), random() limit 3) c
      returning user_id)
    select 'push'::text, r.endpoint, r.p256dh, r.auth, null::bigint, r.lang, s.name, s.rating, s.races, h
      from told a join public.regatta_push r on r.user_id = a.user_id
     where public.regatta_msg_on(a.user_id, 'push')
    union all
    select 'telegram'::text, null, null, null, t.id,
      coalesce((select r.lang from public.regatta_push r where r.user_id = a.user_id order by r.seen_at desc nulls last limit 1), t.lang, 'en'),
      s.name, s.rating, s.races, h
      from told a join public.users t on t.id = public.regatta_tg_writable(a.user_id)
     where public.regatta_msg_on(a.user_id, 'telegram');
end $$;
revoke all on function public.regatta_ping_due(text, uuid) from public;
grant execute on function public.regatta_ping_due(text, uuid) to anon, authenticated;
