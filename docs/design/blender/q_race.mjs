// Racing Rules test images: the race diagrams (figure type `race`) in the plan-view schematic look of
// figure-schematic.js / q_chart.mjs (flat, theme tokens, Carlito, pills, a faint grid, the key band along the bottom).
// For each id in figure-style/questions/racing-rules/race.json it writes
//   <id>/q.json     the image for the question: the figure's own data and nothing more (boats, headings, tacks,
//                   labels, wind, mark and zone, line, obstruction, track; the note is the title of the key band)
//   <id>/plan.json  the same diagram with the reasoning on it, when <id>/plan.spec.json exists (format below)
//   <id>/ru.json    the Russian of every text node drawn in either
// Both are {svg}: 1280 wide, the figures.js 320×200 frame mapped uniformly (zoomed to fit what is drawn) into the
// area above the key band. Geometry is the figures.js FIG.race geometry: same positions, headings, hull length
// (44 × scale per length, the drawn hull 40 × scale), zone radius 3 lengths, sail on the leeward side for the wind
// (heading − wind in (0°,180°): boom to starboard, port tack; otherwise boom to port, starboard tack; exactly head
// to wind the boom lies on the centreline, sail flapping).
//
//   node docs/design/blender/q_race.mjs [rr-001 | definitions ...] [--check]
//        --check: only validate the plan specs (names, colours, coordinates, Russian), write nothing
//   then: node docs/design/blender/capture_questions.mjs racing-rules --type race [--ru]
//
// ───────────────────────── plan.spec.json: the plan for the answer ─────────────────────────
// One file per question, <id>/plan.spec.json. Write it from the question, `answer` and `why` in race.json; the
// diagram itself (boats, mark, zone, line, wind…) is drawn from the figure, you only add the reasoning. Everything
// is optional except "title". Coordinates are the figure's own: 320×200 units, x right, y down, as in race.json.
// Boats are named by their label in the figure ("You", "Red", "Blue", "A"…).
// {
//   "title": "Red is clear astern",                  // bold first line of the key band: the answer in a few words
//   "key": ["Definition Clear Astern: her hull is behind the line abeam your transom", "…"],
//                                                     // 1–3 short lines, rule numbers here (≤ ~70 characters each)
//   "keep":  ["Red"],                                // must keep clear: red ring round the hull + "keeps clear" tag;
//                                                     //   ["Red", "must give room"] puts your own words on the tag
//   "right": ["You"],                                // right of way: blue ring + "right of way" tag (or ["You", "…"])
//   "tags":  [["Red", "clear astern", "light"]],     // more tags under a boat's name; kind light|red|accent|ink|green
//   "tack":  true,                                   // "port tack" / "starboard tack" under every boat (or ["You"]),
//                                                     //   read from the drawing, so it always agrees with the sails
//   "abeam": ["You"],                                // the line abeam the named boat's transom (overlap, clear astern)
//   "zone":  true,                                   // the mark's zone drawn bold with "zone · 3 hull lengths"
//                                                     //   (also when the question image has no zone); a number
//                                                     //   instead of true is the radius in figure units (e.g. three
//                                                     //   lengths of a bigger boat nearer the mark: 3 × 44 × scale)
//   "arrows": [[x1, y1, x2, y2, "red"]],             // an arrow; colour red|accent|ink|green|course|muted;
//                                                     //   a 6th item "dash" makes it dashed
//   "lines":  [[x1, y1, x2, y2, "ink", "dash"]],     // a line without a head (same colours, "dash" optional)
//   "rings":  [[x, y, r, "red"]],                    // a dashed circle, r in figure units
//   "tracks": [["M120 55 L95 100 L125 140", "accent"]],   // a path (M L C Q) with an arrowhead at its end
//   "ghosts": [{ "of": "You", "x": 150, "y": 90, "hdg": 45, "text": "after the tack" }],
//                                                     // the named boat again, faded, at another place or heading
//                                                     //   (its sail set for that heading); "text" is optional
//   "pills":  [[x, y, "text", "red"]],               // a text pill near (x, y); kind light|red|accent|ink|green
//   "ru": { "Red is clear astern": "Red чисто позади", "…": "…" }
//                                                     // Russian for EVERY string the spec adds (title, key lines,
//                                                     //   tags, pills, ghost texts); built-ins are known already:
//                                                     //   keeps clear, right of way, port tack, starboard tack,
//                                                     //   line abeam, zone · 3 hull lengths, and every figure string
// }
// Rules: the plan must agree with `answer` and `why`; mark the give-way boat with "keep" and the right-of-way boat
// with "right" when the question is about who keeps clear; say the rule in the key ("Rule 11: windward keeps clear").
// Keep text short: tags ≤ 20 characters, pills ≤ 28, key lines ≤ 70. The script reports unknown boats, keys,
// colours and every string without Russian; run it with --check after writing specs.
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(HERE, '..', 'figure-style', 'questions', 'racing-rules');
const ARGS = process.argv.slice(2), CHECK = ARGS.includes('--check'), ONLY = ARGS.filter(a => !a.startsWith('--'));
const W = 1280, HQ = 800;
const RAD = Math.PI / 180;
const pol = (x, y, r, deg) => [x + r * Math.sin(deg * RAD), y - r * Math.cos(deg * RAD)];
const f1 = v => (+v).toFixed(1);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const COLS = { red: '#e8231a', accent: 'var(--accent)', ink: 'var(--ink)', green: '#1a9a48', course: '#e0b400', muted: 'var(--muted)' };
const MARKY = '#ffa800', LAND = '#d8c9a3', COAST = '#6b5a3a', SAND = '#ece0bd';
// boat colours by name: You as the app (accent), the rest as named; anything else from a spare palette
const BOATCOL = {
  You: ['var(--accent)', '#fff'], Red: ['#e0251b', '#fff'], Blue: ['#1d3c96', '#fff'], Green: ['#17924a', '#fff'],
  Yellow: ['#f2c200', '#1a1a1a'], Grey: ['#8b949c', '#fff'], Black: ['#1b1f23', '#fff'], White: ['#ffffff', '#1a1a1a'],
};
const SPARE = [['#7b4fc4', '#fff'], ['#0e8f83', '#fff'], ['#c4661b', '#fff'], ['#b0397a', '#fff'], ['#56657a', '#fff']];
const BUILTIN = {
  Wind: 'Ветер', You: 'Вы', zone: 'зона', pin: 'знак', RC: 'ГК', 'keeps clear': 'сторонится', 'right of way': 'право дороги',
  'port tack': 'левый галс', 'starboard tack': 'правый галс', 'line abeam': 'линия траверза', 'zone · 3 hull lengths': 'зона · 3 длины корпуса',
};

