-- Matchmaking for the Regatta game's 1-on-1 races (release 4a of the 1-on-1 plan; the ryc-regatta repo: app/connect/seek,
-- components/duel-finder.tsx, app/[lang]/duel/page.tsx, public/game/match-ui.js `auto`). A signed-in sailor asks to be
-- found a race; the site asks again every few seconds; two seekers are paired, both have ten seconds to say Ready, and the
-- site sends both into the same race: the host (the one who waited longer) with the race's settings, the guest to its link.
--
-- regatta_seek: who is looking, one row an account: rating and rated races then, their wishes (a venue, a yacht, or none),
-- since when (the band widens with it) and when last asked (a seeker unheard 8 s is gone), and the pair they are in.
-- regatta_pairs: a match offered: the code, both accounts and names, the settings, each side's Ready, and its state:
-- offered, then accepted (both Ready), declined (one said no) or expired (12 s and not both Ready).
-- Row-level security on, no policies, grants revoked: the functions alone touch them.
--
-- regatta_seek(wishes): the signed-in sailor's turn. In one step, under one lock, so two seekers can't both take a third:
--   - in a pair: its state (found, with the other sailor, the settings and the seconds left; go, once both are Ready);
--   - else looking: the row kept fresh, and the nearest rating within the band (±100, ±200 from 0:20, ±350 from 0:45 of
--     waiting, both sailors' bands), provisional sailors with each other first, the longest waiting first among equals;
--     a pair made of it, or how many are looking and how many are within the band.
-- A sailor's first three rated races are easy ones: one lap of a short windward–leeward in a medium breeze, at one of the
-- five lightest venues to load (Phuket, Antigua, Muscat, St Barths, Porto Cervo), in a J/70. Otherwise the host's wishes,
-- then the guest's, then the defaults.
-- An accepted pair answers go to each of its sailors for two minutes, however late each screen asks; after that, asking
-- again looks afresh. Neither sailor in it can be paired again meanwhile.
-- regatta_seek_ready(pair, ok): Ready, or Decline (the decliner stops looking; the other goes on). regatta_seek_stop():
-- stop looking, and decline a pair not yet accepted.

create table public.regatta_seek (
  user_id uuid primary key references auth.users (id) on delete cascade,
  name text,
  rating int not null,
  races int not null,
  wishes jsonb not null default '{}'::jsonb,
  since timestamptz not null default now(),
  seen timestamptz not null default now(),
  pair_id uuid
);

create table public.regatta_pairs (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  host_user uuid not null references auth.users (id) on delete cascade,
  guest_user uuid not null references auth.users (id) on delete cascade,
  host_name text,
  guest_name text,
  host_rating int not null,
  guest_rating int not null,
  host_races int not null,
  guest_races int not null,
  settings jsonb not null,
  host_ok boolean,
  guest_ok boolean,
  state text not null default 'offered' check (state in ('offered', 'accepted', 'declined', 'expired')),
  created_at timestamptz not null default now()
);

create index regatta_seek_seen_idx on public.regatta_seek (seen);
alter table public.regatta_seek enable row level security;
alter table public.regatta_pairs enable row level security;
revoke all on public.regatta_seek from public, anon, authenticated;
revoke all on public.regatta_pairs from public, anon, authenticated;

-- an account's name as the site shows it (as regatta_admin_duels finds it)
create function public.regatta_account_name(p_user uuid)
returns text language sql stable security definer set search_path = '' as $$
  select coalesce(nullif(a.raw_user_meta_data ->> 'display_name', ''), nullif(u.name, ''))
    from auth.users a
    left join public.users u on u.id = case when a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,18}$' then (a.raw_app_meta_data ->> 'telegram_id')::bigint end
   where a.id = p_user
$$;

revoke all on function public.regatta_account_name(uuid) from public, anon, authenticated;

-- a new race code, as lib/code.ts makes them, and not one in use
create function public.regatta_new_code()
returns text language plpgsql volatile security definer set search_path = '' as $$
declare
  a text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  c text;
begin
  loop
    c := '';
    for i in 1..6 loop c := c || substr(a, 1 + floor(random() * length(a))::int, 1); end loop;
    exit when not exists (select 1 from public.regatta_pairs p where p.code = c)
      and not exists (select 1 from public.regatta_duels d where d.code = c)
      and not exists (select 1 from public.regatta_invites i where i.code = c);
  end loop;
  return c;
end $$;

revoke all on function public.regatta_new_code() from public, anon, authenticated;

-- a pair's state for one of its two sailors, as regatta_seek tells it
create function public.regatta_pair_view(p public.regatta_pairs, me uuid)
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
    'left', greatest(0, 12 - extract(epoch from now() - p.created_at))::numeric(4, 1),
    'minutes', public.regatta_duel_minutes(p.settings ->> 'yacht', p.settings ->> 'length', (p.settings ->> 'laps')::int, (p.settings ->> 'start')::int))
$$;

revoke all on function public.regatta_pair_view(public.regatta_pairs, uuid) from public, anon, authenticated;

