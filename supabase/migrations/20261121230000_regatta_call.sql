-- Open calls for the 1-on-1 race (release 5a of the 1-on-1 plan; the ryc-regatta repo: /duel's Post an open call,
-- /call/[code], components/duel-finder.tsx, app/connect/seek).
--
-- A sailor looking for a race (regatta_seek) can post a call: a link for any chat that says who, their rating and the
-- band of ratings that may take it (theirs ±100 by default). The first signed-in sailor in the band to take it is paired
-- with them at once, as a challenge is (regatta_make_pair): both see Match found, the caller hosts. A call stays the
-- caller's while they go on looking; it is taken once its pair is offered or accepted (open again if that pair is declined
-- or lapses and the caller is still looking), away while the caller isn't looking, and closed after an hour.
--
-- regatta_call_post(wishes, band): the caller's open call (the same one again while it lasts), made if there is none.
-- regatta_call_view(code): what the link shows, to anyone: who, rating, races, the band, venue and yacht wished, its
-- state (open, taken, away, closed), who took it, the time left, and for a signed-in reader whether it's theirs and
-- whether their rating fits.
-- regatta_call_take(code, wishes): take it, if it is open, not yours and your rating fits: found, as from Find a race.

create table public.regatta_call (
  code text primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  name text,
  rating int not null,
  races int not null,
  lo int not null,
  hi int not null,
  wishes jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  closes_at timestamptz not null default now() + interval '1 hour',
  pair_id uuid references public.regatta_pairs (id) on delete set null,
  taken_by uuid references auth.users (id) on delete set null,
  taken_name text
);
create index regatta_call_user_idx on public.regatta_call (user_id, closes_at);

alter table public.regatta_call enable row level security;
revoke all on public.regatta_call from public, anon, authenticated;

-- a call's state now
create function public.regatta_call_state(c public.regatta_call)
returns text language plpgsql stable security definer set search_path = '' as $$
declare
  ps text;
  s public.regatta_seek;
begin
  if c.pair_id is not null then
    select state into ps from public.regatta_pairs where id = c.pair_id;
    if ps = 'accepted' or (ps = 'offered' and exists (select 1 from public.regatta_pairs p where p.id = c.pair_id and now() - p.created_at <= interval '12 seconds')) then return 'taken'; end if;
  end if;
  if now() > c.closes_at then return 'closed'; end if;
  select * into s from public.regatta_seek where user_id = c.user_id;
  if not found or s.seen < now() - interval '30 seconds' or s.pair_id is not null then return 'away'; end if;
  return 'open';
end $$;

revoke all on function public.regatta_call_state(public.regatta_call) from public, anon, authenticated;

create function public.regatta_call_post(p_wishes jsonb default '{}'::jsonb, p_band int default 100)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  c public.regatta_call;
  band int := case when p_band in (100, 200, 350) then p_band else 100 end;
  k text;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select * into s from public.regatta_seek where user_id = me;
  if not found or s.seen < now() - interval '10 seconds' or s.pair_id is not null then return jsonb_build_object('status', 'none', 'reason', 'not_looking'); end if;
  -- the call already out, while it lasts and isn't taken: kept, its band and wishes as now asked
  select * into c from public.regatta_call x where x.user_id = me and x.closes_at > now() order by x.created_at desc limit 1;
  if found and public.regatta_call_state(c) <> 'taken' and (c.pair_id is null or not exists (select 1 from public.regatta_pairs p where p.id = c.pair_id and p.state = 'accepted')) then
    update public.regatta_call set lo = s.rating - band, hi = s.rating + band, wishes = coalesce(p_wishes, '{}'::jsonb), rating = s.rating, races = s.races, name = s.name,
      pair_id = null, taken_by = null, taken_name = null
     where code = c.code returning * into c;
  else
    loop
      k := public.regatta_new_code();
      exit when not exists (select 1 from public.regatta_call x where x.code = k);
    end loop;
    insert into public.regatta_call (code, user_id, name, rating, races, lo, hi, wishes)
    values (k, me, s.name, s.rating, s.races, s.rating - band, s.rating + band, coalesce(p_wishes, '{}'::jsonb))
    returning * into c;
  end if;
  return jsonb_build_object('status', 'open', 'code', c.code, 'lo', c.lo, 'hi', c.hi, 'left', round(extract(epoch from c.closes_at - now())));
end $$;

revoke all on function public.regatta_call_post(jsonb, int) from public, anon;
grant execute on function public.regatta_call_post(jsonb, int) to authenticated;

create function public.regatta_call_view(p_code text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  c public.regatta_call;
  mine int;
begin
  select * into c from public.regatta_call where code = upper(coalesce(p_code, ''));
  if not found then return null; end if;
  if me is not null then select coalesce((select rating from public.regatta_rating where user_id = me), 1500) into mine; end if;
  return jsonb_build_object('code', c.code, 'name', c.name, 'rating', c.rating, 'races', c.races, 'lo', c.lo, 'hi', c.hi,
    'venue', nullif(c.wishes ->> 'venue', ''), 'yacht', nullif(c.wishes ->> 'yacht', ''),
    'state', public.regatta_call_state(c), 'taken_name', c.taken_name,
    'left', greatest(0, round(extract(epoch from c.closes_at - now()))),
    'mine', me is not null and me = c.user_id,
    'fits', case when me is null then null else mine between c.lo and c.hi end);
end $$;

revoke all on function public.regatta_call_view(text) from public;
grant execute on function public.regatta_call_view(text) to anon, authenticated;

create function public.regatta_call_take(p_code text, p_wishes jsonb default '{}'::jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  c public.regatta_call;
  s public.regatta_seek;
  o public.regatta_seek;
  r public.regatta_rating;
  p public.regatta_pairs;
  st text;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  select * into c from public.regatta_call where code = upper(coalesce(p_code, ''));
  if not found then return jsonb_build_object('status', 'none', 'reason', 'closed'); end if;
  if c.user_id = me then return jsonb_build_object('status', 'none', 'reason', 'mine'); end if;
  select * into s from public.regatta_seek where user_id = me;
  if found and s.pair_id is not null then return public.regatta_seek(p_wishes); end if; -- (in a pair already: that one)
  st := public.regatta_call_state(c);
  if st <> 'open' then return jsonb_build_object('status', 'none', 'reason', st); end if;
  select * into r from public.regatta_rating where user_id = me;
  if coalesce(r.rating, 1500) not between c.lo and c.hi then return jsonb_build_object('status', 'none', 'reason', 'band'); end if;
  insert into public.regatta_seek as x (user_id, name, rating, races, wishes)
  values (me, public.regatta_account_name(me), coalesce(r.rating, 1500), coalesce(r.races, 0), coalesce(p_wishes, '{}'::jsonb))
  on conflict (user_id) do update set seen = now(), wishes = excluded.wishes, rating = excluded.rating, races = excluded.races, name = excluded.name
  returning * into s;
  select * into o from public.regatta_seek where user_id = c.user_id;
  p := public.regatta_make_pair(o, s);
  update public.regatta_call set pair_id = p.id, taken_by = me, taken_name = s.name where code = c.code;
  return jsonb_build_object('status', 'found', 'pair', public.regatta_pair_view(p, me));
end $$;

revoke all on function public.regatta_call_take(text, jsonb) from public, anon;
grant execute on function public.regatta_call_take(text, jsonb) to authenticated;