/* ───────────────── text: every text node is recorded, so ru.json covers it ───────────────── */
let USED = new Set(), RUMAP = {}, FRAG = {}, WARN = [];
const isCode = s => !/[A-Za-zА-Яа-я]/.test(s);
const ruOf = s => FRAG[s] ?? RUMAP[s] ?? (isCode(s) ? s.replace(/(\d)\.(\d)/g, '$1,$2') : s);
const CW = c => ' '.includes(c) ? .23 : '.,:;\'|il′·()[]!'.includes(c) ? .26 : 'ftrIj'.includes(c) ? .34 : 'mwMWшщжмШЩЖЮюы'.includes(c) ? .8
  : /[0-9]/.test(c) ? .507 : '°'.includes(c) ? .36 : '←→'.includes(c) ? .95 : /[A-ZА-ЯЁ]/.test(c) ? .62 : .52;
const tw0 = (s, size) => [...String(s)].reduce((a, c) => a + CW(c), 0) * size;
const tw = (s, size) => Math.max(tw0(s, size), tw0(ruOf(s), size));      // room for the Russian too
function txt(x, y, s, o = {}) {
  s = String(s); if (!isCode(s)) USED.add(s);
  const halo = o.halo === false ? '' : `stroke="var(--bg)" stroke-width="${o.haloW || 8}" stroke-linejoin="round" paint-order="stroke"`;
  return `<text x="${f1(x)}" y="${f1(y)}" font-size="${o.s || 32}" font-weight="${o.w || 700}" fill="${o.f || 'var(--ink)'}" text-anchor="${o.a || 'middle'}" ${halo}>${esc(s)}</text>`;
}
const PILLK = { light: ['var(--bg)', 'var(--ink)', 'var(--tag-line)'], red: [COLS.red, '#fff'], accent: ['var(--accent)', '#fff'], ink: ['var(--ink)', 'var(--bg)'], green: [COLS.green, '#fff'] };
const pillWH = (text, size = 30) => [tw(text, size) + size * 1.2, size * 1.6];
function pill(cx, cy, text, kind = 'light', size = 30, colours) {
  const [w, h] = pillWH(text, size), [fill, ink, stroke] = colours || PILLK[kind] || PILLK.light;
  return `<rect x="${f1(cx - w / 2)}" y="${f1(cy - h / 2)}" width="${f1(w)}" height="${f1(h)}" rx="${f1(h / 2)}" fill="${fill}" stroke="${stroke || (fill === '#ffffff' ? 'var(--ink)' : fill)}" stroke-width="3"/>` + txt(cx, cy + size * 0.35, text, { f: ink, s: size, halo: false });
}
// a string wrapped to the width, the English and the Russian into the same number of lines, line for line:
// the capture page translates each text node on its own, so every English line maps to its Russian line
function wrapPair(text, size, maxW) {
  const en = String(text), ru = ruOf(en);
  const part = (s, n) => {
    const words = s.split(' ').filter(Boolean); if (words.length < n) return null;
    const wd = words.map(w => tw0(w, size)), sp = tw0(' ', size), m = words.length;
    const width = (i, j) => wd.slice(i, j).reduce((a, b) => a + b, 0) + sp * (j - i - 1);
    const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(Infinity)), cut = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
    dp[0][0] = 0;
    for (let k = 1; k <= n; k++) for (let j = 1; j <= m; j++) for (let i = k - 1; i < j; i++) {
      const v = Math.max(dp[k - 1][i], width(i, j)); if (v < dp[k][j]) { dp[k][j] = v; cut[k][j] = i; } }
    const lines = []; let j = m; for (let k = n; k >= 1; k--) { const i = cut[k][j]; lines.unshift(words.slice(i, j).join(' ')); j = i; }
    return { lines, w: dp[n][m] };
  };
  for (let n = 1; n <= 6; n++) {
    const a = part(en, n), b = part(ru, n);
    if (!a) break;
    if (a.w <= maxW && (!b || b.w <= maxW) || n === 6) {
      if (!b) { FRAG[en] = ru; return [en]; }
      a.lines.forEach((l, i) => { if (FRAG[l] !== undefined && FRAG[l] !== b.lines[i] && l !== en) WARN.push(`${CUR}: line "${l}" wraps two ways`); FRAG[l] = b.lines[i]; });
      return a.lines;
    }
  }
  return [en];
}

/* ───────────────── geometry of figures.js ───────────────── */
const HULL = 'M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z';
const relOf = (hdg, wind) => ((hdg - wind) % 360 + 360) % 360;
// figures.js: rel < 180 → boom +14 (to starboard): the wind comes over the port side, port tack
const tackOf = (hdg, wind) => relOf(hdg, wind) < 180 ? 'port' : 'starboard';
const boomSide = (hdg, wind) => relOf(hdg, wind) < 180 ? 1 : -1;
const boomAngle = (hdg, wind) => { const r = relOf(hdg, wind), th = Math.min(r, 360 - r); return th === 0 ? 0 : Math.max(7, Math.min(80, (th - 28) * 0.62)); };

/* ───────────────── the scene: everything in pixel space, with a label placer ───────────────── */
function bandOf(title, key) {
  const lines = [];   // {t, s, w, x, dy}
  if (title) wrapPair(title, 38, W - 64).forEach((t, i) => lines.push({ t, s: 38, w: 700, x: 32, dy: i ? 46 : 0 }));
  for (const k of key || []) wrapPair(k, 32, W - 90).forEach((t, i) => lines.push({ t, s: 32, w: 400, x: 54, dy: i ? 42 : (lines.length ? 50 : 0), bullet: !i }));
  const h = lines.length ? 54 + lines.reduce((a, l) => a + l.dy, 0) + 28 : 0;
  return { lines, h };
}

