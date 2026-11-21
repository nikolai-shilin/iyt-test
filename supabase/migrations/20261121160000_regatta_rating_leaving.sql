-- Leaving a 1-on-1 race after the gun loses it (the ryc-regatta repo: public/game/match-ui.js leave, duel-log.js endBody
-- `left`; 20261121140000_regatta_rating.sql). Each screen's end now says who left: the host's Leave, her tab asleep past a
-- minute, her page gone mid-race; on the guest's screen also the host silent five minutes; the guest's Leave before her own
-- finish, which both screens now count as her forfeit (finished, the host the winner: rated as any finish).
--
-- regatta_duels.left_by: who left, as the host's screen has it; guest_left: as the guest's has it.
--
-- regatta_duel_outcome(d): who won a race for the rating, or null:
--   - finished, both screens agreeing, with a winner: the winner;
--   - abandoned on both screens, which name the same sailor as the one who left, after the gun (one screen says so and
--     neither says it wasn't): the other sailor;
--   - the host's screen never told the end, and the guest's says the host left after the gun, a minute or more ago: the
--     guest (her screen only gives up on a silent host after five minutes, so the host has had those to say otherwise).
-- regatta_duel_unrated(d) and regatta_rate_duel(id) go by it. A race abandoned before the gun, or by a leaver the screens
-- don't agree on, is still never rated.
--
-- The host who never comes back leaves no end to set off the trigger, so a race of that kind is rated by
-- regatta_rate_waiting(), which every report runs (regatta_duel_apply), and by regatta_duel_rating(code, seed) as the
-- guest's screen asks after it (now volatile: it may rate the race it is asked about).

alter table public.regatta_duels
  add column left_by text check (left_by in ('host', 'guest')),
  add column guest_left text check (guest_left in ('host', 'guest'));

create function public.regatta_duel_outcome(d public.regatta_duels)
returns text language sql stable set search_path = '' as $$
  select case
    when d.state = 'finished' and d.agreed is true and d.winner in ('host', 'guest') then d.winner
    when d.state = 'abandoned' and d.agreed is true and d.left_by is not null and d.left_by = d.guest_left
         and (d.gun is true or d.guest_gun is true) and d.gun is not false and d.guest_gun is not false
      then case d.left_by when 'host' then 'guest' else 'host' end
    when d.state = 'racing' and d.guest_state = 'abandoned' and d.guest_left = 'host' and d.guest_gun is true
         and d.guest_ended_at <= now() - interval '1 minute'
      then 'guest'
    else null end
$$;

revoke all on function public.regatta_duel_outcome(public.regatta_duels) from public, anon, authenticated;

create or replace function public.regatta_duel_unrated(d public.regatta_duels)
returns text language sql stable security definer set search_path = '' as $$
  select case
    when d.host_user is null or d.guest_user is null then 'account'
    when d.host_user = d.guest_user then 'same'
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

create or replace function public.regatta_rate_duel(p_id uuid)
returns void language plpgsql security definer set search_path = '' as $$
declare
  d public.regatta_duels;
  h public.regatta_rating;
  g public.regatta_rating;
  won text;
  host_won boolean;
  dh int;
  dg int;
begin
  select * into d from public.regatta_duels where id = p_id for update;
  if not found then return; end if;
  won := public.regatta_duel_outcome(d);
  if won is null or public.regatta_duel_unrated(d) is not null then return; end if;
  if exists (select 1 from public.regatta_rating_change c where c.duel_id = d.id) then return; end if;

  insert into public.regatta_rating (user_id) values (d.host_user), (d.guest_user) on conflict (user_id) do nothing;
  perform 1 from public.regatta_rating r where r.user_id in (d.host_user, d.guest_user) order by r.user_id for update;
  select * into h from public.regatta_rating where user_id = d.host_user;
  select * into g from public.regatta_rating where user_id = d.guest_user;

  host_won := won = 'host';
  dh := public.regatta_elo_delta(h.rating, g.rating, h.races, host_won);
  dg := public.regatta_elo_delta(g.rating, h.rating, g.races, not host_won);

  insert into public.regatta_rating_change (duel_id, user_id, opponent, won, before, after, delta, k, chance, opponent_before, races_before)
  values
    (d.id, d.host_user, d.guest_user, host_won, h.rating, h.rating + dh, dh, case when h.races < 5 then 64 else 32 end,
     1 / (1 + power(10::float8, ((g.rating - h.rating) / 400.0)::float8)), g.rating, h.races),
    (d.id, d.guest_user, d.host_user, not host_won, g.rating, g.rating + dg, dg, case when g.races < 5 then 64 else 32 end,
     1 / (1 + power(10::float8, ((h.rating - g.rating) / 400.0)::float8)), h.rating, g.races);

  update public.regatta_rating r set
    rating = r.rating + x.delta,
    races = r.races + 1,
    wins = r.wins + x.w,
    losses = r.losses + 1 - x.w,
    best = greatest(r.best, r.rating + x.delta),
    lowest = least(r.lowest, r.rating + x.delta),
    updated_at = now()
  from (values (d.host_user, dh, host_won::int), (d.guest_user, dg, (not host_won)::int)) x(uid, delta, w)
  where r.user_id = x.uid;
end $$;

-- the races whose host never told the end, waiting on their minute: rated as they come due (a handful a day at most)
create function public.regatta_rate_waiting()
returns void language plpgsql security definer set search_path = '' as $$
declare
  r record;
begin
  for r in
    select d.id from public.regatta_duels d
     where d.state = 'racing' and d.guest_state = 'abandoned' and d.guest_left = 'host' and d.guest_gun is true
       and d.guest_ended_at <= now() - interval '1 minute' and d.started_at > now() - interval '2 days'
       and d.host_user is not null and d.guest_user is not null
       and not exists (select 1 from public.regatta_rating_change c where c.duel_id = d.id)
  loop
    perform public.regatta_rate_duel(r.id);
  end loop;
end $$;

revoke all on function public.regatta_rate_waiting() from public, anon, authenticated;

create index regatta_duels_waiting_idx on public.regatta_duels (guest_ended_at) where state = 'racing' and guest_state = 'abandoned';

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

create or replace function public.regatta_duel_rating(p_code text, p_seed int)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  d public.regatta_duels;
  side text;
  mine public.regatta_rating_change;
  theirs public.regatta_rating_change;
  r public.regatta_rating;
  why text;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  select * into d from public.regatta_duels where code = p_code and seed = p_seed;
  if not found or me not in (coalesce(d.host_user, '00000000-0000-0000-0000-000000000000'), coalesce(d.guest_user, '00000000-0000-0000-0000-000000000000')) then
    return jsonb_build_object('status', 'none');
  end if;
  side := case when me = d.host_user then 'host' else 'guest' end;
  -- a race whose host never told the end comes due a minute after the guest's: rate it now if it has
  perform public.regatta_rate_duel(d.id);
  select * into mine from public.regatta_rating_change c where c.duel_id = d.id and c.user_id = me;
  if found then
    select * into theirs from public.regatta_rating_change c where c.duel_id = d.id and c.user_id = mine.opponent;
    select * into r from public.regatta_rating where user_id = me;
    return jsonb_build_object('status', 'rated', 'side', side,
      'me', jsonb_build_object('before', mine.before, 'after', mine.after, 'delta', mine.delta, 'won', mine.won, 'k', mine.k,
                               'chance', mine.chance, 'races', mine.races_before + 1, 'rating', r.rating, 'all_races', r.races),
      'them', jsonb_build_object('name', case when side = 'host' then d.guest_name else d.host_name end,
                                 'before', theirs.before, 'after', theirs.after, 'delta', theirs.delta, 'races', theirs.races_before + 1));
  end if;
  why := public.regatta_duel_unrated(d);
  if why is null and (d.state = 'racing' or (d.agreed is null and coalesce(d.ended_at, d.guest_ended_at, now()) > now() - interval '2 minutes')) then
    return jsonb_build_object('status', 'waiting', 'side', side);
  end if;
  return jsonb_build_object('status', 'unrated', 'side', side, 'reason', coalesce(why, 'one_screen'));
end $$;

revoke all on function public.regatta_duel_rating(text, int) from public, anon;
grant execute on function public.regatta_duel_rating(text, int) to authenticated;
