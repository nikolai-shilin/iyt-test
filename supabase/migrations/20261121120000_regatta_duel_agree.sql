-- Trusted results for the Regatta game's 1-on-1 races (the ryc-regatta repo: public/game/duel-log.js, match-ui.js,
-- lib/duel-log.ts, components/admin-duels.tsx): both screens now report the end, and a race says whether it reached the
-- gun, so a later rating counts only races both screens agree on, and /admin/duels can measure how races go.
--
-- regatta_duels:
--   gun: the host's word that the race reached the gun (its clock past nought, or a recall); null from a build before it.
--   guest_hash: the SHA-256 of the token the guest's screen sent with her join; the first join that brings one keeps it.
--   guest_state, guest_winner, guest_gun, guest_ended_at: the end as the guest's screen had it, set once by an end with
--   side 'guest' and her token, on a race started in the last six hours. The host's end stays the race's result.
--   agreed: null until both ends are in; then whether they name the same state and the same winner.
--
-- regatta_duel_apply(p_report): a join with a guest_hash keeps it on a racing row that has none (and names the guest as
-- before, until an account has joined); once a row has one, a join with another changes nothing. An end with side 'guest'
-- fills the guest's columns; the host's end keeps gun.
--
-- regatta_admin_duels(days): totals add gun (races that reached it: finished, or told so by either screen), gun_known,
-- both_told, agreed, disputed, finished_accounts (finished with two accounts) and trusted (those of them agreed); each race
-- adds gun, agreed, guest_state and guest_winner.

alter table public.regatta_duels
  add column gun boolean,
  add column guest_hash text,
  add column guest_state text check (guest_state in ('finished', 'abandoned')),
  add column guest_winner text check (guest_winner in ('host', 'guest')),
  add column guest_gun boolean,
  add column guest_ended_at timestamptz,
  add column agreed boolean generated always as (
    case when state = 'racing' or guest_state is null then null
         else state = guest_state and winner is not distinct from guest_winner end) stored;

create or replace function public.regatta_duel_apply(p_report jsonb)
returns void language plpgsql security definer set search_path = '' as $$
declare
  v_kind text := p_report ->> 'kind';
  v_code text := p_report ->> 'code';
  v_seed int := (p_report ->> 'seed')::int;
begin
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
      guest_gun = (p_report ->> 'gun')::boolean
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

