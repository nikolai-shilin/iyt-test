-- For you (release 7e of the 1-on-1 plan; the ryc-regatta repo: lib/suggest.ts gathers, scores, filters and shows,
-- components/for-you.tsx draws the list). The site makes the cards from what it already knows; the database keeps what
-- each signed-in sailor does with them, so the list drifts towards what they really do, the same on every device:
--   regatta_suggest: per sailor and kind, the weight (1 to start; a tap adds 10%, up to 3; a × takes 20% off and "Fewer
--     like this" half, down to 0.2), until when a dismissed kind stays out (seven days), and the counts shown, tapped and
--     dismissed, so a weight that doesn't work can be seen.
--   regatta_suggest_event: each showing, tap and dismissal, when.
-- regatta_suggest_state(): the sailor's weights, the kinds held out now, and the kinds gone stale (shown three times or
--   more in three days without a tap).
-- regatta_suggest_mark(ev, kinds): 'shown' for the kinds on the list (once a kind in ten minutes), or 'tap', 'dismiss' or
--   'fewer' for one; the state after.

create table public.regatta_suggest (
  user_id uuid not null references auth.users (id) on delete cascade,
  kind text not null check (kind ~ '^[a-z_]{2,24}$'),
  weight real not null default 1,
  out_until timestamptz,
  shown int not null default 0,
  tapped int not null default 0,
  dismissed int not null default 0,
  primary key (user_id, kind)
);
create table public.regatta_suggest_event (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  kind text not null,
  ev text not null check (ev in ('shown', 'tap', 'dismiss', 'fewer')),
  at timestamptz not null default now()
);
create index regatta_suggest_event_user_idx on public.regatta_suggest_event (user_id, at desc);
alter table public.regatta_suggest enable row level security;
alter table public.regatta_suggest_event enable row level security;
revoke all on public.regatta_suggest from public, anon, authenticated;
revoke all on public.regatta_suggest_event from public, anon, authenticated;

create function public.regatta_suggest_state()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare me uuid := auth.uid();
begin
  if me is null then return null; end if;
  return jsonb_build_object(
    'weights', (select coalesce(jsonb_object_agg(s.kind, round(s.weight::numeric, 3)), '{}'::jsonb) from public.regatta_suggest s where s.user_id = me),
    'out', (select coalesce(jsonb_agg(s.kind order by s.kind), '[]'::jsonb) from public.regatta_suggest s where s.user_id = me and s.out_until > now()),
    'stale', (select coalesce(jsonb_agg(x.kind order by x.kind), '[]'::jsonb) from (
                select e.kind from public.regatta_suggest_event e where e.user_id = me and e.at > now() - interval '3 days'
                 group by e.kind having count(*) filter (where e.ev = 'shown') >= 3 and count(*) filter (where e.ev = 'tap') = 0) x));
end $$;
revoke all on function public.regatta_suggest_state() from public, anon;
grant execute on function public.regatta_suggest_state() to authenticated;

create function public.regatta_suggest_mark(p_ev text, p_kinds text[])
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare me uuid := auth.uid(); k text;
begin
  if me is null then return null; end if;
  if p_ev not in ('shown', 'tap', 'dismiss', 'fewer') or p_kinds is null then return public.regatta_suggest_state(); end if;
  foreach k in array (case when p_ev = 'shown' then p_kinds[1:3] else p_kinds[1:1] end) loop
    continue when k is null or k !~ '^[a-z_]{2,24}$';
    -- a showing counts once a kind in ten minutes (a page opened again and again is one look)
    continue when p_ev = 'shown' and exists (select 1 from public.regatta_suggest_event e where e.user_id = me and e.kind = k and e.ev = 'shown' and e.at > now() - interval '10 minutes');
    insert into public.regatta_suggest_event (user_id, kind, ev) values (me, k, p_ev);
    insert into public.regatta_suggest (user_id, kind) values (me, k) on conflict do nothing;
    update public.regatta_suggest s set
      weight = case p_ev when 'tap' then least(3, s.weight * 1.1) when 'dismiss' then greatest(0.2, s.weight * 0.8) when 'fewer' then greatest(0.2, s.weight * 0.5) else s.weight end,
      out_until = case when p_ev in ('dismiss', 'fewer') then now() + interval '7 days' else s.out_until end,
      shown = s.shown + (p_ev = 'shown')::int, tapped = s.tapped + (p_ev = 'tap')::int, dismissed = s.dismissed + (p_ev in ('dismiss', 'fewer'))::int
     where s.user_id = me and s.kind = k;
  end loop;
  return public.regatta_suggest_state();
end $$;
revoke all on function public.regatta_suggest_mark(text, text[]) from public, anon;
grant execute on function public.regatta_suggest_mark(text, text[]) to authenticated;
