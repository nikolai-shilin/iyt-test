-- The friend challenge, its first part (release 3 of the 1-on-1 plan; the ryc-regatta repo: public/game/match-ui.js tellInvite,
-- app/connect/invite, app/connect/claim, components/invite-info.tsx, components/duel-keep.tsx).
--
-- regatta_invites: one row a link, written by the host's screen as its waiting room opens (a report of kind 'invite' through
-- regatta_duel_log, with the account the site's session names): who is asking and the race's settings. Only the host who
-- made it can change it. regatta_invite(code), for anyone with the link: the host's name, rating and races, the settings,
-- and about how many minutes the race takes (regatta_duel_minutes: the start sequence and the median finished race of that
-- yacht, length and laps, or of that length and laps in any yacht, from three races up; null with fewer).
--
-- A friend who raced signed out can keep the race by signing in after it: regatta_duel_claim(key, code, seed, hash, user),
-- which the site's /connect/claim calls with its key, the session's account and the SHA-256 of the token the guest's screen
-- sent with her join. It sets the guest's account on a race that has none (and isn't the host's), and guest_claimed_at. A
-- race so kept is in that sailor's history, never the rating: regatta_duel_unrated says 'claimed'.
--
-- regatta_my_rating() adds recent: the sailor's last ten 1-on-1 races, rated or not (the player page's history).

