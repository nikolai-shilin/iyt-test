-- The 1-on-1 plan's targets, measured (its last part: "a number to move", each release with its target set against
-- release 1's baseline; the ryc-regatta repo: components/admin-targets.tsx on /admin/duels). Two things weren't kept:
--   regatta_seek_wait: how long each search waited for Match found. A search's row holds when it began (since) until it
--     ends, and every way a pair is made (the matchmaker, a direct challenge, a search kept while away) sets the row's
--     pair_id, so a trigger keeps since and the moment, one row a sailor a pair. From now on; none before.
--   regatta_invites.opened_at: the first time someone other than its host opened a friend's link. regatta_invite(code),
--     which the invite page asks from the friend's browser with their session, sets it, so it becomes volatile.
-- regatta_admin_targets(days): for an admin, over the last `days` (or all time), each target's figure as [hits, of] or, for
-- a time, [median seconds, of]: the database's own counts, the site says what each target is and whether it's met.

create table public.regatta_seek_wait (
  pair_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  since timestamptz not null,
  at timestamptz not null default now(),
  primary key (pair_id, user_id)
);
create index regatta_seek_wait_at_idx on public.regatta_seek_wait (at);
alter table public.regatta_seek_wait enable row level security;
revoke all on public.regatta_seek_wait from public, anon, authenticated;

create function public.regatta_seek_wait_keep()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.regatta_seek_wait (pair_id, user_id, since) values (new.pair_id, new.user_id, new.since) on conflict do nothing;
  return null;
end $$;
revoke all on function public.regatta_seek_wait_keep() from public, anon, authenticated;

create trigger regatta_seek_wait_keep after update of pair_id on public.regatta_seek
  for each row when (old.pair_id is null and new.pair_id is not null) execute function public.regatta_seek_wait_keep();

alter table public.regatta_invites add column opened_at timestamptz;

create or replace function public.regatta_invite(p_code text)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  i public.regatta_invites;
  r public.regatta_rating;
begin
  select * into i from public.regatta_invites where code = p_code;
  if not found then return null; end if;
  if i.opened_at is null and auth.uid() is distinct from i.host_user then
    update public.regatta_invites set opened_at = now() where code = p_code and opened_at is null;
  end if;
  select * into r from public.regatta_rating where user_id = i.host_user;
  return jsonb_build_object('name', i.host_name, 'rating', coalesce(r.rating, 1500), 'races', coalesce(r.races, 0),
    'venue', i.venue, 'yacht', i.yacht, 'wind', i.wind, 'length', i.length, 'course', i.course, 'laps', i.laps, 'start_min', i.start_min,
    'current', i."current", 'minutes', public.regatta_duel_minutes(i.yacht, i.length, i.laps, i.start_min),
    'sailed', (select count(*) from public.regatta_duels d where d.code = i.code));
end $$;

