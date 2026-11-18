-- The Regatta game's 1-on-1 races, one row a race, for the site's /admin/duels (the ryc-regatta repo: app/connect/log,
-- components/admin-duels.tsx). Nothing here reaches game_races, a ranking or a rating.
--
-- regatta_duels: row-level security is on with no policies, so nobody reads or writes the table directly.
--
-- regatta_duel_log(p_key, p_report): the site's route writes a report with its key, DUEL_LOG_KEY. The vault keeps only the
-- key's SHA-256, as regatta_duel_key_hash, so the key itself is never written in SQL.
--
-- regatta_duel_apply(p_report): what a report does; for regatta_duel_log alone. Reports may arrive in any order and may be
-- repeated. A join before the start is kept, and the start then sets the write hash on that row. Once a row has a write
-- hash, another start changes nothing. A join names the guest until an account has joined. The first end with the right
-- hash stands.
--
-- regatta_admin_duels(days): for a regatta admin alone (is_regatta_admin()), the overall numbers of the last `days` (1–365;
-- null is all time) and the newest 1,000 races. A race still racing two hours after its start is No result: it counts in
-- totals.no_result and reads as the state 'no_result' in races.

create table public.regatta_duels (
  id uuid primary key default gen_random_uuid(),
  code text not null,
  seed int not null,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  state text not null default 'racing' check (state in ('racing', 'finished', 'abandoned')),
  write_hash text,
  venue text,
  yacht text,
  wind text,
  length text,
  course text,
  laps smallint,
  start_min smallint,
  "current" boolean,
  daytime text,
  host_name text,
  host_user uuid,
  host_place smallint,
  host_secs real,
  host_mark text,
  host_pens smallint,
  guest_name text,
  guest_user uuid,
  guest_place smallint,
  guest_secs real,
  guest_mark text,
  guest_pens smallint,
  winner text,
  margin real,
  forfeited text,
  recalls smallint,
  prep_flag text,
  unique (code, seed)
);

create index regatta_duels_started_at_idx on public.regatta_duels (started_at desc);

alter table public.regatta_duels enable row level security;

create function public.regatta_duel_apply(p_report jsonb)
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
    insert into public.regatta_duels as d (code, seed, guest_user, guest_name)
    values (v_code, v_seed, (p_report ->> 'guest_user')::uuid, p_report ->> 'guest_name')
    on conflict (code, seed) do update set
      guest_user = excluded.guest_user,
      guest_name = coalesce(excluded.guest_name, d.guest_name)
    where d.guest_user is null;

  elsif v_kind = 'end' then
    update public.regatta_duels d set
      ended_at = now(),
      state = p_report ->> 'state',
      winner = p_report ->> 'winner',
      margin = (p_report ->> 'margin')::real,
      forfeited = p_report ->> 'forfeited',
      recalls = (p_report ->> 'recalls')::smallint,
      prep_flag = p_report ->> 'prep_flag',
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
  end if;
end $$;

revoke all on function public.regatta_duel_apply(jsonb) from public, anon, authenticated;

create function public.regatta_duel_log(p_key text, p_report jsonb)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if p_key is null or encode(sha256(convert_to(p_key, 'UTF8')), 'hex')
     is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_duel_key_hash') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  perform public.regatta_duel_apply(p_report);
end $$;

revoke all on function public.regatta_duel_log(text, jsonb) from public;
grant execute on function public.regatta_duel_log(text, jsonb) to anon, authenticated;

create function public.regatta_admin_duels(days int default null)
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
        'median', percentile_cont(0.5) within group (order by p.length_s) filter (where p.state = 'finished'))
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
          'length_s', r.length_s,
          'host', jsonb_build_object(
            'name', coalesce(h.name, r.host_name),
            'who', case when h.id is not null then coalesce(h.tg, h.id::text) end,
            'kind', case when h.tg is not null then 'tg' when h.id is not null then 'acct' else 'guest' end,
            'handle', case when h.tg is null then h.email end,
            'place', r.host_place, 'secs', r.host_secs, 'mark', r.host_mark, 'pens', r.host_pens),
          'guest', jsonb_build_object(
            'name', coalesce(g.name, r.guest_name),
            'who', case when g.id is not null then coalesce(g.tg, g.id::text) end,
            'kind', case when g.tg is not null then 'tg' when g.id is not null then 'acct' else 'guest' end,
            'handle', case when g.tg is null then g.email end,
            'place', r.guest_place, 'secs', r.guest_secs, 'mark', r.guest_mark, 'pens', r.guest_pens)
        ) order by r.started_at desc, r.id desc), '[]'::jsonb)
      from shown r
      left join accounts h on h.id = r.host_user
      left join accounts g on g.id = r.guest_user)
  ) into result;
  return result;
end $$;

revoke all on function public.regatta_admin_duels(int) from public, anon;
grant execute on function public.regatta_admin_duels(int) to authenticated;
