-- The 1-on-1 tab of your player card (release 7d of the 1-on-1 plan; the ryc-regatta repo: components/player-tabs.tsx,
-- lib/my-duels.ts). regatta_my_duels(): for the signed-in sailor alone, every 1-on-1 they finished (the latest 300, the
-- latest first): when, the other sailor's name, won or not, the margin, a forfeit, rated or not and the change, the
-- venue and the yacht; and their rivals, each account they finished races against with a winner (the most met first,
-- ten at most): the name they last raced under, how many races, won and lost, and that sailor's rating and rated races
-- now. No ids: a rival is told apart by account in here, but only named out of it.

create function public.regatta_my_duels()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare me uuid := auth.uid();
begin
  if me is null then return null; end if;
  return jsonb_build_object(
    'races', (select coalesce(jsonb_agg(jsonb_build_object('at', x.started_at, 'them', x.them, 'won', x.won, 'margin', x.margin, 'forfeit', x.forfeit,
                 'delta', x.delta, 'venue', x.venue, 'yacht', x.yacht) order by x.started_at desc), '[]'::jsonb)
              from (select d.started_at, case when d.host_user = me then d.guest_name else d.host_name end as them,
                           case when d.winner is not null then d.winner = (case when d.host_user = me then 'host' else 'guest' end) end as won,
                           d.margin, d.forfeited is not null as forfeit, d.venue, d.yacht,
                           (select c.delta from public.regatta_rating_change c where c.duel_id = d.id and c.user_id = me) as delta
                      from public.regatta_duels d
                     where (d.host_user = me or d.guest_user = me) and d.state = 'finished'
                     order by d.started_at desc limit 300) x),
    'rivals', (select coalesce(jsonb_agg(jsonb_build_object('name', y.name, 'met', y.met, 'wins', y.wins, 'losses', y.met - y.wins,
                  'rating', r.rating, 'races', r.races) order by y.met desc, y.last desc), '[]'::jsonb)
               from (select h.them, count(*) as met, count(*) filter (where h.won) as wins, max(h.started_at) as last,
                            (array_agg(h.name order by h.started_at desc))[1] as name
                       from (select case when d.host_user = me then d.guest_user else d.host_user end as them,
                                    case when d.host_user = me then d.guest_name else d.host_name end as name, d.started_at,
                                    d.winner = (case when d.host_user = me then 'host' else 'guest' end) as won
                               from public.regatta_duels d
                              where (d.host_user = me or d.guest_user = me) and d.state = 'finished' and d.winner is not null
                                and d.host_user is not null and d.guest_user is not null and d.host_user <> d.guest_user) h
                      group by h.them order by count(*) desc, max(h.started_at) desc limit 10) y
               left join public.regatta_rating r on r.user_id = y.them));
end $$;
revoke all on function public.regatta_my_duels() from public, anon;
grant execute on function public.regatta_my_duels() to authenticated;