create function public.regatta_admin_targets(days int default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  t_from timestamptz := case when days is null then null else now() - make_interval(days => greatest(1, least(days, 365))) end;
  today date := (now() at time zone 'UTC')::date;
  o jsonb := '{}'::jsonb;
begin
  if not public.is_regatta_admin() then
    raise exception 'not a regatta admin' using errcode = '42501';
  end if;

  -- releases 1 to 3, from the races: the gun (finished, or told so by either screen, as regatta_admin_duels counts it), the
  -- finish, results with both accounts that both screens agree on, the disputed among the rated, guests who kept the race
  -- by signing in after it, and rematches on the same link within five minutes of the finish
  with d as (
    select x.*, (x.state = 'finished' or coalesce(x.gun, false) or coalesce(x.guest_gun, false)) as reached,
           (x.state = 'finished' or x.gun is not null or x.guest_gun is not null) as known,
           (x.host_user is not null and x.guest_user is not null and x.host_user <> x.guest_user and x.guest_claimed_at is null) as two
      from public.regatta_duels x where x.state <> 'racing' and (t_from is null or x.started_at >= t_from))
  select o || jsonb_build_object(
    'gun', jsonb_build_array(count(*) filter (where reached), count(*) filter (where known)),
    'gun_fin', jsonb_build_array(count(*) filter (where reached and state = 'finished'), count(*) filter (where reached)),
    'trusted', jsonb_build_array(count(*) filter (where state = 'finished' and two and agreed), count(*) filter (where state = 'finished')),
    'disputed', jsonb_build_array(count(*) filter (where state = 'finished' and two and agreed = false), count(*) filter (where state = 'finished' and two and agreed is not null)),
    'claim', jsonb_build_array(count(*) filter (where state = 'finished' and guest_claimed_at is not null),
                               count(*) filter (where state = 'finished' and (guest_user is null or guest_claimed_at is not null))),
    'rematch', jsonb_build_array(
      count(*) filter (where state = 'finished' and exists (select 1 from public.regatta_duels n where n.code = d.code and n.id <> d.id
                                                               and n.started_at >= d.ended_at and n.started_at <= d.ended_at + interval '5 minutes')),
      count(*) filter (where state = 'finished' and ended_at < now() - interval '5 minutes')))
    into o from d;

  -- release 2: from the first screen's end to the new rating, for the races rated
  with r as (
    select min(c.at) as rated, least(d.ended_at, coalesce(d.guest_ended_at, d.ended_at)) as fin
      from public.regatta_rating_change c join public.regatta_duels d on d.id = c.duel_id
     where t_from is null or d.started_at >= t_from group by d.id)
  select o || jsonb_build_object('rated_1min', jsonb_build_array(count(*) filter (where rated - fin <= interval '1 minute'), count(*) filter (where fin is not null)))
    into o from r;

  -- release 3: friends' links opened (by someone other than the host) that reached the gun, and of those the finish;
  -- a link opened in the last quarter of an hour may not have raced yet, so it waits
  with i as (
    select exists (select 1 from public.regatta_duels d where d.code = v.code and (d.state = 'finished' or coalesce(d.gun, false) or coalesce(d.guest_gun, false))) as reached,
           exists (select 1 from public.regatta_duels d where d.code = v.code and d.state = 'finished') as fin
      from public.regatta_invites v
     where v.opened_at is not null and v.opened_at < now() - interval '15 minutes' and (t_from is null or v.opened_at >= t_from))
  select o || jsonb_build_object('invite_gun', jsonb_build_array(count(*) filter (where reached), count(*)),
                                 'invite_fin', jsonb_build_array(count(*) filter (where reached and fin), count(*) filter (where reached)))
    into o from i;

  -- release 4: the wait from Find a race to Match found (the median, in the duel hour and at any hour); matches found that
  -- reached the gun (a pair from the last two minutes may still be starting, so it waits)
  with w as (select extract(epoch from (x.at - x.since)) as s, extract(hour from x.at at time zone 'UTC') = 19 as hour
               from public.regatta_seek_wait x where t_from is null or x.at >= t_from)
  select o || jsonb_build_object(
    'wait_hour', jsonb_build_array(percentile_cont(0.5) within group (order by s) filter (where hour), count(*) filter (where hour)),
    'wait_all', jsonb_build_array(percentile_cont(0.5) within group (order by s), count(*)))
    into o from w;
  with p as (
    select x.pushed_at, x.state,
           exists (select 1 from public.regatta_duels d where d.code = x.code and (d.state = 'finished' or coalesce(d.gun, false) or coalesce(d.guest_gun, false))) as reached
      from public.regatta_pairs x where x.created_at < now() - interval '2 minutes' and (t_from is null or x.created_at >= t_from))
  select o || jsonb_build_object(
    'pair_gun', jsonb_build_array(count(*) filter (where reached), count(*)),
    -- release 5: Match found sent while away (by push or the bot) that ended in a match both accepted
    'push_ok', jsonb_build_array(count(*) filter (where pushed_at is not null and state = 'accepted'), count(*) filter (where pushed_at is not null)))
    into o from p;

  -- release 4: each account's first 1-on-1, how many reached the finish; and of those a week old or more, how many came
  -- back on a later day within the week (another 1-on-1, or today's race, as the account's races are keyed)
  with s as (
    select v.u, x.id, x.state, x.started_at, coalesce(x.ended_at, x.started_at) as e
      from public.regatta_duels x cross join lateral (values (x.host_user), (x.guest_user)) v(u)
     where v.u is not null and x.state <> 'racing'),
  f as (select distinct on (u) * from s order by u, started_at, id),
  b as (
    select f.*, exists (select 1 from s n where n.u = f.u and (n.started_at at time zone 'UTC')::date > (f.started_at at time zone 'UTC')::date
                          and n.started_at <= f.e + interval '7 days')
             or exists (select 1 from auth.users a join public.game_races g
                          on (case when a.raw_app_meta_data ->> 'telegram_id' ~ '^[0-9]{1,15}$' then g.user_id = (a.raw_app_meta_data ->> 'telegram_id')::bigint
                                   else g.user_id is null and g.player = a.id end)
                         where a.id = f.u and g.finished_at is not null and (g.finished_at at time zone 'UTC')::date > (f.started_at at time zone 'UTC')::date
                           and g.finished_at <= f.e + interval '7 days') as back
      from f where t_from is null or f.started_at >= t_from)
  select o || jsonb_build_object(
    'first_fin', jsonb_build_array(count(*) filter (where state = 'finished'), count(*)),
    'back_7', jsonb_build_array(count(*) filter (where back and started_at <= now() - interval '7 days'), count(*) filter (where started_at <= now() - interval '7 days')))
    into o from b;

  -- release 5: open calls taken within ten minutes (one from the last ten minutes still open waits)
  select o || jsonb_build_object('call_10', jsonb_build_array(
      count(*) filter (where exists (select 1 from public.regatta_pairs p where p.id = c.pair_id and p.created_at <= c.created_at + interval '10 minutes')),
      count(*) filter (where c.pair_id is not null or c.created_at < now() - interval '10 minutes')))
    into o from public.regatta_call c where t_from is null or c.created_at >= t_from;

  -- release 6: days sailed in today's race per active sailor, the last 30 days beside the 30 before (whatever the period)
  with g as (
    select coalesce(r.user_id::text, 'a:' || r.player::text) as who, (r.finished_at at time zone 'UTC')::date as d
      from public.game_races r
     where r.finished_at >= now() - interval '60 days' and not coalesce(r.dsq, false) and r.secs > 0 and (r.user_id is not null or r.player is not null)),
  per as (select who, count(distinct d) filter (where d > today - 30) as now_n, count(distinct d) filter (where d <= today - 30) as prev_n from g group by who)
  select o || jsonb_build_object(
    'days_now', jsonb_build_array(round(avg(now_n) filter (where now_n > 0), 2), count(*) filter (where now_n > 0)),
    'days_prev', jsonb_build_array(round(avg(prev_n) filter (where prev_n > 0), 2), count(*) filter (where prev_n > 0)))
    into o from per;

  -- release 7: For you's cards shown, tapped and dismissed (× or Fewer like this)
  select o || jsonb_build_object(
    'fy_tap', jsonb_build_array(count(*) filter (where e.ev = 'tap'), count(*) filter (where e.ev = 'shown')),
    'fy_dismiss', jsonb_build_array(count(*) filter (where e.ev in ('dismiss', 'fewer')), count(*) filter (where e.ev = 'shown')))
    into o from public.regatta_suggest_event e where t_from is null or e.at >= t_from;

  return o || jsonb_build_object('since', t_from);
end $$;

revoke all on function public.regatta_admin_targets(int) from public, anon;
grant execute on function public.regatta_admin_targets(int) to authenticated;
