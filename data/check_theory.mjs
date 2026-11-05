// Checks the theory articles (data/theory/<level>/<topic>[.ru].json) against docs/theory.md and the question banks.
//
//   node data/check_theory.mjs            every level that has articles
//   node data/check_theory.mjs <level>    one level, with each topic's references and how many questions use them
//
// Exits 1 if any article breaks a rule.

import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const only = process.argv[2];

// figures.js is a browser script: run it here to draw every figure once
const figSrc = await readFile(join(root, 'docs/design/figures.js'), 'utf8');
const { FIG, figSvg, FIG_KEYS } = new Function(`${figSrc}\nreturn { FIG, figSvg, FIG_KEYS };`)();

const LIMITS = { sections: [4, 7], words: [400, 900], pictures: 4, bigRef: 10, q: 18, a: [8, 45] };
const KINDS = ['p', 'list', 'fig', 'tiles', 'rule', 'table'];
const kind = (b) => KINDS.find((k) => b && typeof b === 'object' && k in b);
const words = (s) => (String(s).match(/[\p{L}\p{N}][\p{L}\p{N}'’().+-]*/gu) || []).length;
const readJson = async (f) => { try { return JSON.parse(await readFile(f, 'utf8')); } catch (e) { if (e.code === 'ENOENT') return null; throw new Error(`${f}: ${e.message}`); } };

let failed = 0;

// One article: its errors, and what it holds (words, pictures, the references it covers).
function check(a, topic, refs) {
  const err = [];
  const str = (v, what) => { if (typeof v !== 'string' || !v.trim()) err.push(`${what}: empty`); return String(v || ''); };
  let w = 0, pics = 0;
  const covered = new Set();
  if (a.topic !== topic) err.push(`topic is "${a.topic}", the file is ${topic}`);
  w += words(str(a.lead, 'lead'));
  const secs = Array.isArray(a.sections) ? a.sections : [];
  if (secs.length < LIMITS.sections[0] || secs.length > LIMITS.sections[1]) err.push(`${secs.length} sections (${LIMITS.sections.join('–')})`);
  const ids = new Set();
  const figure = (f, where) => {
    if (!f || !FIG[f.type]) return err.push(`${where}: no figure type "${f && f.type}"`);
    // a labelled figure names its parts by key; a key it does not know is silently not drawn, so it is an error here
    if (FIG_KEYS[f.type]) for (const [k] of f.parts || f.flags || f.lines || []) if (!(k in FIG_KEYS[f.type](f))) err.push(`${where}: the ${f.type} figure${f.view ? ` (${f.view})` : ''} has no "${k}"`);
    try { const s = figSvg(f); if (/NaN|undefined/.test(s)) err.push(`${where}: the ${f.type} figure draws NaN or undefined`); } catch (e) { err.push(`${where}: the ${f.type} figure fails: ${e.message}`); }
  };
  const view = (v, where) => { if (v != null && !/^-?\d+(\.\d+)? -?\d+(\.\d+)? \d+(\.\d+)? \d+(\.\d+)?$/.test(v)) err.push(`${where}: view "${v}" is not "x y w h"`); };
  for (const s of secs) {
    const at = `section ${s.id}`;
    if (!/^[a-z][a-z0-9-]*$/.test(s.id || '')) err.push(`${at}: id must be lower case letters, digits and dashes`);
    if (ids.has(s.id)) err.push(`${at}: id used twice`);
    ids.add(s.id);
    w += words(str(s.kicker, `${at} kicker`)) + words(str(s.title, `${at} title`));
    // the opener (optional): a question as a reader would ask it, and the answer in a sentence or two; not counted in the words
    if (s.qa != null) {
      const q = str(s.qa.q, `${at} qa.q`), a = str(s.qa.a, `${at} qa.a`);
      if (!/\?$/.test(q.trim())) err.push(`${at}: qa.q is not a question (ends in ?)`);
      if (words(q) > LIMITS.q) err.push(`${at}: qa.q has ${words(q)} words (at most ${LIMITS.q})`);
      if (words(a) < LIMITS.a[0] || words(a) > LIMITS.a[1]) err.push(`${at}: qa.a has ${words(a)} words (${LIMITS.a.join('–')})`);
    }
    for (const r of s.refs || []) { if (!(r in refs)) err.push(`${at}: the bank has no reference "${r}" in this topic`); covered.add(r); }
    let shown = 0;
    (s.blocks || []).forEach((b, i) => {
      const k = kind(b), wh = `${at} block ${i + 1}`;
      if (!k) return err.push(`${wh}: unknown block ${JSON.stringify(b).slice(0, 60)}`);
      if (k === 'p' || k === 'rule') w += words(str(b[k], wh));
      if (k === 'rule' && b.label != null) w += words(str(b.label, `${wh} label`));
      if (k === 'list') { if (!Array.isArray(b.list) || !b.list.length) err.push(`${wh}: empty list`); else b.list.forEach((x) => { w += words(str(x, wh)); }); }
      if (k === 'fig') { figure(b.fig, wh); view(b.view, wh); if (b.cap != null) w += words(str(b.cap, `${wh} cap`)); pics++; shown++; }
      if (k === 'tiles') {
        if (!Array.isArray(b.tiles) || b.tiles.length < 2) err.push(`${wh}: tiles need two or more`);
        if (b.cols != null && ![2, 3, 4].includes(b.cols)) err.push(`${wh}: cols 2–4`);
        (b.tiles || []).forEach((x, j) => { figure(x.fig, `${wh} tile ${j + 1}`); view(x.view, `${wh} tile ${j + 1}`); w += words(str(x.name, `${wh} tile ${j + 1} name`)); if (x.note != null) w += words(x.note); pics++; });
        shown++;
      }
      if (k === 'table') {
        const tb = b.table || {}, n = (tb.head || []).length;
        if (n < 2 || n > 4) err.push(`${wh}: a table has 2–4 columns`);
        if (!Array.isArray(tb.rows) || !tb.rows.length) err.push(`${wh}: a table needs rows`);
        (tb.rows || []).forEach((r, j) => { if (r.length !== n) err.push(`${wh}: row ${j + 1} has ${r.length} cells, the head has ${n}`); r.forEach((c) => { w += words(c); }); });
        (tb.head || []).forEach((c) => { w += words(c); });
        shown++;
      }
    });
    if (!shown) err.push(`${at}: no picture or table`);
  }
  if (w < LIMITS.words[0] || w > LIMITS.words[1]) err.push(`${w} words (${LIMITS.words.join('–')})`);
  if (pics < LIMITS.pictures) err.push(`${pics} pictures (at least ${LIMITS.pictures})`);
  for (const [r, n] of Object.entries(refs)) if (n >= LIMITS.bigRef && !covered.has(r)) err.push(`reference "${r}" (${n} questions) is not covered by any section`);
  const total = Object.values(refs).reduce((x, y) => x + y, 0);
  const hit = Object.entries(refs).reduce((x, [r, n]) => x + (covered.has(r) ? n : 0), 0);
  return { err, words: w, pics, cover: total ? Math.round((hit / total) * 100) : 0 };
}

// A figure with its words taken out: what must be the same in every language (the type, the numbers, the keys that
// choose what is drawn). Free text is any other string.
const FIXED = new Set(['type', 'kind', 'view', 'shape', 'c', 'region', 'land', 'track', 'hull', 'path']);
function bare(v, key) {
  // in a list, the words are dropped too, but the key of a named part, line or flag ([i][0]) and a mark's colour (marks[i][2]) stay
  if (Array.isArray(v)) return v.map((x, i) => (typeof x === 'string' ? ((['parts.item', 'lines.item', 'flags.item'].includes(key) && i === 0) || (key === 'marks.item' && i === 2) ? x : '') : bare(x, `${key}.item`)));
  if (v && typeof v === 'object') return Object.fromEntries(Object.keys(v).sort().map((k) => [k, typeof v[k] === 'string' ? (FIXED.has(k) ? v[k] : '') : bare(v[k], k)]));
  return v;
}
// The translation holds the same things in the same order as the source.
function parity(en, ru) {
  const err = [];
  const figs = (a) => (a.sections || []).flatMap((s) => (s.blocks || []).flatMap((b) => (b.fig ? [b.fig] : b.tiles ? b.tiles.map((x) => x.fig) : [])));
  const fe = figs(en), fr = figs(ru);
  fe.forEach((f, i) => { if (fr[i] && JSON.stringify(bare(f)) !== JSON.stringify(bare(fr[i]))) err.push(`picture ${i + 1} (${f.type}) is not the English one with its words translated`); });
  const shape = (a) => (a.sections || []).map((s) => `${s.id}[${(s.refs || []).join('|')}]${s.qa ? ' qa' : ''}: ` + (s.blocks || []).map((b) => {
    const k = kind(b);
    if (k === 'fig') return `fig:${b.fig && b.fig.type}:${b.view || ''}`;
    if (k === 'tiles') return `tiles:${(b.tiles || []).map((x) => `${x.fig && x.fig.type}:${x.view || ''}`).join(',')}:${b.cols || ''}`;
    if (k === 'table') return `table:${(b.table.head || []).length}x${(b.table.rows || []).length}`;
    if (k === 'list') return `list:${(b.list || []).length}`;
    return k;
  }).join(' '));
  const a = shape(en), b = shape(ru);
  if (a.length !== b.length) err.push(`${b.length} sections, the English article has ${a.length}`);
  a.forEach((x, i) => { if (b[i] !== undefined && b[i] !== x) err.push(`section ${i + 1} differs from the English one:\n      en ${x}\n      ru ${b[i]}`); });
  const text = JSON.stringify((ru.sections || []).map((s) => [s.title, (s.blocks || []).map((b) => b.p || b.rule || '')]));
  if (!/[а-яё]/i.test(text)) err.push('no Russian text');
  return err;
}

const tdir = join(root, 'data/theory');
const levels = (await readdir(tdir).catch(() => [])).filter((l) => !only || l === only).sort();
if (only && !levels.length) { console.error(`no articles for ${only}`); process.exit(1); }
for (const level of levels) {
  if (!(await stat(join(tdir, level))).isDirectory()) continue;
  const bank = await readJson(join(root, 'data/questions', `${level}.json`));
  if (!bank) { console.error(`${level}: no bank data/questions/${level}.json`); failed++; continue; }
  console.log(`\n${bank.title}`);
  const files = (await readdir(join(tdir, level))).filter((f) => f.endsWith('.json'));
  for (const f of files) {
    const id = f.replace(/(\.ru)?\.json$/, '');
    if (!bank.topics.some((tp) => tp.id === id)) { console.error(`  ✗ ${f}: the bank has no topic "${id}"`); failed++; }
  }
  for (const tp of bank.topics) {
    const refs = {};
    for (const q of bank.questions) if (q.topic === tp.id) refs[q.ref] = (refs[q.ref] || 0) + 1;
    const en = await readJson(join(tdir, level, `${tp.id}.json`));
    const ru = await readJson(join(tdir, level, `${tp.id}.ru.json`));
    if (!en) { console.log(`  –  ${tp.id.padEnd(12)} not written${ru ? ' (a Russian file without the English one)' : ''}`); if (ru) failed++; continue; }
    const r = check(en, tp.id, refs);
    const errs = r.err.map((e) => `en: ${e}`);
    if (ru) { errs.push(...check(ru, tp.id, refs).err.map((e) => `ru: ${e}`), ...parity(en, ru).map((e) => `ru: ${e}`)); }
    console.log(`  ${errs.length ? '✗' : '✓'}  ${tp.id.padEnd(12)} ${String(r.words).padStart(4)} words  ${String(r.pics).padStart(2)} pictures  ${String(r.cover).padStart(3)}% of questions covered  ${ru ? 'en + ru' : 'en only'}`);
    errs.forEach((e) => console.log(`       ${e}`));
    failed += errs.length;
    if (only) {
      const used = new Set(en.sections.flatMap((s) => s.refs || []));
      console.log('       ' + Object.entries(refs).sort((a, b) => b[1] - a[1]).map(([x, n]) => `${used.has(x) ? '' : '·'}${x} ${n}`).join(' | '));
    }
  }
}
if (failed) { console.error(`\n${failed} problem${failed === 1 ? '' : 's'}`); process.exit(1); }
console.log('\nall articles pass');
