-- Ready now and a direct challenge, for the 1-on-1 page (release 4b of the 1-on-1 plan; the ryc-regatta repo: /duel,
-- components/duel-finder.tsx, app/connect/seek).
--
-- regatta_make_pair(a, b): a pair of two seekers, as Find a race always made one (20261121200000_regatta_seek.sql): the one who
-- waited longer hosts; a sailor's first three rated races easy; else the host's wishes, the guest's, the defaults. Now shared by
-- regatta_seek and regatta_seek_challenge.
-- regatta_ready_now(): for a signed-in sailor, who else is looking now (asked within the last 10 s, in no pair): a handle (not
-- their account), name, rating, races and how long they have waited, the nearest rating first, twenty at most.
-- regatta_seek_challenge(handle, wishes): pair with that sailor at once, whatever the band (a deliberate challenge), if they
-- are still looking; the challenger becomes a seeker if they weren't. Both then see Match found as from Find a race.

create function public.regatta_make_pair(a public.regatta_seek, b public.regatta_seek)
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
  insert into public.regatta_pairs (code, host_user, guest_user, host_name, guest_name, host_rating, guest_rating, host_races, guest_races, settings)
  values (public.regatta_new_code(), host.user_id, guest.user_id, host.name, guest.name, host.rating, guest.rating, host.races, guest.races, settings)
  returning * into p;
  update public.regatta_seek set pair_id = p.id where user_id in (host.user_id, guest.user_id);
  return p;
end $$;

revoke all on function public.regatta_make_pair(public.regatta_seek, public.regatta_seek) from public, anon, authenticated;

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

  -- a pair: made as a challenge makes one (regatta_make_pair)
  p := public.regatta_make_pair(s, o);
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;


revoke all on function public.regatta_seek(jsonb) from public, anon;
grant execute on function public.regatta_seek(jsonb) to authenticated;

-- a seeker's handle, as Ready now names them: stable, and not their account
create function public.regatta_seek_handle(p_user uuid)
returns text language sql immutable set search_path = '' as $$ select left(md5('regatta-seek:' || p_user::text), 12) $$;

revoke all on function public.regatta_seek_handle(uuid) from public, anon, authenticated;

create function public.regatta_ready_now()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  mine int;
begin
  if me is null then return '[]'::jsonb; end if;
  select coalesce((select rating from public.regatta_rating where user_id = me), 1500) into mine;
  return coalesce((
    select jsonb_agg(jsonb_build_object('handle', public.regatta_seek_handle(x.user_id), 'name', x.name, 'rating', x.rating, 'races', x.races,
        'waited', round(extract(epoch from now() - x.since))) order by abs(x.rating - mine), x.since)
      from (select * from public.regatta_seek x where x.user_id <> me and x.pair_id is null and x.seen > now() - interval '10 seconds'
             order by abs(x.rating - mine), x.since limit 20) x), '[]'::jsonb);
end $$;

revoke all on function public.regatta_ready_now() from public, anon;
grant execute on function public.regatta_ready_now() to authenticated;

create function public.regatta_seek_challenge(p_handle text, p_wishes jsonb default '{}'::jsonb)
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
   where public.regatta_seek_handle(x.user_id) = p_handle and x.user_id <> me and x.pair_id is null and x.seen > now() - interval '10 seconds';
  if not found then return jsonb_build_object('status', 'none', 'reason', 'gone'); end if;
  select * into r from public.regatta_rating where user_id = me;
  insert into public.regatta_seek as x (user_id, name, rating, races, wishes)
  values (me, public.regatta_account_name(me), coalesce(r.rating, 1500), coalesce(r.races, 0), coalesce(p_wishes, '{}'::jsonb))
  on conflict (user_id) do update set seen = now(), wishes = excluded.wishes, rating = excluded.rating, races = excluded.races, name = excluded.name
  returning * into s;
  p := public.regatta_make_pair(s, o);
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;

revoke all on function public.regatta_seek_challenge(text, jsonb) from public, anon;
grant execute on function public.regatta_seek_challenge(text, jsonb) to authenticated;