function render(e, spec) {
  const f = e.figure, wind = f.wind ?? 0, sc = f.scale || 0.6, len = 44 * sc;
  const plan = !!spec, P0 = [];
  const boats = (f.boats || []).map((b, i) => ({ ...b, i, hdg: b.hdg ?? 0, bs: b.scale || sc }));
  // colours: by name, spare palette for the rest (never two boats alike)
  const taken = new Set(); boats.forEach(b => { const c = BOATCOL[b.you ? 'You' : b.label]; if (c && !taken.has(c[0])) { b.col = c; taken.add(c[0]); } });
  let sp = 0; boats.forEach(b => { if (!b.col) { while (taken.has(SPARE[sp % SPARE.length][0]) && sp < 20) sp++; b.col = SPARE[sp++ % SPARE.length]; taken.add(b.col[0]); } });
  const byName = Object.fromEntries(boats.map(b => [b.label, b]));

  // ---- the band and the drawing area
  const band = plan ? bandOf(spec.title, spec.key) : bandOf(f.note || '', []);
  const H = plan ? Math.max(HQ, 640 + band.h) : HQ, Ha = H - band.h;

  // ---- the view: fitted round what is drawn, zoomed in as far as a 170-unit-wide view
  const fit = [];
  const onBorder = ([x, y]) => x <= 0 || x >= 320 || y <= 0 || y >= 200;
  for (const b of boats) { fit.push([b.x - 22 * b.bs, b.y - 22 * b.bs], [b.x + 22 * b.bs, b.y + 22 * b.bs], pol(b.x, b.y, Math.max(1.4 * len, 22 * b.bs + 10), b.hdg)); }
  if (f.mark) { const m = f.mark, r = plan && typeof spec.zone === 'number' ? spec.zone : (m.zone === true || (plan && spec.zone)) ? 3 * len : (m.zone || 8); const a = [m.x - r, m.y - r], b = [m.x + r, m.y + r]; a.zoneBox = b.zoneBox = true; fit.push(a, b); }
  if (f.line) { const l = f.line; fit.push([l.x1, l.y1], [l.x2, l.y2], [l.x2 - len * .6, l.y2 + len * .6], [l.x2 + len * .6, l.y2 - len * .6]); }
  const obs = f.obstruction;
  if (obs) {
    if (obs.path) { for (const sub of pathPts(obs.path)) for (const q of sub) if (!onBorder(q)) fit.push(q); }
    else fit.push([obs.x, obs.y], [obs.x + obs.w, obs.y + obs.h]);
    if (obs.lx != null) fit.push([obs.lx, obs.ly]);
  }
  if (f.track) for (const sub of pathPts(f.track)) fit.push(...sub);
  if (plan) {
    for (const a of [...(spec.arrows || []), ...(spec.lines || [])]) fit.push([a[0], a[1]], [a[2], a[3]]);
    for (const r of spec.rings || []) fit.push([r[0] - r[2], r[1] - r[2]], [r[0] + r[2], r[1] + r[2]]);
    for (const p of spec.pills || []) fit.push([p[0], p[1]]);
    for (const g of spec.ghosts || []) { const bs = byName[g.of]?.bs || sc; fit.push([g.x - 22 * bs, g.y - 22 * bs], [g.x + 22 * bs, g.y + 22 * bs]); }
    for (const t of spec.tracks || []) for (const sub of pathPts(t[0])) fit.push(...sub);
  }
  const busy = fit.filter(q => !q.zoneBox);
  if (f.mark) { const m = f.mark, r = plan && typeof spec.zone === 'number' ? spec.zone : (m.zone === true || (plan && spec.zone)) ? 3 * len : (m.zone || 0);
    for (let a = 0; a < 360; a += 15) busy.push(pol(m.x, m.y, r, a)); busy.push([m.x, m.y]); }
  const xs = fit.map(p => p[0]), ys = fit.map(p => p[1]);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const padX = 110, padY = 95;
  let k = Math.min((W - 2 * padX) / Math.max(x1 - x0, 1), (Ha - 2 * padY) / Math.max(y1 - y0, 1), W / 170);
  // the wind needs a free corner: zoom out a step at a time while every corner is crowded
  let ox, oy, P, windAt;
  const corners = [[W - 92, 60], [92, 60], [W - 92, Ha - 190], [92, Ha - 190]];
  for (let tries = 0; tries < 6; tries++) {
    ox = W / 2 - (x0 + x1) / 2 * k; oy = Ha / 2 - (y0 + y1) / 2 * k;
    P = (x, y) => [ox + x * k, oy + y * k];
    const pts = busy.map(q => P(...q));
    const crowd = c => pts.filter(([px, py]) => px > c[0] - 100 && px < c[0] + 100 && py > c[1] - 20 && py < c[1] + 200).length;
    const best = corners.map((c, i) => [crowd(c), i]).sort((a, b) => a[0] - b[0] || a[1] - b[1])[0];
    windAt = corners[best[1]];
    if (best[0] === 0) break;
    k *= 0.88;
  }
  const S = v => v * k;

  // ---- obstacles for the label placer
  const OB = [];
  const addOb = (bx0, by0, bx1, by1, w = 1) => OB.push([bx0, by0, bx1, by1, w]);
  const addPt = (x, y, r, w = 1) => addOb(x - r, y - r, x + r, y + r, w);
  const addSeg = (a, b, r, w = 1) => { const n = Math.max(2, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / (r * 1.5))); for (let i = 0; i <= n; i++) addPt(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, r, w); };
  const ov = (b, o) => Math.max(0, Math.min(b[2], o[2]) - Math.max(b[0], o[0])) * Math.max(0, Math.min(b[3], o[3]) - Math.max(b[1], o[1]));
  const inFrame = (cx, cy, w, h) => [Math.min(Math.max(cx, w / 2 + 12), W - w / 2 - 12), Math.min(Math.max(cy, h / 2 + 10), Ha - h / 2 - 10)];
  // the clear spot nearest to where the label belongs; candidates: [cx, cy, extra cost]
  const place = (cands, w, h, ax, ay, obW = 3, own = null) => {
    let best = null, bestC = Infinity;
    for (const [cx0, cy0, extra = 0] of cands) {
      const [cx, cy] = inFrame(cx0, cy0, w, h), b = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
      let c = OB.reduce((a, o) => a + ov(b, o) * o[4], 0) * 10 + Math.hypot(cx - ax, cy - ay) * h * 0.6 + extra * h;
      if (own) { const dOwn = Math.hypot(cx - own[0], cy - own[1]); for (const q of BOATPX) if (q !== own) { const dq = Math.hypot(cx - q[0], cy - q[1]); if (dq < dOwn + 20) c += (dOwn + 20 - dq) * h * 3; } }
      if (c < bestC) { bestC = c; best = [cx, cy]; }
    }
    addOb(best[0] - w / 2, best[1] - h / 2, best[0] + w / 2, best[1] + h / 2, obW); return best;
  };
  const around = (ax, ay, bx, by, w, h, gap = 10, prefer = 'below') => {   // round a box [bx0,by0,bx1,by1]
    const c = [], [bx0, by0, bx1, by1] = [ax - bx, ay - by, ax + bx, ay + by];
    for (let r = 0; r < 5; r++) {
      const g = gap + r * 26;
      const set = [[ax, by1 + g + h / 2, 0], [ax, by0 - g - h / 2, 0.4], [bx1 + g + w / 2, ay, 0.6], [bx0 - g - w / 2, ay, 0.6],
        [bx1 + g + w / 2 - w * 0.3, by1 + g + h / 2, 0.5], [bx0 - g - w / 2 + w * 0.3, by1 + g + h / 2, 0.5],
        [bx1 + g + w / 2 - w * 0.3, by0 - g - h / 2, 0.7], [bx0 - g - w / 2 + w * 0.3, by0 - g - h / 2, 0.7]];
      if (prefer === 'above') { set[0][2] = 0.4; set[1][2] = 0; }
      c.push(...set.map(([x, y, e]) => [x, y, e + r * 0.3]));
    }
    return c;
  };

  let under = '', mid = '', top = '', labels = '';
  // ---- the water, a faint grid one hull length apart
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">`;
  const clip = `rr-${e.id}-${plan ? 'p' : 'q'}`;
  s += `<defs><clipPath id="${clip}"><rect x="0" y="0" width="${W}" height="${Ha}"/></clipPath></defs><rect width="${W}" height="${H}" fill="var(--bg)"/>`;
  s += `<g clip-path="url(#${clip})"><rect width="${W}" height="${Ha}" fill="rgba(60,140,190,.07)"/>`;
  const step = S(len), gx0 = f.mark ? P(f.mark.x, 0)[0] : ox, gy0 = f.mark ? P(0, f.mark.y)[1] : oy;
  for (let gx = ((gx0 % step) + step) % step; gx < W; gx += step) s += `<line x1="${f1(gx)}" y1="0" x2="${f1(gx)}" y2="${Ha}" stroke="var(--line)" stroke-width="2"/>`;
  for (let gy = ((gy0 % step) + step) % step; gy < Ha; gy += step) s += `<line x1="0" y1="${f1(gy)}" x2="${W}" y2="${f1(gy)}" stroke="var(--line)" stroke-width="2"/>`;

  // ---- obstruction
  if (obs) {
    const lab = obs.label || '', kind = obsKind(lab);
    let bx;   // its box in px, for the label
    if (obs.path) {
      const d = landD(obs.path, P), st = OBSTYLE[kind];
      under += `<path d="${d}" fill="${st[0]}" stroke="${st[1]}" stroke-width="${st[2]}" stroke-linejoin="round" ${st[3] ? `stroke-dasharray="${st[3]}"` : ''} fill-rule="evenodd"/>`;
      for (const sub of pathPts(obs.path)) for (const q of sub) addPt(...P(...q), 6, 0.3);
    } else {
      const [a, b] = [P(obs.x, obs.y), P(obs.x + obs.w, obs.y + obs.h)], st = OBSTYLE[kind];
      const rx = kind === 'vessel' ? Math.min(b[0] - a[0], b[1] - a[1]) / 2 : Math.min(S(8), (b[1] - a[1]) / 2, (b[0] - a[0]) / 2);
      under += `<rect x="${f1(a[0])}" y="${f1(a[1])}" width="${f1(b[0] - a[0])}" height="${f1(b[1] - a[1])}" rx="${f1(rx)}" fill="${st[0]}" stroke="${st[1]}" stroke-width="${st[2]}" ${st[3] ? `stroke-dasharray="${st[3]}"` : ''}/>`;
      bx = [a[0], a[1], b[0], b[1]]; addOb(...bx, 0.4);
    }
    if (lab) obs._lab = { lab, bx, at: P(obs.lx ?? (obs.path ? 160 : obs.x + obs.w / 2), obs.ly ?? (obs.path ? 20 : obs.y + obs.h / 2)) };
  }
  // ---- the zone
  const zoneOn = f.mark && (f.mark.zone || (plan && spec.zone));
  if (zoneOn) {
    const m = f.mark, r = S(plan && typeof spec.zone === 'number' ? spec.zone : m.zone === true || (plan && spec.zone) ? 3 * len : m.zone), [cx, cy] = P(m.x, m.y), bold = plan && spec.zone;
    under += `<circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r)}" fill="var(--accent)" fill-opacity="${bold ? .1 : .06}"/><circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r)}" fill="none" stroke="var(--accent)" stroke-width="${bold ? 6 : 3.5}" ${bold ? '' : 'stroke-dasharray="14 10"'}/>`;
    f.mark._zone = { cx, cy, r, bold };
  }
  // ---- the track
  if (f.track) { mid += `<path d="${pathD(f.track, P)}" fill="none" stroke="var(--muted)" stroke-width="5" stroke-dasharray="14 10" stroke-linecap="round" stroke-linejoin="round"/>`;
    for (const sub of pathPts(f.track)) for (let i = 1; i < sub.length; i++) addSeg(P(...sub[i - 1]), P(...sub[i]), 6, 0.5); }
  // ---- the line: pin to committee boat
  let lineLabs = [];
  if (f.line) {
    const l = f.line, a = P(l.x1, l.y1), b = P(l.x2, l.y2);
    mid += `<line x1="${f1(a[0])}" y1="${f1(a[1])}" x2="${f1(b[0])}" y2="${f1(b[1])}" stroke="var(--ink)" stroke-width="4" stroke-dasharray="12 10"/>`;
    addSeg(a, b, 5, 0.6);
    mid += `<circle cx="${f1(a[0])}" cy="${f1(a[1])}" r="15" fill="${MARKY}" stroke="var(--ink)" stroke-width="3"/>`; addPt(a[0], a[1], 16, 3);
    const rcs = sc * 0.9 * k, rch = l.hdg ?? wind;
    mid += `<g transform="translate(${f1(b[0])} ${f1(b[1])}) rotate(${rch}) scale(${f1(rcs)})"><path d="${HULL}" fill="#c3cad0" stroke="var(--ink)" stroke-width="3" vector-effect="non-scaling-stroke" stroke-linejoin="round"/><rect x="-4" y="-6" width="8" height="12" rx="2" fill="#fff" fill-opacity=".7"/></g>`;
    hullObs(b, rch, rcs, addPt);
    lineLabs.push({ t: 'pin', at: a, r: 16 }, { t: 'RC', at: b, r: 22 * rcs * 0.8 });
    if (l.label) lineLabs.push({ t: l.label, at: [(a[0] + b[0]) / 2, Math.min(a[1], b[1])], line: true });
  }
  // ---- the mark
  let markR = 0;
  if (f.mark) { const [mx, my] = P(f.mark.x, f.mark.y); markR = Math.max(15, Math.min(24, S(7)));
    mid += `<circle cx="${f1(mx)}" cy="${f1(my)}" r="${f1(markR)}" fill="${MARKY}" stroke="var(--ink)" stroke-width="3.5"/>`; addPt(mx, my, markR + 2, 4); }

  // ---- boats, their headings, the plan's rings
  const roleOf = {};
  if (plan) {
    for (const [list, kind, def] of [[spec.keep, 'red', 'keeps clear'], [spec.right, 'accent', 'right of way']])
      for (const it of list || []) { const [n, t] = Array.isArray(it) ? it : [it, def]; if (byName[n]) roleOf[n] = { kind, t }; }
  }
  const drawBoat = (b, o = {}) => {
    const [x, y] = P(b.x, b.y), s0 = b.bs * k, [hull, ink] = b.col, side = boomSide(b.hdg, wind), ang = boomAngle(b.hdg, wind);
    // the heading: a dashed arrow from the bow, as long as figures.js draws it (1.4 lengths from the centre)
    const bow = pol(x, y, 22 * s0 + 4, b.hdg), tip = pol(x, y, Math.max(S(1.4 * len), 22 * s0 + 46), b.hdg);
    const hd = arrowSvg(bow[0], bow[1], tip[0], tip[1], { c: o.ghost ? 'var(--faint)' : 'var(--muted)', w: 4, dash: '10 8', h: 18 }); let g = '';
    addSeg(bow, tip, 6, 0.6);
    const role = roleOf[b.label] && !o.ghost ? roleOf[b.label] : null;
    let body = '';
    if (role) body += `<path d="${HULL}" fill="none" stroke="${role.kind === 'red' ? COLS.red : 'var(--accent)'}" stroke-width="16" stroke-opacity=".9" vector-effect="non-scaling-stroke" stroke-linejoin="round"/><path d="${HULL}" fill="none" stroke="var(--bg)" stroke-width="6" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>`;
    const deck = hull === '#ffffff' || hull === '#f2c200' ? '#000' : '#fff';
    body += `<path d="${HULL}" fill="${hull}" stroke="var(--ink)" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>`;
    body += `<rect x="-3.6" y="-4" width="7.2" height="9" rx="2" fill="${deck}" fill-opacity=".16"/><rect x="-3.4" y="7.5" width="6.8" height="8" rx="1.2" fill="#000" fill-opacity=".25"/>`;
    // the mainsail: boom from the mast (0,-7) aft and to leeward, the sail bellied to leeward
    const L = 21, mx = 0, my = -7, ex = side * L * Math.sin(ang * RAD), ey = my + L * Math.cos(ang * RAD);
    if (ang === 0) { // head to wind: the boom on the centreline, the sail flapping
      body += `<path d="M0 -7 q 2 3 0 5 q -2 3 0 5 q 2 3 0 5 q -2 3 0 6" fill="none" stroke="#fff" stroke-width="5" vector-effect="non-scaling-stroke" stroke-linecap="round"/><path d="M0 -7 q 2 3 0 5 q -2 3 0 5 q 2 3 0 5 q -2 3 0 6" fill="none" stroke="var(--ink)" stroke-width="2" vector-effect="non-scaling-stroke"/>`;
    } else {
      const nx = side * Math.cos(ang * RAD), ny = -Math.sin(ang * RAD), cxp = (mx + ex) / 2 + nx * 5.5, cyp = (my + ey) / 2 + ny * 5.5;
      body += `<path d="M${mx} ${my} Q ${f1(cxp)} ${f1(cyp)} ${f1(ex)} ${f1(ey)} Z" fill="#fff" fill-opacity=".92" stroke="var(--ink)" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>`;
      body += `<line x1="${mx}" y1="${my}" x2="${f1(ex)}" y2="${f1(ey)}" stroke="var(--ink)" stroke-width="5" vector-effect="non-scaling-stroke" stroke-linecap="round"/>`;
    }
    body += `<circle cx="0" cy="-7" r="1.8" fill="var(--ink)"/>`;
    if (b.you) body += `<circle cx="0" cy="-14" r="3" fill="#fff" stroke="var(--ink)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`;
    g += `<g transform="translate(${f1(x)} ${f1(y)}) rotate(${b.hdg}) scale(${f1(s0)})" ${o.ghost ? 'opacity=".42"' : ''}>${body}</g>`;
    hullObs([x, y], b.hdg, s0, addPt);
    // the boom end, in px, for the obstacles
    const be = [x + (ex * Math.cos(b.hdg * RAD) - ey * Math.sin(b.hdg * RAD)) * s0, y + (ex * Math.sin(b.hdg * RAD) + ey * Math.cos(b.hdg * RAD)) * s0];
    addSeg([x, y], be, 7, 2);
    return { g, hd, x, y, s0, be };
  };
  const drawn = boats.map(b => ({ b, ...drawBoat(b) }));
  const BOATPX = drawn.map(d => (d.px = [d.x, d.y]));
  const ghosts = plan ? (spec.ghosts || []).filter(g => byName[g.of]).map(g => ({ gs: g, ...drawBoat({ ...byName[g.of], x: g.x, y: g.y, hdg: g.hdg ?? byName[g.of].hdg }, { ghost: true }) })) : [];
  for (const d of ghosts) mid = d.hd + d.g + mid;   // under the boats
  // ---- the plan's lines, rings, tracks, arrows, the line abeam
  let over = '';
  if (plan) {
    for (const a of spec.lines || []) { const [p, q] = [P(a[0], a[1]), P(a[2], a[3])]; over += `<line x1="${f1(p[0])}" y1="${f1(p[1])}" x2="${f1(q[0])}" y2="${f1(q[1])}" stroke="${COLS[a[4]] || COLS.ink}" stroke-width="5" stroke-linecap="round" ${a[5] ? 'stroke-dasharray="14 10"' : ''}/>`; addSeg(p, q, 5, 0.6); }
    for (const r of spec.rings || []) { const [p, rr] = [P(r[0], r[1]), S(r[2])]; over += `<circle cx="${f1(p[0])}" cy="${f1(p[1])}" r="${f1(rr)}" fill="none" stroke="${COLS[r[3]] || COLS.red}" stroke-width="5" stroke-dasharray="14 10"/>`; }
    for (const t of spec.tracks || []) { const c = COLS[t[1]] || COLS.accent; over += `<path d="${pathD(t[0], P)}" fill="none" stroke="${c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>`;
      const subs = pathPts(t[0]); for (const sub of subs) for (let i = 1; i < sub.length; i++) addSeg(P(...sub[i - 1]), P(...sub[i]), 6, 0.6);
      const last = subs[subs.length - 1], [a, b] = [P(...last[last.length - 2]), P(...last[last.length - 1])], Lab = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, tt = Math.min(1, 24 / Lab);
      over += arrowSvg(b[0] - (b[0] - a[0]) * tt, b[1] - (b[1] - a[1]) * tt, b[0], b[1], { c, w: 6, h: 24 }); }
    for (const a of spec.arrows || []) { const [p, q] = [P(a[0], a[1]), P(a[2], a[3])]; over += arrowSvg(p[0], p[1], q[0], q[1], { c: COLS[a[4]] || COLS.red, w: 7, h: 26, dash: a[5] ? '14 10' : '' }); addSeg(p, q, 6, 0.8); }
    for (const n of spec.abeam || []) { const b = byName[n]; if (!b) continue;
      const st = pol(b.x, b.y, 18 * b.bs, b.hdg + 180), Lx = len * 1.6, a = pol(...st, Lx, b.hdg + 90), c = pol(...st, Lx, b.hdg - 90), [p, q] = [P(...a), P(...c)];
      over += `<line x1="${f1(p[0])}" y1="${f1(p[1])}" x2="${f1(q[0])}" y2="${f1(q[1])}" stroke="${COLS.red}" stroke-width="5" stroke-dasharray="14 9" stroke-linecap="round"/>`;
      addSeg(p, q, 5, 0.6); b._abeam = [p, q]; }
  }

  // ---- the wind, in its corner
  { const [wx, wy] = windAt, [ax, ay] = pol(wx, wy + 52, 46, wind), [bx, by] = pol(wx, wy + 52, 46, wind + 180);
    top += arrowSvg(ax, ay, bx, by, { c: COLS.red, w: 10, h: 28 }) + pill(wx, wy + 140, 'Wind', 'red', 30);
    addOb(wx - 90, wy - 6, wx + 90, wy + 170, 5); }

  // ---- labels: the boats first, then the mark, the line, the obstruction, the zone, the plan's pills
  const blockOf = (b) => {
    const rows = [[b.you ? 'You' : b.label, 'boat']];
    if (plan) {
      if (roleOf[b.label]) rows.push([roleOf[b.label].t, roleOf[b.label].kind]);
      const tk = spec.tack === true || (Array.isArray(spec.tack) && spec.tack.includes(b.label));
      if (tk) rows.push([`${tackOf(b.hdg, wind)} tack`, 'light']);
      for (const t of spec.tags || []) if (t[0] === b.label) rows.push([t[1], t[2] || 'light']);
    }
    return rows;
  };
  const SZ = 30, GAPR = 6;
  for (const d of drawn) {
    const rows = blockOf(d.b).map(([t, kind], i) => ({ t, kind, size: i ? 26 : SZ }));
    const dims = rows.map(r => pillWH(r.t, r.size)), w = Math.max(...dims.map(q => q[0])), h = dims.reduce((a, q) => a + q[1], 0) + GAPR * (rows.length - 1);
    const ext = 22 * d.s0 * 0.75;
    const [cx, cy] = place(around(d.x, d.y, ext, ext, w, h, 10), w, h, d.x, d.y + ext + h / 2, 3, d.px);
    let yy = cy - h / 2;
    rows.forEach((r, i) => { const hh = dims[i][1];
      labels += i === 0 ? pill(cx, yy + hh / 2, r.t, '', r.size, [d.b.col[0], d.b.col[1], d.b.col[0] === '#ffffff' ? 'var(--ink)' : d.b.col[0]]) : pill(cx, yy + hh / 2, r.t, r.kind, r.size);
      yy += hh + GAPR; });
  }
  for (const d of ghosts) if (d.gs.text) { const [w, h] = pillWH(d.gs.text, 26), ext = 22 * d.s0 * 0.75; const [cx, cy] = place(around(d.x, d.y, ext, ext, w, h, 10), w, h, d.x, d.y + ext + h / 2); labels += pill(cx, cy, d.gs.text, 'light', 26); }
  if (f.mark && f.mark.label) {
    const m = f.mark, [mx, my] = P(m.x, m.y), w = tw(m.label, 30) + 10, h = 36;
    const prefer = m.labelY != null && m.labelY < 0 ? 'above' : 'below';
    const [cx, cy] = place(around(mx, my, markR, markR, w, h, 8, prefer), w, h, mx, my + markR + 26, 3);
    labels += txt(cx, cy + 11, m.label, { s: 30 });
  }
  for (const L of lineLabs) {
    const sz = L.line ? 30 : 26, w = tw(L.t, sz) + 10, h = sz * 1.15;
    const c = L.line ? [[L.at[0], L.at[1] - 34, 0], [L.at[0], L.at[1] + 34, 0.5], [L.at[0] - 120, L.at[1] - 34, 0.8], [L.at[0] + 120, L.at[1] - 34, 0.8], [L.at[0], L.at[1] - 80, 1]] : around(L.at[0], L.at[1], L.r, L.r, w, h, 6);
    const [cx, cy] = place(c, w, h, L.at[0], L.at[1] + (L.line ? -34 : L.r + 20), 3);
    labels += txt(cx, cy + sz * 0.35, L.t, { s: sz, f: L.line ? 'var(--ink)' : 'var(--muted)' });
  }
  if (obs && obs._lab) {
    const { lab, bx, at } = obs._lab, w = tw(lab, 28) + 12, h = 34;
    const inside = bx && (bx[2] - bx[0]) > w + 6 && (bx[3] - bx[1]) > h - 4;
    if (inside) { labels += txt((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2 + 10, lab, { s: 28, halo: false, f: obsKind(lab) === 'vessel' ? '#fff' : 'var(--ink)' }); }
    else { const c = bx ? around((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2, (bx[2] - bx[0]) / 2, (bx[3] - bx[1]) / 2, w, h, 8) : [[at[0], at[1], 0], ...around(at[0], at[1], 10, 10, w, h, 4)];
      const [cx, cy] = place(c, w, h, at[0], at[1], 2); labels += txt(cx, cy + 10, lab, { s: 28 }); }
  }
  if (f.mark && f.mark._zone) {
    const { cx, cy, r, bold } = f.mark._zone, t = bold ? 'zone · 3 hull lengths' : 'zone';
    if (bold) { const [w, h] = pillWH(t, 26); const c = [-30, 30, -60, 60, 0, -90, 90, 180, -150, 150].map((a, i) => { const [px, py] = pol(cx, cy, r, a); return [px, py, i * 0.3]; });
      const [px, py] = place(c, w, h, ...pol(cx, cy, r, -30), 3); labels += pill(px, py, t, 'accent', 26); }
    else { const w = tw(t, 28) + 8, h = 32; const c = [[cx, cy - r + 30, 0], [cx, cy + r - 26, 0.3], [cx - r + w / 2 + 14, cy, 0.6], [cx + r - w / 2 - 14, cy, 0.6], [cx, cy - r - 24, 1]];
      const [px, py] = place(c, w, h, cx, cy - r + 30, 2); labels += txt(px, py + 10, t, { s: 28, f: 'var(--accent)' }); }
  }
  if (plan) {
    for (const n of spec.abeam || []) { const b = byName[n]; if (!b || !b._abeam) continue; const [p, q] = b._abeam, [w, h] = pillWH('line abeam', 26);
      const [cx, cy] = place([[q[0], q[1], 0], [p[0], p[1], 0.2], [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2 - 40, 0.5]], w, h, q[0], q[1], 3); labels += pill(cx, cy, 'line abeam', 'red', 26); }
    for (const p of spec.pills || spec.marks || []) { const [x, y] = P(p[0], p[1]), [w, h] = pillWH(p[2], 28);
      const c = [[x, y, 0], ...around(x, y, 6, 6, w, h, 4)]; const [cx, cy] = place(c, w, h, x, y, 3); labels += pill(cx, cy, p[2], p[3] || 'light', 28); }
  }

  s += under + mid + drawn.map(d => d.hd).join('') + drawn.map(d => d.g).join('') + over + labels + top + `</g>`;
  // ---- the key band
  if (band.h) {
    s += `<rect x="0" y="${Ha}" width="${W}" height="${band.h}" fill="var(--band)"/>`;
    let y = Ha + 54;
    for (const l of band.lines) { y += l.dy; if (l.bullet) s += `<text x="34" y="${y}" font-size="32" fill="var(--ink)">·</text>`; s += txt(l.x, y, l.t, { s: l.s, w: l.w, a: 'start', halo: false }); }
  }
  return s + '</svg>';
}

/* ───────────────── helpers ───────────────── */
function arrowSvg(x1, y1, x2, y2, o = {}) {
  const c = o.c || 'var(--muted)', w = o.w || 4, a = Math.atan2(y2 - y1, x2 - x1), h = o.h || Math.max(16, w * 3.2);
  const p1 = [x2 - h * Math.cos(a - .45), y2 - h * Math.sin(a - .45)], p2 = [x2 - h * Math.cos(a + .45), y2 - h * Math.sin(a + .45)];
  const ex = x2 - h * 0.6 * Math.cos(a), ey = y2 - h * 0.6 * Math.sin(a);
  return `<line x1="${f1(x1)}" y1="${f1(y1)}" x2="${f1(ex)}" y2="${f1(ey)}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/><path d="M${f1(x2)} ${f1(y2)} L${f1(p1[0])} ${f1(p1[1])} L${f1(p2[0])} ${f1(p2[1])} Z" fill="${c}"/>`;
}
// the hull as a row of small boxes along its centreline, for the placer
function hullObs([x, y], hdg, s0, addPt) { for (const t of [-18, -9, 0, 9, 16]) { const [px, py] = pol(x, y, -t * s0, hdg); addPt(px, py, 6.5 * s0, 4); } }
// SVG paths of figures.js (absolute M L H V C Q Z): the points of each subpath, and the path mapped to px
function pathTok(d) { return d.match(/[MLHVCQZ]|-?\d*\.?\d+/gi) || []; }
function pathPts(d) {
  const t = pathTok(d), subs = []; let i = 0, cmd = '', cur = [0, 0], sub = null;
  while (i < t.length) {
    if (/[A-Za-z]/.test(t[i])) cmd = t[i++].toUpperCase();
    if (cmd === 'Z') { cmd = ''; continue; }
    if (cmd === 'M') { cur = [+t[i++], +t[i++]]; sub = [cur]; subs.push(sub); cmd = 'L'; continue; }
    if (cmd === 'L') { cur = [+t[i++], +t[i++]]; sub.push(cur); continue; }
    if (cmd === 'H') { cur = [+t[i++], cur[1]]; sub.push(cur); continue; }
    if (cmd === 'V') { cur = [cur[0], +t[i++]]; sub.push(cur); continue; }
    if (cmd === 'C') { const p = [[+t[i++], +t[i++]], [+t[i++], +t[i++]], [+t[i++], +t[i++]]]; for (const q of bez(cur, p, 6)) sub.push(q); cur = p[2]; continue; }
    if (cmd === 'Q') { const p = [[+t[i++], +t[i++]], [+t[i++], +t[i++]]]; for (const q of bez(cur, p, 6)) sub.push(q); cur = p[1]; continue; }
    i++;
  }
  return subs;
}
function bez(p0, p, n) {
  const out = [];
  for (let j = 1; j <= n; j++) { const u = j / n;
    if (p.length === 3) { const a = (1 - u) ** 3, b = 3 * (1 - u) ** 2 * u, c = 3 * (1 - u) * u * u, d = u ** 3; out.push([a * p0[0] + b * p[0][0] + c * p[1][0] + d * p[2][0], a * p0[1] + b * p[0][1] + c * p[1][1] + d * p[2][1]]); }
    else { const a = (1 - u) ** 2, b = 2 * (1 - u) * u, c = u * u; out.push([a * p0[0] + b * p[0][0] + c * p[1][0], a * p0[1] + b * p[0][1] + c * p[1][1]]); } }
  return out;
}
// land touching the 320×200 frame runs on past it, its coastline straight on, to the edge of whatever view is drawn:
// a vertex on the frame's edge moves out along the coast edge that ends there; corners move out diagonally
const side = ([x, y]) => [x <= 0 ? 'l' : '', x >= 320 ? 'r' : '', y <= 0 ? 't' : '', y >= 200 ? 'b' : ''].join('');
const alongBorder = (a, b) => [...side(a)].some(c => side(b).includes(c));
function extendPoly(pts) {
  const n = pts.length;
  return pts.map((v, i) => {
    if (!side(v)) return v;
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n], ca = !alongBorder(v, a), cb = !alongBorder(v, b);
    const out = (o) => { const dx = v[0] - o[0], dy = v[1] - o[1], L = Math.hypot(dx, dy) || 1; return [v[0] + dx / L * 2500, v[1] + dy / L * 2500]; };
    if (ca && !cb) return out(a);
    if (cb && !ca) return out(b);
    return out([160, 100]);
  });
}
function landD(d, P) {
  if (/[CQ]/i.test(d)) return pathD(d, P);
  return pathPts(d).map(sub => { let q = sub; if (q.length > 2 && q[0][0] === q[q.length - 1][0] && q[0][1] === q[q.length - 1][1]) q = q.slice(0, -1);
    return 'M' + extendPoly(q).map(p => P(...p).map(f1).join(' ')).join(' L') + ' Z'; }).join(' ');
}
function pathD(d, P, ext) {
  const t = pathTok(d); let i = 0, cmd = '', out = '', cur = [0, 0];
  const pt = (x, y) => { cur = [x, y]; return P(x, y).map(f1).join(' '); };
  while (i < t.length) {
    if (/[A-Za-z]/.test(t[i])) { cmd = t[i++].toUpperCase(); if (cmd === 'Z') { out += 'Z '; continue; } }
    if (cmd === 'M' || cmd === 'L') { out += `${cmd}${pt(+t[i++], +t[i++])} `; if (cmd === 'M') cmd = 'L'; continue; }
    if (cmd === 'H') { out += `L${pt(+t[i++], cur[1])} `; continue; }
    if (cmd === 'V') { out += `L${pt(cur[0], +t[i++])} `; continue; }
    if (cmd === 'C') { out += `C${pt(+t[i++], +t[i++])} ${pt(+t[i++], +t[i++])} ${pt(+t[i++], +t[i++])} `; continue; }
    if (cmd === 'Q') { out += `Q${pt(+t[i++], +t[i++])} ${pt(+t[i++], +t[i++])} `; continue; }
    i++;
  }
  return out.trim();
}
// obstruction kinds by their label: land, shallows, a no-go area, a line, or a vessel / floating object
function obsKind(l) {
  if (/swim/i.test(l)) return 'area';
  if (/shoal|sandbank|awash/i.test(l)) return 'shallow';
  if (/anchor line/i.test(l)) return 'rope';
  if (/shore|beach|breakwater|wall|headland|island|jetty|pier|quay|rock|point|bridge|post/i.test(l)) return 'land';
  return 'vessel';
}
const OBSTYLE = { land: [LAND, COAST, 4], shallow: [SAND, COAST, 3, '10 8'], area: ['rgba(224,37,27,.08)', COLS.red, 4, '14 10'], rope: ['var(--ink)', 'var(--ink)', 2], vessel: ['#8e979f', 'var(--ink)', 3] };

