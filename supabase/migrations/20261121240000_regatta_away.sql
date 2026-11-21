-- Keep looking when you leave, and a message when a sailor is found (release 5b of the 1-on-1 plan; the ryc-regatta repo:
-- /duel, components/duel-finder.tsx, app/connect/seek, app/connect/push-link, lib/push-send.ts, public/sw.js).
--
-- A browser's push subscription (regatta_push, the daily reminder's) is tied to the signed-in account as well
-- (regatta_push_link). A sailor looking for a race on a device that can be messaged may ask to go on looking after
-- leaving the page, for 30 minutes (regatta_seek_away). Such an away seeker is paired, offered in Ready now and can be
-- challenged as if on the page; a pair with an away sailor gives a minute to say Ready rather than 12 s (regatta_pairs.ttl),
-- time for a message to come and be opened. The site, having made the pair, asks regatta_pair_push (with the key the daily
-- reminder's list takes) for the away sailor's devices, once per pair, and sends each a push that opens /duel at Match found.
--
-- Recreated with the pair's own time to answer: regatta_make_pair, regatta_seek, regatta_pair_view, regatta_seek_ready,
-- regatta_ready_now, regatta_seek_challenge, regatta_call_state.

alter table public.regatta_push add column user_id uuid references auth.users (id) on delete set null;
create index regatta_push_user_idx on public.regatta_push (user_id) where user_id is not null;
alter table public.regatta_seek add column away_until timestamptz;
alter table public.regatta_pairs add column ttl int not null default 12, add column pushed_at timestamptz;

-- this browser's subscription is the signed-in sailor's too
create function public.regatta_push_link(p_endpoint text)
returns boolean language plpgsql volatile security definer set search_path = '' as $$
declare me uuid := auth.uid();
begin
  if me is null or p_endpoint is null then return false; end if;
  update public.regatta_push set user_id = me, seen_at = now() where endpoint = p_endpoint;
  return found;
end $$;

revoke all on function public.regatta_push_link(text) from public, anon;
grant execute on function public.regatta_push_link(text) to authenticated;

-- a seeker on the page now, or one gone from it who asked to be looked for still
create function public.regatta_seek_live(x public.regatta_seek, p_seen interval default interval '8 seconds')
returns boolean language sql stable set search_path = '' as $$
  select x.seen > now() - p_seen or (x.away_until is not null and x.away_until > now())
$$;
create function public.regatta_seek_is_away(x public.regatta_seek)
returns boolean language sql stable set search_path = '' as $$
  select x.seen <= now() - interval '8 seconds' and x.away_until is not null and x.away_until > now()
$$;
revoke all on function public.regatta_seek_live(public.regatta_seek, interval) from public, anon, authenticated;
revoke all on function public.regatta_seek_is_away(public.regatta_seek) from public, anon, authenticated;

-- go on looking after leaving the page (on), or not (off): only while looking, and only with a device to message
create function public.regatta_seek_away(p_on boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  n int;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  if not coalesce(p_on, false) then
    update public.regatta_seek set away_until = null where user_id = me;
    return jsonb_build_object('status', 'here');
  end if;
  select count(*) into n from public.regatta_push where user_id = me;
  if n = 0 then return jsonb_build_object('status', 'none', 'reason', 'no_push'); end if;
  update public.regatta_seek set away_until = now() + interval '30 minutes'
   where user_id = me and seen > now() - interval '10 seconds' and pair_id is null
  returning * into s;
  if not found then return jsonb_build_object('status', 'none', 'reason', 'not_looking'); end if;
  return jsonb_build_object('status', 'away', 'left', round(extract(epoch from s.away_until - now())), 'devices', n);
end $$;

revoke all on function public.regatta_seek_away(boolean) from public, anon;
grant execute on function public.regatta_seek_away(boolean) to authenticated;

-- a pair: as before, and a minute to answer when one of the two is away (a message has to reach them)
create or replace function public.regatta_make_pair(a public.regatta_seek, b public.regatta_seek)
returns public.regatta_pairs language plpgsql volatile security definer set search_path = '' as $$
declare
  light text[] := array['phuket', 'antigua', 'muscat', 'st-barths', 'porto-cervo'];
  host public.regatta_seek;
  guest public.regatta_seek;
  settings jsonb;
  p public.regatta_pairs;
begin
  if b.since < a.since then host := b; guest := a; else host := a; guest := b; end if;
  if host.races < 3 or guest.races < 3 then
    settings := jsonb_build_object('venue', light[1 + floor(random() * array_length(light, 1))::int], 'yacht', 'j70', 'preset', 'medium', 'length', 'short',
      'course', 'wl', 'laps', 1, 'start', 1, 'current', 0, 'daytime', 'any');
  else
    settings := jsonb_build_object(
      'venue', coalesce(nullif(host.wishes ->> 'venue', ''), nullif(guest.wishes ->> 'venue', ''), light[1 + floor(random() * array_length(light, 1))::int]),
      'yacht', coalesce(nullif(host.wishes ->> 'yacht', ''), nullif(guest.wishes ->> 'yacht', ''), 'j70'),
      'preset', 'medium', 'length', 'short', 'course', 'wl', 'laps', 1, 'start', 1, 'current', 0, 'daytime', 'any');
  end if;
  insert into public.regatta_pairs (code, host_user, guest_user, host_name, guest_name, host_rating, guest_rating, host_races, guest_races, settings, ttl)
  values (public.regatta_new_code(), host.user_id, guest.user_id, host.name, guest.name, host.rating, guest.rating, host.races, guest.races, settings,
    case when public.regatta_seek_is_away(a) or public.regatta_seek_is_away(b) then 60 else 12 end)
  returning * into p;
  update public.regatta_seek set pair_id = p.id where user_id in (host.user_id, guest.user_id);
  return p;
end $$;

create or replace function public.regatta_pair_view(p public.regatta_pairs, me uuid)
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'id', p.id, 'code', p.code, 'role', case when p.host_user = me then 'host' else 'guest' end, 'settings', p.settings,
    'them', case when p.host_user = me
      then jsonb_build_object('name', p.guest_name, 'rating', p.guest_rating, 'races', p.guest_races)
      else jsonb_build_object('name', p.host_name, 'rating', p.host_rating, 'races', p.host_races) end,
    'me', case when p.host_user = me
      then jsonb_build_object('rating', p.host_rating, 'races', p.host_races, 'ok', p.host_ok)
      else jsonb_build_object('rating', p.guest_rating, 'races', p.guest_races, 'ok', p.guest_ok) end,
    'them_ok', case when p.host_user = me then p.guest_ok else p.host_ok end,
    'left', greatest(0, p.ttl - extract(epoch from now() - p.created_at))::numeric(4, 1),
    'ttl', p.ttl,
    'minutes', public.regatta_duel_minutes(p.settings ->> 'yacht', p.settings ->> 'length', (p.settings ->> 'laps')::int, (p.settings ->> 'start')::int))
$$;

create or replace function public.regatta_seek(p_wishes jsonb default '{}'::jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  o public.regatta_seek;
  p public.regatta_pairs;
  r public.regatta_rating;
  band int;
  waited numeric;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));

  -- a pair already: its state
  select * into s from public.regatta_seek where user_id = me;
  if found and s.pair_id is not null then
    select * into p from public.regatta_pairs where id = s.pair_id;
    if found then
      if p.state = 'offered' and now() - p.created_at > make_interval(secs => p.ttl) then
        update public.regatta_pairs set state = 'expired' where id = p.id returning * into p;
        -- whoever didn't say Ready has walked away; the one who did goes on looking
        delete from public.regatta_seek x where x.pair_id = p.id
          and ((x.user_id = p.host_user and p.host_ok is not true) or (x.user_id = p.guest_user and p.guest_ok is not true));
        update public.regatta_seek x set pair_id = null where x.pair_id = p.id;
      end if;
      if p.state = 'accepted' and now() - p.created_at < interval '2 minutes' then
        update public.regatta_seek set seen = now(), away_until = null where user_id = me;
        return jsonb_build_object('status', 'go', 'pair', public.regatta_pair_view(p, me)); -- (both screens told, however late each asks)
      elsif p.state = 'offered' then
        update public.regatta_seek set seen = now() where user_id = me;
        return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
      end if;
      if p.state = 'accepted' then update public.regatta_seek set pair_id = null, since = now(), away_until = null where user_id = me; end if; -- (a race long gone: looking afresh)
      select * into s from public.regatta_seek where user_id = me; -- (gone, or back to looking)
      if not found then return jsonb_build_object('status', 'none', 'reason', p.state); end if;
    end if;
  end if;

  -- looking: the row kept fresh (a seeker gone 15 s, and not looked for while away, starts again)
  select * into r from public.regatta_rating where user_id = me;
  insert into public.regatta_seek as x (user_id, name, rating, races, wishes)
  values (me, public.regatta_account_name(me), coalesce(r.rating, 1500), coalesce(r.races, 0), coalesce(p_wishes, '{}'::jsonb))
  on conflict (user_id) do update set
    seen = now(), wishes = excluded.wishes, rating = excluded.rating, races = excluded.races, name = excluded.name,
    since = case when x.seen < now() - interval '15 seconds' and not (x.away_until is not null and x.away_until > now()) then now() else x.since end
  returning * into s;
  waited := extract(epoch from now() - s.since);
  band := case when waited < 20 then 100 when waited < 45 then 200 else 350 end;

  -- the nearest within both bands, on the page or away, provisional with provisional first, the longest waiting first
  select * into o from public.regatta_seek x
   where x.user_id <> me and x.pair_id is null and public.regatta_seek_live(x)
     and abs(x.rating - s.rating) <= least(band, case when extract(epoch from now() - x.since) < 20 then 100 when extract(epoch from now() - x.since) < 45 then 200 else 350 end)
   order by ((x.races < 5) = (s.races < 5)) desc, abs(x.rating - s.rating), x.since
   limit 1;

  if not found then
    return jsonb_build_object('status', 'looking', 'waited', round(waited), 'band', band,
      'online', (select count(*) from public.regatta_seek x where public.regatta_seek_live(x, interval '10 seconds')),
      'near', (select count(*) from public.regatta_seek x where x.user_id <> me and public.regatta_seek_live(x, interval '10 seconds') and abs(x.rating - s.rating) <= 350),
      'away', s.away_until is not null and s.away_until > now());
  end if;

  p := public.regatta_make_pair(s, o);
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;

