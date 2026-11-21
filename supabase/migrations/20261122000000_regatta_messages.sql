-- Which messages come, and quiet hours (release 5d of the 1-on-1 plan; the ryc-regatta repo: the Messages card on
-- /settings, components/messages-form.tsx, app/connect/messages).
--
-- regatta_msg: a sailor's choices, by account: Match found by browser push (push) and from the Telegram bot (telegram),
-- both on until turned off; and quiet hours, from and to in their own time zone (whole hours; none by default). In quiet
-- hours nothing is sent: no Match found (regatta_pair_push), no daily reminder to a browser tied to the account
-- (regatta_push_due), and "Keep looking if I leave" is refused (regatta_seek_away: quiet), as nobody could be told.
-- regatta_msg_get(): the choices, what can reach the sailor (browsers tied to the account, the bot) and whether it is quiet
-- now. regatta_msg_set(push, telegram, quiet_from, quiet_to, tz): saved; a time zone Postgres doesn't know is UTC.

create table public.regatta_msg (
  user_id uuid primary key references auth.users (id) on delete cascade,
  push boolean not null default true,
  telegram boolean not null default true,
  quiet_from smallint check (quiet_from between 0 and 23),
  quiet_to smallint check (quiet_to between 0 and 23),
  tz text not null default 'UTC',
  updated_at timestamptz not null default now()
);
alter table public.regatta_msg enable row level security;
revoke all on public.regatta_msg from public, anon, authenticated;

-- is it this sailor's quiet hours at this moment (their own time zone; from 23 to 7 wraps past midnight)
create function public.regatta_msg_quiet(p_user uuid, p_at timestamptz default now())
returns boolean language sql stable security definer set search_path = '' as $$
  select coalesce((
    select case
      when m.quiet_from is null or m.quiet_to is null or m.quiet_from = m.quiet_to then false
      when m.quiet_from < m.quiet_to then h >= m.quiet_from and h < m.quiet_to
      else h >= m.quiet_from or h < m.quiet_to end
    from public.regatta_msg m, lateral (select extract(hour from p_at at time zone m.tz)::int as h) x
    where m.user_id = p_user), false)
$$;
-- does this sailor take Match found this way (push or telegram); on unless turned off
create function public.regatta_msg_on(p_user uuid, p_kind text)
returns boolean language sql stable security definer set search_path = '' as $$
  select coalesce((select case when p_kind = 'push' then m.push else m.telegram end from public.regatta_msg m where m.user_id = p_user), true)
$$;
revoke all on function public.regatta_msg_quiet(uuid, timestamptz) from public, anon, authenticated;
revoke all on function public.regatta_msg_on(uuid, text) from public, anon, authenticated;

create function public.regatta_msg_get()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  m public.regatta_msg;
begin
  if me is null then return null; end if;
  select * into m from public.regatta_msg where user_id = me;
  return jsonb_build_object('push', coalesce(m.push, true), 'telegram', coalesce(m.telegram, true),
    'quiet_from', m.quiet_from, 'quiet_to', m.quiet_to, 'tz', coalesce(m.tz, 'UTC'),
    'browsers', (select count(*) from public.regatta_push r where r.user_id = me),
    'bot', public.regatta_tg_writable(me) is not null,
    'quiet_now', public.regatta_msg_quiet(me));
end $$;

create function public.regatta_msg_set(p_push boolean, p_telegram boolean, p_quiet_from int, p_quiet_to int, p_tz text)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  z text := case when p_tz is not null and length(p_tz) <= 64 and exists (select 1 from pg_catalog.pg_timezone_names n where n.name = p_tz) then p_tz else 'UTC' end;
  f int := case when p_quiet_from between 0 and 23 and p_quiet_to between 0 and 23 and p_quiet_from <> p_quiet_to then p_quiet_from end;
  t int := case when p_quiet_from between 0 and 23 and p_quiet_to between 0 and 23 and p_quiet_from <> p_quiet_to then p_quiet_to end;
begin
  if me is null then return null; end if;
  insert into public.regatta_msg as x (user_id, push, telegram, quiet_from, quiet_to, tz)
  values (me, coalesce(p_push, true), coalesce(p_telegram, true), f, t, z)
  on conflict (user_id) do update set push = excluded.push, telegram = excluded.telegram, quiet_from = excluded.quiet_from,
    quiet_to = excluded.quiet_to, tz = excluded.tz, updated_at = now();
  return public.regatta_msg_get();
