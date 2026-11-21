-- The 1-on-1 rating of the Regatta game (release 2 of the 1-on-1 plan; the ryc-regatta repo: lib/elo.ts, lib/levels.ts,
-- app/connect/rating, components/duel-rating.tsx). Plain Elo: everyone starts at 1500; a win earns round(K × (1 − chance)),
-- a loss costs round(K × chance), chance = 1 / (1 + 10^((theirs − yours) / 400)); K is 64 for a sailor's first five rated races
-- (provisional, shown with a ~) and 32 after. No decay, no uncertainty band. lib/elo.ts does the same sums, and
-- test/elo.test.mjs holds the cases this function was run against.
--
-- regatta_rating: one row per account that has sailed a rated race: rating, races, wins, losses, best, lowest.
-- regatta_rating_change: each rated race's change for each of its two sailors, with the chance and K it was worked out with.
-- Row-level security is on with no policies, and the grants are revoked: only the functions below touch them.
--
-- A race is rated once, by regatta_rate_duel(id), which the trigger on regatta_duels runs as a race becomes agreed
-- (20261121120000_regatta_duel_agree.sql), when all of these hold:
--   - it finished with a winner (a forfeit counts: the one who gave up after the gun loses);
--   - both screens agree on it;
--   - both seats have an account, and not the same one;
--   - the pair hasn't already had three rated races since midnight UTC.
-- A race abandoned, with no winner, disputed, or told by one screen only is never rated.
--
-- regatta_duel_rating(code, seed): for the signed-in sailor of that race, how it went for the rating: rated (the change for
-- both), waiting (the race or the other screen's end is still to come, for two minutes after the end), or unrated and why.
-- regatta_my_rating(): the signed-in sailor's rating, place among the settled ratings and last 20 rated races.

create table public.regatta_rating (
  user_id uuid primary key references auth.users (id) on delete cascade,
  rating int not null default 1500,
  races int not null default 0,
  wins int not null default 0,
  losses int not null default 0,
  best int not null default 1500,
  lowest int not null default 1500,
  updated_at timestamptz not null default now()
);

create table public.regatta_rating_change (
  duel_id uuid not null references public.regatta_duels (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  opponent uuid not null,
  won boolean not null,
  before int not null,
  after int not null,
  delta int not null,
  k smallint not null,
  chance real not null,
  opponent_before int not null,
  races_before int not null,
  at timestamptz not null default now(),
  primary key (duel_id, user_id)
);

create index regatta_rating_change_user_idx on public.regatta_rating_change (user_id, at desc);
create index regatta_rating_rating_idx on public.regatta_rating (rating desc) where races >= 5;

alter table public.regatta_rating enable row level security;
alter table public.regatta_rating_change enable row level security;
revoke all on public.regatta_rating from public, anon, authenticated;
revoke all on public.regatta_rating_change from public, anon, authenticated;

-- one side's change: the same sums as lib/elo.ts rate(), rounded half up as the site rounds them
create function public.regatta_elo_delta(mine int, theirs int, races_before int, won boolean)
returns int language sql immutable set search_path = '' as $$
  select (case when won then round((x.k * (1 - x.e))::numeric) else -round((x.k * x.e)::numeric) end)::int
    from (select case when races_before < 5 then 64 else 32 end as k,
                 1 / (1 + power(10::float8, ((theirs - mine) / 400.0)::float8)) as e) x
$$;

-- why a race isn't rated, or null when it is (or will be): the same rules regatta_rate_duel checks
create function public.regatta_duel_unrated(d public.regatta_duels)
returns text language sql stable security definer set search_path = '' as $$
  select case
    when d.host_user is null or d.guest_user is null then 'account'
    when d.host_user = d.guest_user then 'same'
    when d.state = 'abandoned' then 'abandoned'
    when d.state = 'finished' and d.winner is null then 'no_winner'
    when d.agreed is false then 'disputed'
    when exists (select 1 from public.regatta_rating_change c where c.duel_id = d.id) then null
    when (select count(*) from public.regatta_rating_change c
           where c.user_id = d.host_user and c.opponent = d.guest_user
             and c.at >= date_trunc('day', now() at time zone 'UTC') at time zone 'UTC') >= 3 then 'limit'
    else null end
$$;

revoke all on function public.regatta_duel_unrated(public.regatta_duels) from public, anon, authenticated;

create function public.regatta_rate_duel(p_id uuid)
returns void language plpgsql security definer set search_path = '' as $$
declare
  d public.regatta_duels;
  h public.regatta_rating;
  g public.regatta_rating;
  host_won boolean;
  dh int;
  dg int;
begin
  select * into d from public.regatta_duels where id = p_id for update;
  if not found or d.state <> 'finished' or d.agreed is not true or d.winner not in ('host', 'guest') then return; end if;
  if public.regatta_duel_unrated(d) is not null then return; end if;
  if exists (select 1 from public.regatta_rating_change c where c.duel_id = d.id) then return; end if;

  insert into public.regatta_rating (user_id) values (d.host_user), (d.guest_user) on conflict (user_id) do nothing;
  -- both rows locked, in one order, so two races of the same sailors can't cross
  perform 1 from public.regatta_rating r where r.user_id in (d.host_user, d.guest_user) order by r.user_id for update;
  select * into h from public.regatta_rating where user_id = d.host_user;
  select * into g from public.regatta_rating where user_id = d.guest_user;

  host_won := d.winner = 'host';
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

revoke all on function public.regatta_rate_duel(uuid) from public, anon, authenticated;

create function public.regatta_duel_rate_trigger()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  perform public.regatta_rate_duel(new.id);
  return null;
end $$;

revoke all on function public.regatta_duel_rate_trigger() from public, anon, authenticated;

create trigger regatta_duels_rate
  after update on public.regatta_duels
  for each row when (new.agreed is true and old.agreed is distinct from true)
  execute function public.regatta_duel_rate_trigger();

create function public.regatta_duel_rating(p_code text, p_seed int)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
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

create function public.regatta_my_rating()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  r public.regatta_rating;
begin
  if me is null then return null; end if;
  select * into r from public.regatta_rating where user_id = me;
  if not found then
    return jsonb_build_object('rating', 1500, 'races', 0, 'wins', 0, 'losses', 0, 'best', 1500, 'lowest', 1500, 'place', null,
      'of', (select count(*) from public.regatta_rating x where x.races >= 5), 'changes', '[]'::jsonb);
  end if;
  return jsonb_build_object('rating', r.rating, 'races', r.races, 'wins', r.wins, 'losses', r.losses, 'best', r.best, 'lowest', r.lowest,
    'place', case when r.races >= 5 then (select count(*) + 1 from public.regatta_rating x where x.races >= 5 and x.rating > r.rating) end,
    'of', (select count(*) from public.regatta_rating x where x.races >= 5),
    'changes', (
      select coalesce(jsonb_agg(jsonb_build_object('at', c.at, 'won', c.won, 'before', c.before, 'after', c.after, 'delta', c.delta,
          'them', case when d.host_user = me then d.guest_name else d.host_name end, 'them_before', c.opponent_before,
          'venue', d.venue, 'yacht', d.yacht, 'margin', d.margin, 'forfeit', d.forfeited is not null) order by c.at desc), '[]'::jsonb)
        from (select * from public.regatta_rating_change c where c.user_id = me order by c.at desc limit 20) c
        join public.regatta_duels d on d.id = c.duel_id));
end $$;

revoke all on function public.regatta_my_rating() from public, anon;
grant execute on function public.regatta_my_rating() to authenticated;