create or replace function public.regatta_seek_ready(p_pair uuid, p_ok boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  p public.regatta_pairs;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select * into p from public.regatta_pairs where id = p_pair and me in (host_user, guest_user) and state = 'offered'
     and now() - created_at <= make_interval(secs => ttl);
  if not found then return jsonb_build_object('status', 'none'); end if;
  if p_ok then
    update public.regatta_pairs x set
      host_ok = case when x.host_user = me then true else x.host_ok end,
      guest_ok = case when x.guest_user = me then true else x.guest_ok end
    where x.id = p.id returning * into p;
    if p.host_ok and p.guest_ok then
      update public.regatta_pairs set state = 'accepted' where id = p.id returning * into p; -- (both rows keep the pair: each screen is told go as it asks)
      return jsonb_build_object('status', 'go', 'pair', public.regatta_pair_view(p, me));
    end if;
    return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
  end if;
  -- Decline: the pair is over; the decliner stops looking, the other goes on
  update public.regatta_pairs set state = 'declined' where id = p.id;
  delete from public.regatta_seek where user_id = me;
  update public.regatta_seek x set pair_id = null where x.pair_id = p.id;
  return jsonb_build_object('status', 'none', 'reason', 'declined');
end $$;

-- Ready now: on the page or away (away: they're sent a message, and have a minute)
create or replace function public.regatta_ready_now()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  mine int;
begin
  if me is null then return '[]'::jsonb; end if;
  select coalesce((select rating from public.regatta_rating where user_id = me), 1500) into mine;
  return coalesce((
    select jsonb_agg(jsonb_build_object('handle', public.regatta_seek_handle(x.user_id), 'name', x.name, 'rating', x.rating, 'races', x.races,
        'waited', round(extract(epoch from now() - x.since)), 'away', public.regatta_seek_is_away(x)) order by abs(x.rating - mine), x.since)
      from (select * from public.regatta_seek x where x.user_id <> me and x.pair_id is null and public.regatta_seek_live(x, interval '10 seconds')
             order by abs(x.rating - mine), x.since limit 20) x), '[]'::jsonb);
end $$;

create or replace function public.regatta_seek_challenge(p_handle text, p_wishes jsonb default '{}'::jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  o public.regatta_seek;
  r public.regatta_rating;
  p public.regatta_pairs;
begin
  if me is null or p_handle is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select * into s from public.regatta_seek where user_id = me;
  if found and s.pair_id is not null then return public.regatta_seek(p_wishes); end if; -- (in a pair already: that one)
  select * into o from public.regatta_seek x
   where public.regatta_seek_handle(x.user_id) = p_handle and x.user_id <> me and x.pair_id is null and public.regatta_seek_live(x, interval '10 seconds');
  if not found then return jsonb_build_object('status', 'none', 'reason', 'gone'); end if;
  select * into r from public.regatta_rating where user_id = me;
  insert into public.regatta_seek as x (user_id, name, rating, races, wishes)
  values (me, public.regatta_account_name(me), coalesce(r.rating, 1500), coalesce(r.races, 0), coalesce(p_wishes, '{}'::jsonb))
  on conflict (user_id) do update set seen = now(), wishes = excluded.wishes, rating = excluded.rating, races = excluded.races, name = excluded.name
  returning * into s;
  p := public.regatta_make_pair(s, o);
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;

-- an open call: taken while its pair has its own time to answer; the caller away is still the caller (looked for)
create or replace function public.regatta_call_state(c public.regatta_call)
returns text language plpgsql stable security definer set search_path = '' as $$
declare
  p public.regatta_pairs;
  s public.regatta_seek;
begin
  if c.pair_id is not null then
    select * into p from public.regatta_pairs where id = c.pair_id;
    if found and (p.state = 'accepted' or (p.state = 'offered' and now() - p.created_at <= make_interval(secs => p.ttl))) then return 'taken'; end if;
  end if;
  if now() > c.closes_at then return 'closed'; end if;
  select * into s from public.regatta_seek where user_id = c.user_id;
  if not found or not public.regatta_seek_live(s, interval '30 seconds') or s.pair_id is not null then return 'away'; end if;
  return 'open';
end $$;

-- the away sailors of a pair just made, to be sent a message: their devices, once per pair; only with the key in the
-- vault (regatta_push_key, the daily reminder's), so only the site's server asks
create function public.regatta_pair_push(p_key text, p_pair uuid)
returns table (endpoint text, p256dh text, auth text, lang text, them_name text, them_rating int, them_races int, ttl int)
language plpgsql volatile security definer set search_path = '' as $$
declare p public.regatta_pairs;
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  update public.regatta_pairs x set pushed_at = now() where x.id = p_pair and x.pushed_at is null and x.state = 'offered' returning * into p;
  if not found then return; end if;
  return query
    select r.endpoint, r.p256dh, r.auth, r.lang,
      case when u.user_id = p.host_user then p.guest_name else p.host_name end,
      case when u.user_id = p.host_user then p.guest_rating else p.host_rating end,
      case when u.user_id = p.host_user then p.guest_races else p.host_races end,
      p.ttl
    from public.regatta_seek u join public.regatta_push r on r.user_id = u.user_id
    where u.pair_id = p.id and public.regatta_seek_is_away(u);
end $$;

revoke all on function public.regatta_pair_push(text, uuid) from public;
grant execute on function public.regatta_pair_push(text, uuid) to anon, authenticated;
