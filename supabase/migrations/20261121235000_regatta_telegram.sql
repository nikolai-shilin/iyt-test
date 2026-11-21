-- Match found through the Telegram bot too (release 5c of the 1-on-1 plan; api/regatta-notify.mjs here, lib/push-send.ts
-- in the ryc-regatta repo).
--
-- A sailor who signed in to the site with Telegram (auth app_metadata.telegram_id) and whom this project's bot may write
-- to (public.users: they wrote to it, and haven't blocked it since) can be looked for while away even without a browser
-- that takes pushes: regatta_seek_away counts the bot as one of their devices. regatta_pair_push, the away sailor's
-- devices once per pair, now hands over the bot's chat with them as well (kind 'telegram', their Telegram id, in the
-- language of their browser's pushes if they have any, else the bot's), and the site has the bot send Match found.

-- the Telegram id the bot may write to for this account, or null
create function public.regatta_tg_writable(p_user uuid)
returns bigint language sql stable security definer set search_path = '' as $$
  select u.id from auth.users a join public.users u on u.id = (a.raw_app_meta_data ->> 'telegram_id')::bigint
   where a.id = p_user and a.raw_app_meta_data ? 'telegram_id' and u.blocked_at is null
$$;
revoke all on function public.regatta_tg_writable(uuid) from public, anon, authenticated;

create or replace function public.regatta_seek_away(p_on boolean)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  s public.regatta_seek;
  n int;
  tg boolean;
begin
  if me is null then return jsonb_build_object('status', 'none'); end if;
  perform pg_advisory_xact_lock(hashtext('regatta_seek'));
  if not coalesce(p_on, false) then
    update public.regatta_seek set away_until = null where user_id = me;
    return jsonb_build_object('status', 'here');
  end if;
  select count(*) into n from public.regatta_push where user_id = me;
  tg := public.regatta_tg_writable(me) is not null;
  if n = 0 and not tg then return jsonb_build_object('status', 'none', 'reason', 'no_push'); end if;
  update public.regatta_seek set away_until = now() + interval '30 minutes'
   where user_id = me and seen > now() - interval '10 seconds' and pair_id is null
  returning * into s;
  if not found then return jsonb_build_object('status', 'none', 'reason', 'not_looking'); end if;
  return jsonb_build_object('status', 'away', 'left', round(extract(epoch from s.away_until - now())), 'devices', n + case when tg then 1 else 0 end, 'telegram', tg);
end $$;

-- the away sailors of a pair just made: their browsers (kind 'push') and the bot's chat with them (kind 'telegram'),
-- once per pair, only with the vault's key
drop function public.regatta_pair_push(text, uuid);
create function public.regatta_pair_push(p_key text, p_pair uuid)
returns table (kind text, endpoint text, p256dh text, auth text, telegram_id bigint, lang text, them_name text, them_rating int, them_races int, ttl int)
language plpgsql volatile security definer set search_path = '' as $$
declare p public.regatta_pairs;
begin
  if p_key is null or p_key is distinct from (select decrypted_secret from vault.decrypted_secrets where name = 'regatta_push_key') then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  update public.regatta_pairs x set pushed_at = now() where x.id = p_pair and x.pushed_at is null and x.state = 'offered' returning * into p;
  if not found then return; end if;
  return query
    with away as (
      select u.user_id,
        case when u.user_id = p.host_user then p.guest_name else p.host_name end as them_name,
        case when u.user_id = p.host_user then p.guest_rating else p.host_rating end as them_rating,
        case when u.user_id = p.host_user then p.guest_races else p.host_races end as them_races
      from public.regatta_seek u where u.pair_id = p.id and public.regatta_seek_is_away(u))
    select 'push'::text, r.endpoint, r.p256dh, r.auth, null::bigint, r.lang, a.them_name, a.them_rating, a.them_races, p.ttl
      from away a join public.regatta_push r on r.user_id = a.user_id
    union all
    select 'telegram'::text, null, null, null, t.id,
      coalesce((select r.lang from public.regatta_push r where r.user_id = a.user_id order by r.seen_at desc nulls last limit 1), t.lang, 'en'),
      a.them_name, a.them_rating, a.them_races, p.ttl
      from away a join public.users t on t.id = public.regatta_tg_writable(a.user_id);
end $$;

revoke all on function public.regatta_pair_push(text, uuid) from public;
grant execute on function public.regatta_pair_push(text, uuid) to anon, authenticated;
