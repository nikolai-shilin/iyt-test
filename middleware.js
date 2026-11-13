// Routing Middleware (Vercel, before the files): the Regatta game has its own address, regatta.rycrentals.com, on the
// same deployment as the app. A vercel.json rewrite cannot do this, since the file at / (index.html, the app) always
// wins over a rewrite; so the root on that host is served from regatta.html here. Everything else on that host (the
// game's scripts, /api/game, the fonts) is the same file as on iyt.rycrentals.com. vercel.json sends the old address,
// iyt.rycrentals.com/regatta, to the new one, and marks the game's host noindex.
export const config = { matcher: '/' };

export default function middleware(request) {
  const url = new URL(request.url);
  if (url.hostname !== 'regatta.rycrentals.com') return; // the app's Home, untouched
  url.pathname = '/regatta';
  return new Response(null, { headers: { 'x-middleware-rewrite': url.toString() } });
}