create table public.regatta_invites (
  code text primary key,
  host_user uuid not null references auth.users (id) on delete cascade,
  host_name text,
  venue text,
  yacht text,
  wind text,
  length text,
  course text,
  laps smallint,
  start_min smallint,
  "current" boolean,
  daytime text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.regatta_invites enable row level security;
revoke all on public.regatta_invites from public, anon, authenticated;

alter table public.regatta_duels add column guest_claimed_at timestamptz;

create function public.regatta_duel_minutes(p_yacht text, p_length text, p_laps int, p_start int)
returns int language sql stable security definer set search_path = '' as $$
  with done as (
    select d.yacht, greatest(d.host_secs, d.guest_secs) as s from public.regatta_duels d
     where d.state = 'finished' and d.length = p_length and d.laps = p_laps and d.host_secs is not null and d.guest_secs is not null
  ), pick as (
    select percentile_cont(0.5) within group (order by s) as m, count(*) as n, 1 as o from done where yacht = p_yacht
    union all
    select percentile_cont(0.5) within group (order by s), count(*), 2 from done
  )
  select ceil((m + coalesce(p_start, 1) * 60) / 60.0)::int from pick where n >= 3 order by o limit 1
$$;

revoke all on function public.regatta_duel_minutes(text, text, int, int) from public, anon, authenticated;

create function public.regatta_invite(p_code text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  i public.regatta_invites;
  r public.regatta_rating;
begin
  select * into i from public.regatta_invites where code = p_code;
  if not found then return null; end if;
  select * into r from public.regatta_rating where user_id = i.host_user;
  return jsonb_build_object('name', i.host_name, 'rating', coalesce(r.rating, 1500), 'races', coalesce(r.races, 0),
    'venue', i.venue, 'yacht', i.yacht, 'wind', i.wind, 'length', i.length, 'course', i.course, 'laps', i.laps, 'start_min', i.start_min,
    'current', i."current", 'minutes', public.regatta_duel_minutes(i.yacht, i.length, i.laps, i.start_min),
    'sailed', (select count(*) from public.regatta_duels d where d.code = i.code));
end $$;

revoke all on function public.regatta_invite(text) from public;
grant execute on function public.regatta_invite(text) to anon, authenticated;

create function public.regatta_duel_claim(p_key text, p_code text, p_seed int, p_hash text, p_user uuid)
returns boolean language plpgsql security definer set search_path = '' as $$
declare
  n int;
begin
  if p_key is null or encode(sha256(convert_to(p_key, 'UTF8')), 'hex')
     is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_duel_key_hash') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if p_user is null or p_hash is null then return false; end if;
  update public.regatta_duels d set guest_user = p_user, guest_claimed_at = now()
   where d.code = p_code and d.seed = p_seed and d.guest_hash = p_hash and d.guest_user is null
     and d.host_user is distinct from p_user and d.started_at > now() - interval '30 days';
  get diagnostics n = row_count;
  return n > 0;
end $$;

revoke all on function public.regatta_duel_claim(text, text, int, text, uuid) from public;
grant execute on function public.regatta_duel_claim(text, text, int, text, uuid) to anon, authenticated;

create or replace function public.regatta_duel_unrated(d public.regatta_duels)
returns text language sql stable security definer set search_path = '' as $$
  select case
    when d.host_user is null or d.guest_user is null then 'account'
    when d.host_user = d.guest_user then 'same'
    when d.guest_claimed_at is not null then 'claimed'
    when exists (select 1 from public.regatta_rating_change c where c.duel_id = d.id) then null
    when public.regatta_duel_outcome(d) is null and d.agreed is false then 'disputed'
    when public.regatta_duel_outcome(d) is null and d.state = 'abandoned' then 'abandoned'
    -- only the guest's end, abandoned, and not a host who left after the gun (that one waits its minute): abandoned
    when public.regatta_duel_outcome(d) is null and d.state = 'racing' and d.guest_state = 'abandoned'
         and not (d.guest_left is not distinct from 'host' and d.guest_gun is true) then 'abandoned'
    when public.regatta_duel_outcome(d) is null and d.state = 'finished' and d.winner is null then 'no_winner'
    when (select count(*) from public.regatta_rating_change c
           where c.user_id = d.host_user and c.opponent = d.guest_user
             and c.at >= date_trunc('day', now() at time zone 'UTC') at time zone 'UTC') >= 3 then 'limit'
    else null end
$$;

create or replace function public.regatta_duel_apply(p_report jsonb)
returns void language plpgsql security definer set search_path = '' as $$
declare
  v_kind text := p_report ->> 'kind';
  v_code text := p_report ->> 'code';
  v_seed int := (p_report ->> 'seed')::int;
begin
  perform public.regatta_rate_waiting();

  if v_kind = 'start' then
    insert into public.regatta_duels as d (
      code, seed, write_hash, host_user, host_name, guest_name,
      venue, yacht, wind, length, course, laps, start_min, "current", daytime
    ) values (
      v_code, v_seed, p_report ->> 'write_hash', (p_report ->> 'host_user')::uuid, p_report ->> 'host_name', p_report ->> 'guest_name',
      p_report ->> 'venue', p_report ->> 'yacht', p_report ->> 'wind', p_report ->> 'length', p_report ->> 'course',
      (p_report ->> 'laps')::smallint, (p_report ->> 'start_min')::smallint, (p_report ->> 'current')::boolean, p_report ->> 'daytime'
    )
    on conflict (code, seed) do update set
      write_hash = excluded.write_hash,
      host_user = excluded.host_user,
      host_name = excluded.host_name,
      guest_name = coalesce(d.guest_name, excluded.guest_name),
      venue = excluded.venue,
      yacht = excluded.yacht,
      wind = excluded.wind,
      length = excluded.length,
      course = excluded.course,
      laps = excluded.laps,
      start_min = excluded.start_min,
      "current" = excluded."current",
      daytime = excluded.daytime
    where d.write_hash is null;

  elsif v_kind = 'join' then
    insert into public.regatta_duels as d (code, seed, guest_user, guest_name, guest_hash)
    values (v_code, v_seed, (p_report ->> 'guest_user')::uuid, p_report ->> 'guest_name', p_report ->> 'guest_hash')
    on conflict (code, seed) do update set
      guest_user = case when d.guest_user is null then excluded.guest_user else d.guest_user end,
      guest_name = case when d.guest_user is null then coalesce(excluded.guest_name, d.guest_name) else d.guest_name end,
      guest_hash = coalesce(d.guest_hash, excluded.guest_hash)
    where d.state = 'racing' and (d.guest_user is null or d.guest_hash is null)
      and (d.guest_hash is null or excluded.guest_hash is null or d.guest_hash = excluded.guest_hash);

  elsif v_kind = 'end' and p_report ->> 'side' = 'guest' then
    update public.regatta_duels d set
      guest_ended_at = now(),
      guest_state = p_report ->> 'state',
      guest_winner = p_report ->> 'winner',
      guest_gun = (p_report ->> 'gun')::boolean,
      guest_left = case when p_report ->> 'left' in ('host', 'guest') then p_report ->> 'left' end
    where d.code = v_code and d.seed = v_seed
      and d.guest_hash = p_report ->> 'write_hash'
      and d.guest_state is null
      and d.started_at > now() - interval '6 hours'
      and p_report ->> 'state' in ('finished', 'abandoned');

  elsif v_kind = 'end' then
    update public.regatta_duels d set
      ended_at = now(),
      state = p_report ->> 'state',
      winner = p_report ->> 'winner',
      margin = (p_report ->> 'margin')::real,
      forfeited = p_report ->> 'forfeited',
      recalls = (p_report ->> 'recalls')::smallint,
      prep_flag = p_report ->> 'prep_flag',
      gun = (p_report ->> 'gun')::boolean,
      left_by = case when p_report ->> 'left' in ('host', 'guest') then p_report ->> 'left' end,
      host_place = (p_report -> 'host' ->> 'place')::smallint,
      host_secs = (p_report -> 'host' ->> 'secs')::real,
      host_mark = p_report -> 'host' ->> 'mark',
      host_pens = (p_report -> 'host' ->> 'pens')::smallint,
      guest_place = (p_report -> 'guest' ->> 'place')::smallint,
      guest_secs = (p_report -> 'guest' ->> 'secs')::real,
      guest_mark = p_report -> 'guest' ->> 'mark',
      guest_pens = (p_report -> 'guest' ->> 'pens')::smallint
    where d.code = v_code and d.seed = v_seed
      and d.write_hash = p_report ->> 'write_hash'
      and d.state = 'racing'
      and p_report ->> 'state' in ('finished', 'abandoned');

  elsif v_kind = 'invite' and p_report ->> 'host_user' is not null then
    insert into public.regatta_invites as i (code, host_user, host_name, venue, yacht, wind, length, course, laps, start_min, "current", daytime)
    values (v_code, (p_report ->> 'host_user')::uuid, p_report ->> 'host_name', p_report ->> 'venue', p_report ->> 'yacht', p_report ->> 'wind',
      p_report ->> 'length', p_report ->> 'course', (p_report ->> 'laps')::smallint, (p_report ->> 'start_min')::smallint,
      (p_report ->> 'current')::boolean, p_report ->> 'daytime')
    on conflict (code) do update set
      host_name = excluded.host_name, venue = excluded.venue, yacht = excluded.yacht, wind = excluded.wind, length = excluded.length,
      course = excluded.course, laps = excluded.laps, start_min = excluded.start_min, "current" = excluded."current",
      daytime = excluded.daytime, updated_at = now()
    where i.host_user = excluded.host_user;

  elsif v_kind = 'perf' and jsonb_typeof(p_report -> 'perf') = 'object' then
    if p_report ->> 'side' = 'host' then
      update public.regatta_duels d set host_perf = p_report -> 'perf'
       where d.code = v_code and d.seed = v_seed and d.host_perf is null and d.started_at > now() - interval '6 hours';
    elsif p_report ->> 'side' = 'guest' then
      update public.regatta_duels d set guest_perf = p_report -> 'perf'
       where d.code = v_code and d.seed = v_seed and d.guest_perf is null and d.started_at > now() - interval '6 hours';
    end if;
  end if;
end $$;


create or replace function public.regatta_my_rating()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  r public.regatta_rating;
  recent jsonb;
begin
  if me is null then return null; end if;
  select coalesce(jsonb_agg(jsonb_build_object('at', x.started_at, 'state', x.st, 'won', x.won, 'them', x.them,
      'venue', x.venue, 'yacht', x.yacht, 'margin', x.margin, 'delta', x.delta, 'fun', x.delta is null) order by x.started_at desc), '[]'::jsonb)
    into recent
    from (
      select d.started_at, d.venue, d.yacht, d.margin,
             case when d.state = 'racing' and d.started_at < now() - interval '2 hours' then 'no_result' else d.state end as st,
             case when d.state = 'finished' and d.winner is not null then d.winner = (case when d.host_user = me then 'host' else 'guest' end) end as won,
             case when d.host_user = me then d.guest_name else d.host_name end as them,
             (select c.delta from public.regatta_rating_change c where c.duel_id = d.id and c.user_id = me) as delta
        from public.regatta_duels d
       where (d.host_user = me or d.guest_user = me) and d.state <> 'racing'
       order by d.started_at desc limit 10
    ) x;
  select * into r from public.regatta_rating where user_id = me;
  if not found then
    return jsonb_build_object('rating', 1500, 'races', 0, 'wins', 0, 'losses', 0, 'best', 1500, 'lowest', 1500, 'place', null,
      'of', (select count(*) from public.regatta_rating x where x.races >= 5), 'changes', '[]'::jsonb, 'recent', recent);
  end if;
  return jsonb_build_object('rating', r.rating, 'races', r.races, 'wins', r.wins, 'losses', r.losses, 'best', r.best, 'lowest', r.lowest,
    'place', case when r.races >= 5 then (select count(*) + 1 from public.regatta_rating x where x.races >= 5 and x.rating > r.rating) end,
    'of', (select count(*) from public.regatta_rating x where x.races >= 5),
    'changes', (
      select coalesce(jsonb_agg(jsonb_build_object('at', c.at, 'won', c.won, 'before', c.before, 'after', c.after, 'delta', c.delta,
          'them', case when d.host_user = me then d.guest_name else d.host_name end, 'them_before', c.opponent_before,
          'venue', d.venue, 'yacht', d.yacht, 'margin', d.margin, 'forfeit', d.forfeited is not null) order by c.at desc), '[]'::jsonb)
        from (select * from public.regatta_rating_change c where c.user_id = me order by c.at desc limit 20) c
        join public.regatta_duels d on d.id = c.duel_id),
    'recent', recent);
end $$;

revoke all on function public.regatta_my_rating() from public, anon;
grant execute on function public.regatta_my_rating() to authenticated;