/* ───────────────── plan specs: check ───────────────── */
const SPECKEYS = new Set(['title', 'key', 'keep', 'right', 'tags', 'tack', 'abeam', 'zone', 'arrows', 'lines', 'rings', 'tracks', 'ghosts', 'pills', 'marks', 'ru']);
const KINDS = new Set(['light', 'red', 'accent', 'ink', 'green']);
function checkSpec(e, sp) {
  const errs = [], names = new Set((e.figure.boats || []).map(b => b.label)), num = v => typeof v === 'number' && isFinite(v);
  const nm = (n, where) => { if (!names.has(n)) errs.push(`${where}: no boat "${n}" (boats: ${[...names].join(', ')})`); };
  for (const k of Object.keys(sp)) if (!SPECKEYS.has(k) && !k.startsWith('_')) errs.push(`unknown key "${k}"`);
  if (!sp.title) errs.push('no title');
  if (sp.key && !Array.isArray(sp.key)) errs.push('key must be a list of strings');
  for (const [lk, it] of [['keep', sp.keep], ['right', sp.right]]) for (const x of it || []) nm(Array.isArray(x) ? x[0] : x, lk);
  for (const t of sp.tags || []) { nm(t[0], 'tags'); if (t[2] && !KINDS.has(t[2])) errs.push(`tags: kind "${t[2]}"`); }
  if (Array.isArray(sp.tack)) sp.tack.forEach(n => nm(n, 'tack'));
  for (const n of sp.abeam || []) nm(n, 'abeam');
  if (sp.zone && !e.figure.mark) errs.push('zone: the figure has no mark');
  for (const [lk, it, n] of [['arrows', sp.arrows, 4], ['lines', sp.lines, 4], ['rings', sp.rings, 3], ['pills', sp.pills || sp.marks, 2]])
    for (const a of it || []) { if (!Array.isArray(a) || !a.slice(0, n).every(num)) errs.push(`${lk}: bad coordinates ${JSON.stringify(a)}`);
      const c = lk === 'pills' ? a[3] : a[n]; if (c && !(lk === 'pills' ? KINDS.has(c) : COLS[c])) errs.push(`${lk}: colour "${c}"`); }
  for (const g of sp.ghosts || []) { nm(g.of, 'ghosts'); if (!num(g.x) || !num(g.y)) errs.push(`ghosts: bad coordinates`); }
  for (const t of sp.tracks || []) if (typeof t[0] !== 'string' || !pathPts(t[0]).length) errs.push(`tracks: bad path`);
  return errs;
}