end $$;

revoke all on function public.regatta_msg_get() from public, anon;
grant execute on function public.regatta_msg_get() to authenticated;
revoke all on function public.regatta_msg_set(boolean, boolean, int, int, text) from public, anon;
grant execute on function public.regatta_msg_set(boolean, boolean, int, int, text) to authenticated;

-- away: only by the ways the sailor takes Match found, and not in their quiet hours
create or replace function public.regatta_seek_away(p_on boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  n int;
  tg boolean;
  any_way boolean;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  if not coalesce(p_on, false) then
    update public.regatta_seek set away_until = null where user_id = me;
    return jsonb_build_object('status', 'here');
  end if;
  if public.regatta_msg_quiet(me) then return jsonb_build_object('status', 'none', 'reason', 'quiet'); end if;
  select count(*) into n from public.regatta_push where user_id = me;
  tg := public.regatta_tg_writable(me) is not null;
  any_way := n > 0 or tg;
  if not public.regatta_msg_on(me, 'push') then n := 0; end if;
  if not public.regatta_msg_on(me, 'telegram') then tg := false; end if;
  if n = 0 and not tg then return jsonb_build_object('status', 'none', 'reason', case when any_way then 'off' else 'no_push' end); end if;
  update public.regatta_seek set away_until = now() + interval '30 minutes'
   where user_id = me and seen > now() - interval '10 seconds' and pair_id is null
  returning * into s;
  if not found then return jsonb_build_object('status', 'none', 'reason', 'not_looking'); end if;
  return jsonb_build_object('status', 'away', 'left', round(extract(epoch from s.away_until - now())), 'devices', n + case when tg then 1 else 0 end, 'telegram', tg);
end $$;

-- Match found: only the ways the sailor takes it, and nothing in their quiet hours
create or replace function public.regatta_pair_push(p_key text, p_pair uuid)
returns table (kind text, endpoint text, p256dh text, auth text, telegram_id bigint, lang text, them_name text, them_rating int, them_races int, ttl int)
language plpgsql volatile security definer set search_path = '' as $$
declare p public.regatta_pairs;
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  update public.regatta_pairs x set pushed_at = now() where x.id = p_pair and x.pushed_at is null and x.state = 'offered' returning * into p;
  if not found then return; end if;
  return query
    with away as (
      select u.user_id,
        case when u.user_id = p.host_user then p.guest_name else p.host_name end as them_name,
        case when u.user_id = p.host_user then p.guest_rating else p.host_rating end as them_rating,
        case when u.user_id = p.host_user then p.guest_races else p.host_races end as them_races
      from public.regatta_seek u where u.pair_id = p.id and public.regatta_seek_is_away(u) and not public.regatta_msg_quiet(u.user_id))
    select 'push'::text, r.endpoint, r.p256dh, r.auth, null::bigint, r.lang, a.them_name, a.them_rating, a.them_races, p.ttl
      from away a join public.regatta_push r on r.user_id = a.user_id
     where public.regatta_msg_on(a.user_id, 'push')
    union all
    select 'telegram'::text, null, null, null, t.id,
      coalesce((select r.lang from public.regatta_push r where r.user_id = a.user_id order by r.seen_at desc nulls last limit 1), t.lang, 'en'),
      a.them_name, a.them_rating, a.them_races, p.ttl
      from away a join public.users t on t.id = public.regatta_tg_writable(a.user_id)
     where public.regatta_msg_on(a.user_id, 'telegram');
end $$;

-- the daily reminder: not to a browser whose sailor is in quiet hours (it is not marked sent, so it may go another day)
create or replace function public.regatta_push_due(p_key text, p_day date)
returns table(endpoint text, p256dh text, auth text, lang text, last_day date, streak integer)
language plpgsql security definer set search_path = '' as $$
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query
    update public.regatta_push r set sent_day = p_day
    where r.sent_day is distinct from p_day
      and r.last_day is distinct from p_day
      and greatest(r.last_day, r.created_at::date) >= p_day - 14
      and (r.user_id is null or not public.regatta_msg_quiet(r.user_id))
    returning r.endpoint, r.p256dh, r.auth, r.lang, r.last_day, r.streak;
end;
$$;