create function public.regatta_seek(p_wishes jsonb default '{}'::jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  o public.regatta_seek;
  p public.regatta_pairs;
  r public.regatta_rating;
  band int;
  waited numeric;
  light text[] := array['phuket', 'antigua', 'muscat', 'st-barths', 'porto-cervo'];
  host public.regatta_seek;
  guest public.regatta_seek;
  wv text;
  wy text;
  settings jsonb;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));

  -- a pair already: its state
  select * into s from public.regatta_seek where user_id = me;
  if found and s.pair_id is not null then
    select * into p from public.regatta_pairs where id = s.pair_id;
    if found then
      if p.state = 'offered' and now() - p.created_at > interval '12 seconds' then
        update public.regatta_pairs set state = 'expired' where id = p.id returning * into p;
        -- whoever didn't say Ready has walked away; the one who did goes on looking
        delete from public.regatta_seek x where x.pair_id = p.id
          and ((x.user_id = p.host_user and p.host_ok is not true) or (x.user_id = p.guest_user and p.guest_ok is not true));
        update public.regatta_seek x set pair_id = null where x.pair_id = p.id;
      end if;
      if p.state = 'accepted' and now() - p.created_at < interval '2 minutes' then
        return jsonb_build_object('status', 'go', 'pair', public.regatta_pair_view(p, me)); -- (both screens told, however late each asks)
      elsif p.state = 'offered' then
        update public.regatta_seek set seen = now() where user_id = me;
        return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
      end if;
      if p.state = 'accepted' then update public.regatta_seek set pair_id = null, since = now() where user_id = me; end if; -- (a race long gone: looking afresh)
      select * into s from public.regatta_seek where user_id = me; -- (gone, or back to looking)
      if not found then return jsonb_build_object('status', 'none', 'reason', p.state); end if;
    end if;
  end if;

  -- looking: the row kept fresh (a seeker gone 15 s starts again)
  select * into r from public.regatta_rating where user_id = me;
  insert into public.regatta_seek as x (user_id, name, rating, races, wishes)
  values (me, public.regatta_account_name(me), coalesce(r.rating, 1500), coalesce(r.races, 0), coalesce(p_wishes, '{}'::jsonb))
  on conflict (user_id) do update set
    seen = now(), wishes = excluded.wishes, rating = excluded.rating, races = excluded.races, name = excluded.name,
    since = case when x.seen < now() - interval '15 seconds' then now() else x.since end
  returning * into s;
  waited := extract(epoch from now() - s.since);
  band := case when waited < 20 then 100 when waited < 45 then 200 else 350 end;

  -- the nearest within both bands, provisional with provisional first, the longest waiting first among equals
  select * into o from public.regatta_seek x
   where x.user_id <> me and x.pair_id is null and x.seen > now() - interval '8 seconds'
     and abs(x.rating - s.rating) <= least(band, case when extract(epoch from now() - x.since) < 20 then 100 when extract(epoch from now() - x.since) < 45 then 200 else 350 end)
   order by ((x.races < 5) = (s.races < 5)) desc, abs(x.rating - s.rating), x.since
   limit 1;

  if not found then
    return jsonb_build_object('status', 'looking', 'waited', round(waited), 'band', band,
      'online', (select count(*) from public.regatta_seek x where x.seen > now() - interval '10 seconds'),
      'near', (select count(*) from public.regatta_seek x where x.user_id <> me and x.seen > now() - interval '10 seconds' and abs(x.rating - s.rating) <= 350));
  end if;

  -- a pair: the one who waited longer hosts
  if o.since < s.since then host := o; guest := s; else host := s; guest := o; end if;
  if host.races < 3 or guest.races < 3 then
    settings := jsonb_build_object('venue', light[1 + floor(random() * array_length(light, 1))::int], 'yacht', 'j70', 'preset', 'medium', 'length', 'short',
      'course', 'wl', 'laps', 1, 'start', 1, 'current', 0, 'daytime', 'any');
  else
    wv := coalesce(nullif(host.wishes ->> 'venue', ''), nullif(guest.wishes ->> 'venue', ''), light[1 + floor(random() * array_length(light, 1))::int]);
    wy := coalesce(nullif(host.wishes ->> 'yacht', ''), nullif(guest.wishes ->> 'yacht', ''), 'j70');
    settings := jsonb_build_object('venue', wv, 'yacht', wy, 'preset', 'medium', 'length', 'short', 'course', 'wl', 'laps', 1, 'start', 1, 'current', 0, 'daytime', 'any');
  end if;
  insert into public.regatta_pairs (code, host_user, guest_user, host_name, guest_name, host_rating, guest_rating, host_races, guest_races, settings)
  values (public.regatta_new_code(), host.user_id, guest.user_id, host.name, guest.name, host.rating, guest.rating, host.races, guest.races, settings)
  returning * into p;
  update public.regatta_seek set pair_id = p.id where user_id in (host.user_id, guest.user_id);
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;

revoke all on function public.regatta_seek(jsonb) from public, anon;
grant execute on function public.regatta_seek(jsonb) to authenticated;

create function public.regatta_seek_ready(p_pair uuid, p_ok boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  p public.regatta_pairs;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select * into p from public.regatta_pairs where id = p_pair and me in (host_user, guest_user) and state = 'offered'
     and now() - created_at <= interval '12 seconds';
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

revoke all on function public.regatta_seek_ready(uuid, boolean) from public, anon;
grant execute on function public.regatta_seek_ready(uuid, boolean) to authenticated;

create function public.regatta_seek_stop()
returns void language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  pid uuid;
begin
  if me is null then return; end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select pair_id into pid from public.regatta_seek where user_id = me;
  delete from public.regatta_seek where user_id = me;
  if pid is not null then
    update public.regatta_pairs set state = 'declined' where id = pid and state = 'offered';
    update public.regatta_seek x set pair_id = null where x.pair_id = pid;
  end if;
end $$;

revoke all on function public.regatta_seek_stop() from public, anon;
grant execute on function public.regatta_seek_stop() to authenticated;