/* ───────────────── run ───────────────── */
const list = JSON.parse(readFileSync(join(DIR, 'race.json'), 'utf8'));
let CUR = '';
const report = { q: 0, plan: 0, missing: [], errors: [] };
for (const e of list) {
  if (ONLY.length && !ONLY.includes(e.id) && !ONLY.includes(e.topic)) continue;
  CUR = e.id; USED = new Set(); FRAG = {};
  const dir = join(DIR, e.id), sp = join(dir, 'plan.spec.json');
  let spec = null;
  if (existsSync(sp)) {
    try { spec = JSON.parse(readFileSync(sp, 'utf8')); } catch (err) { report.errors.push(`${e.id}: plan.spec.json is not JSON: ${err.message}`); }
    if (spec) { const errs = checkSpec(e, spec); if (errs.length) report.errors.push(...errs.map(x => `${e.id}: ${x}`)); }
  }
  RUMAP = { ...BUILTIN, ...(spec?.ru || {}), ...(e.ru || {}) };
  let q, plan = null, specOk = !!spec;
  if (spec) { const errs = checkSpec(e, spec); specOk = !errs.length;
    // every string the spec adds needs Russian, whether or not the plan could be drawn
    const strs = [spec.title, ...(spec.key || []), ...(spec.tags || []).map(t => t[1]), ...(spec.pills || spec.marks || []).map(p => p[2]),
      ...(spec.ghosts || []).map(g => g.text), ...[...(spec.keep || []), ...(spec.right || [])].filter(Array.isArray).map(x => x[1])];
    for (const t of strs) if (typeof t === 'string' && !isCode(t) && RUMAP[t] === undefined) report.missing.push(`${e.id}: ${t} (plan.spec.json ru)`); }
  try { q = render(e, null); }
  catch (err) { report.errors.push(`${e.id}: question image failed: ${err.stack.split('\n').slice(0, 2).join(' ')}`); continue; }
  const qUsed = USED;
  if (specOk) {
    try { plan = render(e, spec); }
    catch (err) { report.errors.push(`${e.id}: plan failed: ${err.stack.split('\n').slice(0, 2).join(' ')}`); plan = null; }
  } else if (spec) report.errors.push(`${e.id}: plan not drawn until the errors above are fixed`);
  if (!plan) USED = qUsed;
  const ru = {};
  for (const s of [...USED].sort()) { const r = ruOf(s); ru[s] = r; if (r === s && !/^(A|B|C|RC|Finn|29er|\d+)$/.test(s) && !(e.ru && e.ru[s] === s) && !report.missing.some(m => m.startsWith(`${e.id}: ${s} (`))) report.missing.push(`${e.id}: ${s}`); }
  if (CHECK) continue;
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'q.json'), JSON.stringify({ svg: q }) + '\n'); report.q++;
  const pp = join(dir, 'plan.json');
  if (plan) { writeFileSync(pp, JSON.stringify({ svg: plan }) + '\n'); report.plan++; } else if (existsSync(pp)) rmSync(pp);
  writeFileSync(join(dir, 'ru.json'), JSON.stringify(ru, null, 1) + '\n');
}
console.log(CHECK ? 'checked' : `q.json ${report.q}, plan.json ${report.plan}`);
if (WARN.length) console.log('warnings:\n  ' + WARN.join('\n  '));
if (report.errors.length) console.log('spec errors:\n  ' + report.errors.join('\n  '));
if (report.missing.length) console.log('no Russian for:\n  ' + report.missing.join('\n  '));
