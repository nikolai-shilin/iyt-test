-- The duel hour (release 6d of the 1-on-1 plan; the ryc-regatta repo: components/duel-finder.tsx, app/push/hour).
-- Every day from 19:00 to 20:00 UTC sailors gather for 1-on-1 races, so there is someone at your level. A signed-in
-- sailor says "I'm in" for the next one, and gets a message 15 minutes before it: by the browsers tied to their account
-- and from the Telegram bot, as they take Match found (regatta_msg), and never in their quiet hours.
--
-- regatta_hour: who is in for which day's hour (the UTC date it falls on), and when they were told.
-- regatta_hour_day(at): the day of the next hour, or of this one while it is on: today until 20:00 UTC, then tomorrow.
-- regatta_hour_state(): for anyone, that day, how many are in, and for a signed-in sailor how many of them are within
--   100 of their rating, whether they are in, and whether a message can reach them (a browser tied to the account, or
--   the bot).
-- regatta_hour_join(in): in, or out, for that day's hour; the state after.
-- regatta_hour_due(key, day): the messages to send for that day's hour, once each sailor (marked told), with the
--   daily reminder's key (vault regatta_push_key): their browsers, the bot, how many are in.

create table public.regatta_hour (
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null,
  at timestamptz not null default now(),
  told_at timestamptz,
  primary key (user_id, day)
);
create index regatta_hour_day_idx on public.regatta_hour (day);
alter table public.regatta_hour enable row level security;
revoke all on public.regatta_hour from public, anon, authenticated;

create function public.regatta_hour_day(p_at timestamptz default now())
returns date language sql stable set search_path = '' as $$
  select case when (p_at at time zone 'UTC')::time < time '20:00' then (p_at at time zone 'UTC')::date
              else (p_at at time zone 'UTC')::date + 1 end
$$;

create function public.regatta_hour_state()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  d date := public.regatta_hour_day();
  mine int;
begin
  if me is null then
    return jsonb_build_object('day', d, 'in', (select count(*) from public.regatta_hour h where h.day = d));
  end if;
  select coalesce((select rating from public.regatta_rating where user_id = me), 1500) into mine;
  return jsonb_build_object('day', d,
    'in', (select count(*) from public.regatta_hour h where h.day = d),
    'near', (select count(*) from public.regatta_hour h left join public.regatta_rating r on r.user_id = h.user_id
              where h.day = d and h.user_id <> me and abs(coalesce(r.rating, 1500) - mine) <= 100),
    'me', exists (select 1 from public.regatta_hour h where h.day = d and h.user_id = me),
    'reach', exists (select 1 from public.regatta_push r where r.user_id = me) or public.regatta_tg_writable(me) is not null);
end $$;
revoke all on function public.regatta_hour_state() from public;
grant execute on function public.regatta_hour_state() to anon, authenticated;

create function public.regatta_hour_join(p_in boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  d date := public.regatta_hour_day();
begin
  if me is null then return public.regatta_hour_state(); end if;
  if coalesce(p_in, false) then
    insert into public.regatta_hour (user_id, day) values (me, d) on conflict do nothing;
  else
    delete from public.regatta_hour where user_id = me and day = d;
  end if;
  return public.regatta_hour_state();
end $$;
revoke all on function public.regatta_hour_join(boolean) from public, anon;
grant execute on function public.regatta_hour_join(boolean) to authenticated;

-- each sailor in is told once: those in quiet hours are not told (nor marked, so a second call later may still reach
-- them); a sailor nothing can reach is marked all the same
create function public.regatta_hour_due(p_key text, p_day date)
returns table (kind text, endpoint text, p256dh text, auth text, telegram_id bigint, lang text, n_in int)
language plpgsql volatile security definer set search_path = '' as $$
declare n int;
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select count(*) into n from public.regatta_hour h where h.day = p_day;
  return query
    with told as (
      update public.regatta_hour h set told_at = now()
       where h.day = p_day and h.told_at is null and not public.regatta_msg_quiet(h.user_id)
      returning h.user_id)
    select 'push'::text, r.endpoint, r.p256dh, r.auth, null::bigint, r.lang, n
      from told a join public.regatta_push r on r.user_id = a.user_id
     where public.regatta_msg_on(a.user_id, 'push')
    union all
    select 'telegram'::text, null, null, null, t.id,
      coalesce((select r.lang from public.regatta_push r where r.user_id = a.user_id order by r.seen_at desc nulls last limit 1), t.lang, 'en'), n
      from told a join public.users t on t.id = public.regatta_tg_writable(a.user_id)
     where public.regatta_msg_on(a.user_id, 'telegram');
end $$;
revoke all on function public.regatta_hour_due(text, date) from public;
grant execute on function public.regatta_hour_due(text, date) to anon, authenticated;