create or replace function public.regatta_admin_duels(days int default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  since timestamptz := case when days is null then null else now() - make_interval(days => greatest(1, least(days, 365))) end;
  result jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;
  with numbered as (   -- numbered over all time, so a rematch keeps its number when the period cuts off the first race
    select d.*, row_number() over (partition by d.code order by d.started_at, d.id) as race_no,
           greatest(d.host_secs, d.guest_secs) as length_s
      from public.regatta_duels d
  ), period as (
    select * from numbered n where since is null or n.started_at >= since
  ), shown as (
    select * from period p order by p.started_at desc, p.id desc limit 1000
  ), accounts as (
    select a.id, a.email, a.raw_app_meta_data ->> 'telegram_id' as tg,
           coalesce(nullif(a.raw_user_meta_data ->> 'display_name', ''), nullif(u.name, '')) as name
      from auth.users a
      left join public.users u on u.id = case when a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,18}$'
                                              then (a.raw_app_meta_data ->> 'telegram_id')::bigint end
     where a.id in (select s.host_user from shown s union select s.guest_user from shown s)
  ), seats as (
    select p.host_user as uid, p.host_name as name from period p
    union all
    select p.guest_user, p.guest_name from period p where p.guest_name is not null or p.guest_user is not null
  ), screens as (      -- each screen's report of how the race ran on it
    select x.perf from period p cross join lateral (values (p.host_perf), (p.guest_perf)) x(perf) where x.perf is not null
  )
  select jsonb_build_object(
    'since', since,
    'more', (select count(*) > 1000 from period),
    'totals', (
      select jsonb_build_object(
        'races', count(*),
        'finished', count(*) filter (where p.state = 'finished'),
        'abandoned', count(*) filter (where p.state = 'abandoned'),
        'no_result', count(*) filter (where p.state = 'racing' and p.started_at < now() - interval '2 hours'),
        'sailors', (select count(distinct s.uid) + count(distinct lower(s.name)) filter (where s.uid is null) from seats s),
        'seats', coalesce(sum(case when p.guest_name is not null then 2 else 1 end), 0),
        'signed', coalesce(sum((p.host_user is not null)::int + (p.guest_name is not null and p.guest_user is not null)::int), 0),
        'rematches', count(*) filter (where p.race_no > 1),
        'median', percentile_cont(0.5) within group (order by p.length_s) filter (where p.state = 'finished'),
        'gun', count(*) filter (where p.state = 'finished' or p.gun or p.guest_gun),
        'gun_known', count(*) filter (where p.state = 'finished' or p.gun is not null or p.guest_gun is not null),
        'both_told', count(*) filter (where p.agreed is not null),
        'agreed', count(*) filter (where p.agreed),
        'disputed', count(*) filter (where not p.agreed),
        'finished_accounts', count(*) filter (where p.state = 'finished' and p.host_user is not null and p.guest_user is not null),
        'trusted', count(*) filter (where p.state = 'finished' and p.host_user is not null and p.guest_user is not null and p.agreed),
        'perf_seats', (select count(*) from screens),
        'slow_seats', (select count(*) from screens s
                        where (s.perf ->> 'low') ~ '^[0-9.]+$' and (s.perf ->> 'low')::real < 20
                           or (s.perf ->> 'stall') ~ '^[0-9.]+$' and (s.perf ->> 'stall')::real >= 2))
      from period p),
    'days', (
      select coalesce(jsonb_agg(jsonb_build_object('d', x.d, 'n', x.n, 'fin', x.fin) order by x.d), '[]'::jsonb)
      from (
        select (p.started_at at time zone 'UTC')::date as d, count(*) as n, count(*) filter (where p.state = 'finished') as fin
          from period p group by 1
      ) x),
    'endings', (
      select jsonb_build_object(
        'forfeit', count(*) filter (where e.ending = 'forfeit'),
        'no_winner', count(*) filter (where e.ending = 'no_winner'),
        'dnf', count(*) filter (where e.ending = 'dnf'),
        'dsq', count(*) filter (where e.ending = 'dsq'),
        'both', count(*) filter (where e.ending = 'both'))
      from (
        select case when p.forfeited is not null then 'forfeit'
                    when p.winner is null then 'no_winner'
                    when 'DNF' in (p.host_mark, p.guest_mark) then 'dnf'
                    when 'DSQ' in (p.host_mark, p.guest_mark) then 'dsq'
                    else 'both' end as ending
          from period p where p.state = 'finished'
      ) e),
    'groups', (
      select coalesce(jsonb_agg(jsonb_build_object('k', x.k, 'v', x.v, 'n', x.n, 'fin', x.fin) order by x.k, x.n desc, x.v), '[]'::jsonb)
      from (
        select g.k, g.v, count(*) as n, count(*) filter (where p.state = 'finished') as fin
          from period p
          cross join lateral (values ('venue', p.venue), ('yacht', p.yacht), ('wind', p.wind), ('course', p.course),
                                     ('start', p.start_min::text)) g(k, v)
         where g.v is not null
         group by g.k, g.v
      ) x),
    'races', (
      select coalesce(jsonb_agg(jsonb_build_object(
          'id', r.id, 'code', r.code, 'race_no', r.race_no, 'at', r.started_at, 'ended', r.ended_at,
          'state', case when r.state = 'racing' and r.started_at < now() - interval '2 hours' then 'no_result' else r.state end,
          'venue', r.venue, 'yacht', r.yacht, 'wind', r.wind, 'length', r.length, 'course', r.course, 'laps', r.laps,
          'start_min', r.start_min, 'current', r."current", 'daytime', r.daytime,
          'winner', r.winner, 'margin', r.margin, 'forfeited', r.forfeited, 'recalls', r.recalls, 'prep_flag', r.prep_flag,
          'length_s', r.length_s, 'gun', coalesce(r.gun, r.guest_gun), 'agreed', r.agreed,
          'guest_state', r.guest_state, 'guest_winner', r.guest_winner,
          'host', jsonb_build_object(
            'name', coalesce(h.name, r.host_name),
            'who', case when h.id is not null then coalesce(h.tg, h.id::text) end,
            'kind', case when h.tg is not null then 'tg' when h.id is not null then 'acct' else 'guest' end,
            'handle', case when h.tg is null then h.email end,
            'place', r.host_place, 'secs', r.host_secs, 'mark', r.host_mark, 'pens', r.host_pens, 'perf', r.host_perf),
          'guest', jsonb_build_object(
            'name', coalesce(g.name, r.guest_name),
            'who', case when g.id is not null then coalesce(g.tg, g.id::text) end,
            'kind', case when g.tg is not null then 'tg' when g.id is not null then 'acct' else 'guest' end,
            'handle', case when g.tg is null then g.email end,
            'place', r.guest_place, 'secs', r.guest_secs, 'mark', r.guest_mark, 'pens', r.guest_pens, 'perf', r.guest_perf)
        ) order by r.started_at desc, r.id desc), '[]'::jsonb)
      from shown r
      left join accounts h on h.id = r.host_user
      left join accounts g on g.id = r.guest_user)
  ) into result;
  return result;
end $$;
