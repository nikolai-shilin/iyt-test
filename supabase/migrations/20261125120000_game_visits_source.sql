-- Up and down: where a game visitor first came from, so the social strategy (ryc-regatta docs/social-strategy.md) can
-- tell which network and which post brings visitors and makes accounts. The site keeps the browser's first touch for
-- 30 days (ryc-regatta public/game/first-touch.js, localStorage regatta-src) and the race's opening post carries it
-- (api/game.mjs openOf); a new account takes a copy in auth.users.raw_user_meta_data->'src' (ryc-regatta
-- components/bests-sync.tsx sourceFor), which needs no column.
--   src       the first tagged link's utm_source, or our own ?src= (telegram, instagram, share …)
--   medium    its utm_medium (post, story, result, duel …)
--   campaign  its utm_campaign (daily-2026-11-25 …)
--   ref_host  another site it came from (google.com, l.instagram.com …), when the browser said
--   app       the app whose own browser it opened in, from its user agent (instagram, threads, facebook, telegram, linkedin)
-- Each null for a browser with no touch kept (most: Telegram's and Instagram's browsers send no referrer).

alter table public.game_visits add column if not exists src text check (length(src) <= 32);
alter table public.game_visits add column if not exists medium text check (length(medium) <= 32);
alter table public.game_visits add column if not exists campaign text check (length(campaign) <= 64);
alter table public.game_visits add column if not exists ref_host text check (length(ref_host) <= 64);
alter table public.game_visits add column if not exists app text check (app in ('instagram', 'threads', 'facebook', 'telegram', 'linkedin'));
