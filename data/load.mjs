// Loads the question banks into Supabase (project iyt-test): every data/questions/<level>.json with its
// <level>.<lang>.json overlays goes through the load_bank() database function (supabase/migrations).
// Safe to run again: unchanged questions are left alone, questions dropped from a bank are marked inactive.
//
//   npm run db:load                       # all levels
//   npm run db:load -- bareboat-skipper   # one level
//
// Needs SUPABASE_URL and SUPABASE_SECRET_KEY (Supabase → Project Settings → API keys → secret key) in .env.local.

import { readdir, readFile } from 'node:fs/promises';

export const DIR = new URL('./questions/', import.meta.url);

// [{ level, bank, overlays: [overlay, ...] }] for the bank files in data/questions (optionally only some levels).
export async function readBanks(only = []) {
  const files = (await readdir(DIR)).filter((f) => f.endsWith('.json')).sort();
  const read = async (f) => JSON.parse(await readFile(new URL(f, DIR), 'utf8'));
  const out = [];
  for (const f of files) {
    const m = f.match(/^([a-z0-9-]+)\.json$/);
    if (!m || (only.length && !only.includes(m[1]))) continue;
    const overlays = await Promise.all(files.filter((o) => o.startsWith(`${m[1]}.`) && o !== f).map(read));
    out.push({ level: m[1], bank: await read(f), overlays });
  }
  return out;
}

// POST to a PostgREST function; the new sb_secret_ keys go in apikey only, legacy JWT keys also as a bearer token.
export async function rpc(fn, body, { url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY } = {}) {
  if (!url || !key) throw new Error('set SUPABASE_URL and SUPABASE_SECRET_KEY in .env.local');
  const headers = { apikey: key, 'content-type': 'application/json' };
  if (!key.startsWith('sb_')) headers.authorization = `Bearer ${key}`;
  const res = await fetch(`${url.replace(/\/$/, '')}/rest/v1/rpc/${fn}`, { method: 'POST', headers, body: JSON.stringify(body) });
  const text = await res.text();
  if (!res.ok) throw new Error(`${fn}: ${res.status} ${text}`);
  return JSON.parse(text);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const banks = await readBanks(process.argv.slice(2));
  if (!banks.length) throw new Error('no bank files matched');
  for (const { bank, overlays } of banks) {
    console.log(JSON.stringify(await rpc('load_bank', { p_bank: bank, p_overlays: overlays })));
  }
}
