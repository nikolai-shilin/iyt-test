// Bareboat Skipper test images for the 2D figure types `chart` and `isobars`, in the plan-view schematic style of
// figure-schematic.js (flat, theme tokens, Carlito, pills, a faint grid, the N arrow, the key band along the bottom).
// For each id in figure-style/questions/bareboat-skipper/{chart,isobars}.json it writes <id>/q.json (the image for the
// question: the figure's own facts and nothing more), <id>/plan.json where a worked drawing helps the answer, and
// <id>/ru.json (every text node of both, in Russian). Everything is drawn here as {svg}: the 320×200 chart frame of
// figures.js mapped uniformly into a 1280×800 frame, type sized for a phone (shown about 240 px high).
// The primitives (boat, arrow, pill, compass, cardinal marks, anchor, rock) are copied from figure-schematic.js.
//   node docs/design/blender/q_chart.mjs [id] [--level charter-checkin]   then capture_questions.mjs <level> --type chart|isobars [--ru]
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
// --level <level> (default bareboat-skipper): read questions/<level>/{chart,isobars}.json, write questions/<level>/<id>/
const ARGS = process.argv.slice(2), LI = ARGS.indexOf('--level');
const LEVEL = LI >= 0 ? ARGS[LI + 1] : 'bareboat-skipper';
const DIR = join(HERE, '..', 'figure-style', 'questions', LEVEL);
const W = 1280, H = 800;
const SCOL = { r: '#e0251b', g: '#1aa34a', w: '#ffffff', y: '#ffa800', k: 'var(--ink)', wind: '#e8231a', course: '#e0b400' };
const LIGHT = '#d4148c';          // the chart's magenta: light flares, traffic separation, charted areas
const LAND = '#d8c9a3', COAST = '#6b5a3a';
const RAD = Math.PI / 180;
const pol = (x, y, r, deg) => [x + r * Math.sin(deg * RAD), y - r * Math.cos(deg * RAD)];
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const f1 = v => (+v).toFixed(1);

/* ---------------- text: every text node is recorded, so ru.json can cover it ---------------- */
let USED = new Set(), RUMAP = {}, CLIP = 'area', NCLIP = 0;
const ruOf = s => RUMAP[s] ?? RU[s] ?? (/^[\d\s.+−=()′°]+$/.test(s) ? s.replace(/(\d)\.(\d)/g, '$1,$2') : s);
const CW = c => ' '.includes(c) ? .23 : '.,:;\'|il′·()[]'.includes(c) ? .26 : 'ftrI'.includes(c) ? .34 : 'mwMWшщжмШЩЖЮюы'.includes(c) ? .78
  : /[0-9]/.test(c) ? .507 : '°'.includes(c) ? .36 : '←→'.includes(c) ? .95 : /[A-ZА-Я]/.test(c) ? .6 : .5;
const tw0 = (s, size) => [...String(s)].reduce((a, c) => a + CW(c), 0) * size;
const tw = (s, size) => Math.max(tw0(s, size), tw0(ruOf(s), size));      // room for the Russian too
function txt(x, y, s, o = {}) {
  s = String(s); if (/[A-Za-zА-Яа-я]|\d\.\d/.test(s)) USED.add(s);
  const halo = o.halo === false ? '' : `stroke="var(--bg)" stroke-width="${o.haloW || 9}" stroke-linejoin="round" paint-order="stroke"`;
  return `<text x="${f1(x)}" y="${f1(y)}" font-size="${o.s || 34}" font-weight="${o.w || 700}" fill="${o.f || 'var(--ink)'}" text-anchor="${o.a || 'middle'}" ${halo}>${esc(s)}</text>`;
}
function pill(x, y, text, kind = 'light', size = 30) {
  const w = tw(text, size) + size * 1.3, h = size * 1.7;
  const fill = kind === 'accent' ? 'var(--accent)' : kind === 'red' ? SCOL.wind : kind === 'ink' ? 'var(--ink)' : 'var(--bg)';
  const ink = kind === 'light' ? 'var(--ink)' : kind === 'ink' ? 'var(--bg)' : '#fff', stroke = kind === 'light' ? 'var(--tag-line)' : fill;
  return `<rect x="${f1(x - w / 2)}" y="${f1(y - h / 2)}" width="${f1(w)}" height="${f1(h)}" rx="${f1(h / 2)}" fill="${fill}" stroke="${stroke}" stroke-width="3"/>` + txt(x, y + size * 0.36, text, { f: ink, s: size, halo: false });
}

/* ---------------- primitives, after figure-schematic.js ---------------- */
function arrow(x1, y1, x2, y2, o = {}) {
  const c = o.c || 'var(--muted)', w = o.w || 4, a = Math.atan2(y2 - y1, x2 - x1), h = o.h || Math.max(16, w * 3.2);
  const p1 = [x2 - h * Math.cos(a - .5), y2 - h * Math.sin(a - .5)], p2 = [x2 - h * Math.cos(a + .5), y2 - h * Math.sin(a + .5)];
  const ex = x2 - h * 0.6 * Math.cos(a), ey = y2 - h * 0.6 * Math.sin(a);
  return `<line x1="${f1(x1)}" y1="${f1(y1)}" x2="${f1(ex)}" y2="${f1(ey)}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/><path d="M${f1(x2)} ${f1(y2)} L${f1(p1[0])} ${f1(p1[1])} L${f1(p2[0])} ${f1(p2[1])} Z" fill="${c}"/>`;
}
function boat(x, y, hdg, o = {}) {
  const s = o.scale || 2.4, fill = o.fill || 'var(--ink)';
  const body = `<path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="${fill}" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round" ${o.ghost ? 'opacity=".45"' : ''}/>`;
  const dot = o.you ? `<circle cx="0" cy="-2" r="4" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.2"/>` : '';
  return `<g transform="translate(${f1(x)} ${f1(y)}) rotate(${hdg}) scale(${s})">${body}${dot}</g>`;
}
function compass(x, y) {
  return `<g><circle cx="${x}" cy="${y}" r="40" fill="var(--bg)" stroke="var(--tag-line)" stroke-width="3"/>${arrow(x, y + 24, x, y - 24, { c: 'var(--ink)', w: 4, h: 14 })}${txt(x, y - 50, 'N', { s: 28 })}</g>`;
}
function card(x, y, kind) {                       // IALA cardinal / special mark (figure-schematic.js sMark)
  const r = 26; let g = '';
  if (kind.startsWith('card')) {
    const bands = { 'card-n': ['k', 'y'], 'card-s': ['y', 'k'], 'card-e': ['k', 'y', 'k'], 'card-w': ['y', 'k', 'y'] }[kind], n = bands.length;
    bands.forEach((b, i) => { g += `<rect x="${x - r}" y="${f1(y - r + (2 * r) * i / n)}" width="${2 * r}" height="${f1((2 * r) / n + 0.5)}" fill="${SCOL[b]}"/>`; });
    g += `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="none" stroke="var(--ink)" stroke-width="3"/>`;
    const cone = (cy, up) => `<path d="M${x - 16} ${up ? cy + 14 : cy - 14} L${x} ${up ? cy - 14 : cy + 14} L${x + 16} ${up ? cy + 14 : cy - 14} Z" fill="var(--ink)"/>`;
    const tm = { 'card-n': [1, 1], 'card-s': [0, 0], 'card-e': [1, 0], 'card-w': [0, 1] }[kind];
    g += cone(y - r - 52, tm[0]) + cone(y - r - 20, tm[1]);
  } else {                                        // special: yellow, X topmark
    const ty = y - r - 22;
    g += `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="${SCOL.y}" stroke="var(--ink)" stroke-width="3"/>`;
    g += `<path d="M${x - 14} ${ty - 14} L${x + 14} ${ty + 14} M${x + 14} ${ty - 14} L${x - 14} ${ty + 14}" stroke="${SCOL.y}" stroke-width="9" stroke-linecap="round"/><path d="M${x - 14} ${ty - 14} L${x + 14} ${ty + 14} M${x + 14} ${ty - 14} L${x - 14} ${ty + 14}" stroke="var(--ink)" stroke-width="2" stroke-linecap="round" opacity=".5"/>`;
  }
  return `<g>${g}</g>`;
}
function anchorGlyph(x, y, s = 1) {
  return `<g transform="translate(${f1(x)} ${f1(y)}) scale(${s})" fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"><circle cx="0" cy="-30" r="8"/><line x1="0" y1="-22" x2="0" y2="28"/><line x1="-16" y1="-10" x2="16" y2="-10"/><path d="M-26 8 C -24 26 -12 32 0 32 C 12 32 24 26 26 8"/><path d="M-30 14 L-26 6 L-18 12 M30 14 L26 6 L18 12"/></g>`;
}
function rockSym(x, y) {
  return `<g><circle cx="${f1(x)}" cy="${f1(y)}" r="40" fill="var(--bg)" stroke="var(--ink)" stroke-width="3" stroke-dasharray="3 7"/><path d="M${f1(x - 20)} ${f1(y)} L${f1(x + 20)} ${f1(y)} M${f1(x)} ${f1(y - 20)} L${f1(x)} ${f1(y + 20)}" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/>${[[-12, -12], [12, -12], [-12, 12], [12, 12]].map(([a, b]) => `<circle cx="${f1(x + a)}" cy="${f1(y + b)}" r="4" fill="var(--ink)"/>`).join('')}</g>`;
}
/* chart symbols of our own, in the same weight: a landmark (position circle), a beacon, a light flare, a rock above water */
const landmark = (x, y) => `<circle cx="${f1(x)}" cy="${f1(y)}" r="13" fill="var(--bg)" stroke="var(--ink)" stroke-width="5"/><circle cx="${f1(x)}" cy="${f1(y)}" r="4.5" fill="var(--ink)"/>`;
const beacon = (x, y) => `<circle cx="${f1(x)}" cy="${f1(y)}" r="14" fill="#fff" stroke="var(--ink)" stroke-width="5"/>`;
const flare = (x, y, c = LIGHT, rot = 35) => `<path transform="translate(${f1(x)} ${f1(y)}) rotate(${rot})" d="M0 -6 C 9 -18 10 -40 0 -62 C -10 -40 -9 -18 0 -6 Z" fill="${c}" stroke="var(--bg)" stroke-width="2"/>`;
const islet = (x, y) => `<path transform="translate(${f1(x)} ${f1(y)}) scale(1.7)" d="M-20 4 C -22 -10 -8 -18 4 -16 C 18 -14 24 -2 18 8 C 12 18 -14 18 -20 4 Z" fill="${LAND}" stroke="${COAST}" stroke-width="4"/>`;
function spotRing(x, y, letter, r = 34) {
  return `<circle cx="${f1(x)}" cy="${f1(y)}" r="${r}" fill="rgba(255,230,0,.18)" stroke="${SCOL.course}" stroke-width="7"/>` + (letter ? txt(x, y + 13, letter, { s: 36, halo: false }) : '');
}

/* ---------------- SVG path strings of figures.js (absolute M L H V C Q Z) ---------------- */
function parsePath(d) {
  const tok = d.match(/[MLHVCQZ]|-?\d*\.?\d+/gi) || [], subs = []; let i = 0, cmd = '', cur = [0, 0], sub = null, start = [0, 0];
  const num = () => +tok[i++];
  while (i < tok.length) {
    if (/[A-Za-z]/.test(tok[i])) cmd = tok[i++];
    if (cmd === 'Z' || cmd === 'z') { if (sub) sub.push({ c: 'Z' }); cur = start; cmd = ''; continue; }
    if (cmd === 'M') { cur = [num(), num()]; start = cur; sub = [{ c: 'M', p: [cur] }]; subs.push(sub); cmd = 'L'; continue; }
    if (cmd === 'L') { cur = [num(), num()]; sub.push({ c: 'L', p: [cur] }); continue; }
    if (cmd === 'H') { cur = [num(), cur[1]]; sub.push({ c: 'L', p: [cur] }); continue; }
    if (cmd === 'V') { cur = [cur[0], num()]; sub.push({ c: 'L', p: [cur] }); continue; }
    if (cmd === 'C') { const p = [[num(), num()], [num(), num()], [num(), num()]]; cur = p[2]; sub.push({ c: 'C', p }); continue; }
    if (cmd === 'Q') { const p = [[num(), num()], [num(), num()]]; cur = p[1]; sub.push({ c: 'Q', p }); continue; }
    i++;
  }
  return subs;
}
// land touching the 320×200 frame runs on past it, into the side strips of the wider frame
const extend = ([x, y]) => [x <= 0 ? -200 : x >= 320 ? 520 : x, y <= 0 ? -200 : y >= 200 ? 400 : y];
const subD = (sub, P, ext) => sub.map(s => s.c === 'Z' ? 'Z' : s.c + s.p.map(q => P(...(ext ? extend(q) : q)).map(f1).join(' ')).join(' ')).join(' ');
const headAt = (a, b, c, w, h = 24) => { const L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, t = Math.min(1, 30 / L); return arrow(b[0] - (b[0] - a[0]) * t, b[1] - (b[1] - a[1]) * t, b[0], b[1], { c, w, h }); };
const pathEnd = sub => { const segs = sub.filter(s => s.c !== 'Z'), last = segs[segs.length - 1], prev = segs[segs.length - 2]; const b = last.p[last.p.length - 1], a = last.p.length > 1 ? last.p[last.p.length - 2] : prev.p[prev.p.length - 1]; return [a, b]; };

/* ---------------- the frame: drawing area over the key band ---------------- */
function frame({ title = '', key = [], view = [0, 0, 320, 200], draw, avoid = [], compassAt, cols, noCompass }) {
  CLIP = `qc-${CUR}-${++NCLIP}`;
  const rowsOf = n => cols === 1 ? n : Math.ceil(n / 2);
  const twoCol = cols !== 1 && key.length >= 2 && key.every(l => tw('· ' + l, 34) <= 590);
  const nRows = key.length ? (twoCol ? rowsOf(key.length) : key.length) : 0;
  const bandH = title || key.length ? 50 + 50 * nRows + 34 : 0, Ha = H - bandH;
  const [x0, y0, x1, y1] = view, k = Math.min(W / (x1 - x0), Ha / (y1 - y0));
  const ox = (W - (x1 - x0) * k) / 2 - x0 * k, oy = (Ha - (y1 - y0) * k) / 2 - y0 * k;
  const P = (x, y) => [ox + x * k, oy + y * k];
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">`;
  s += `<defs><clipPath id="${CLIP}"><rect x="0" y="0" width="${W}" height="${Ha}"/></clipPath></defs><rect width="${W}" height="${H}" fill="var(--bg)"/>`;
  s += `<g clip-path="url(#${CLIP})">`;
  const step = 30 * k; for (let gx = ox % step; gx < W; gx += step) s += `<line x1="${f1(gx)}" y1="0" x2="${f1(gx)}" y2="${Ha}" stroke="var(--line)" stroke-width="2"/>`;
  for (let gy = oy % step; gy < Ha; gy += step) s += `<line x1="0" y1="${f1(gy)}" x2="${W}" y2="${f1(gy)}" stroke="var(--line)" stroke-width="2"/>`;
  s += draw(P, k, Ha);
  // the N arrow in the emptiest corner
  const corners = [[70, 82], [W - 70, 82], [70, Ha - 70], [W - 70, Ha - 70]], pts = avoid.map(([x, y]) => P(x, y));
  const free = c => Math.min(1e9, ...pts.map(p => Math.hypot(p[0] - c[0], p[1] - c[1])));
  const c = compassAt ? corners[compassAt] : corners.find(c => free(c) > 130) || corners.reduce((a, b) => free(b) > free(a) ? b : a);
  if (!noCompass) s += compass(...c);
  s += `</g>`;
  if (bandH) {
    s += `<rect x="0" y="${Ha}" width="${W}" height="${bandH}" fill="var(--band)"/>` + txt(30, Ha + 52, title, { s: 40, a: 'start', halo: false });
    key.forEach((l, i) => { const r = twoCol ? Math.floor(i / 2) : i, cx = twoCol && i % 2 ? 660 : 30; s += txt(cx, Ha + 52 + 50 * (r + 1), '·', { s: 34, w: 400, a: 'start', halo: false }) + txt(cx + 18, Ha + 52 + 50 * (r + 1), l, { s: 34, w: 400, a: 'start', halo: false }); });
  }
  return s + '</svg>';
}

/* ---------------- chart: the figures.js spec, redrawn ---------------- */
const TRACK = { course: { c: SCOL.course, w: 6, dash: '16 11', arrow: true }, bearing: { c: 'var(--ink)', w: 4 }, plain: { c: 'var(--ink)', w: 4 },
  clearing: { c: SCOL.wind, w: 5, dash: '16 11' }, gps: { c: 'var(--accent)', w: 6 }, distance: { c: 'var(--ink)', w: 4, dash: '12 10' } };
const isLightName = n => /\b(Fl|Oc|Iso|Al)\b|\blt\b|^[A-C]  /.test(n);
const cardKind = n => ({ 'N cardinal': 'card-n', 'S cardinal': 'card-s', 'E cardinal': 'card-e', 'W cardinal': 'card-w' })[n];

function chartDraw(f, cfg, extra = {}) {
  return (P, k, Ha) => {
    let s = '';
    const subs = f.land ? parsePath(f.land) : [];
    subs.forEach((sub, i) => {
      if ((cfg.zones || []).includes(i)) s += `<path d="${subD(sub, P, true)}" fill="rgba(212,20,140,.13)" stroke="${LIGHT}" stroke-width="4" stroke-dasharray="14 10"/>`;
      else s += `<path d="${subD(sub, P, true)}" fill="${LAND}" stroke="${COAST}" stroke-width="5" stroke-linejoin="round"/>`;
    });
    if (cfg.area) { const [a, b] = [P(...cfg.area[0]), P(...cfg.area[1])]; s += `<rect x="${f1(a[0])}" y="${f1(a[1])}" width="${f1(b[0] - a[0])}" height="${f1(b[1] - a[1])}" fill="rgba(212,20,140,.07)" stroke="${LIGHT}" stroke-width="4" stroke-dasharray="14 10"/>`; }
    s += (extra.under || []).map(o => item(o, P, k)).join('');
    if (f.track && !cfg.noTrack) {
      const st = TRACK[cfg.track || 'course'];
      for (const sub of parsePath(f.track)) {
        s += `<path d="${subD(sub, P)}" fill="none" stroke="${st.c}" stroke-width="${st.w}" stroke-linecap="round" stroke-linejoin="round" ${st.dash ? `stroke-dasharray="${st.dash}"` : ''}/>`;
        if (st.arrow) { const [a, b] = pathEnd(sub).map(q => P(...q)); s += headAt(a, b, st.c, st.w); }
      }
    }
    for (const d of f.depths || []) {
      const [x, y] = P(d[0], d[1]); s += txt(x, y, d[2], { s: 40 });
      if (d[3]) { const w = tw0(d[2], 40); s += `<line x1="${f1(x - w / 2)}" y1="${f1(y + 7)}" x2="${f1(x + w / 2)}" y2="${f1(y + 7)}" stroke="var(--ink)" stroke-width="4"/>`; }
    }
    for (const m of f.marks || []) {
      const [col, name] = [m[2], m[3] || ''];
      if ((cfg.dropMarks || []).includes(name)) continue;
      const [x, y] = P(m[0], m[1]), lo = (cfg.markLabel || {})[name] || {};
      const lab = (dy, a = 'middle', dx = 0) => name && !lo.hide ? txt(x + (lo.dx ?? dx), y + (lo.dy ?? dy), name, { s: 32, a: lo.a || a }) : '';
      if (cardKind(name) || (col === 'y' && name === 'ODAS')) { s += card(x, y, cardKind(name) || 'special') + lab(70); continue; }
      if (name === 'anchor') { s += anchorGlyph(x, y, 0.9); continue; }
      if (name === 'rock') { s += rockSym(x, y) + lab(-56); continue; }
      if (!name && col === 'k') { s += islet(x, y); continue; }
      if (col === 'r') { s += flare(x, y, SCOL.r) + `<circle cx="${f1(x)}" cy="${f1(y)}" r="12" fill="${SCOL.r}" stroke="var(--ink)" stroke-width="4"/>` + lab(-34); continue; }
      if (isLightName(name) || /light/.test(name)) s += flare(x, y) + landmark(x, y);
      else if (col === 'w') s += beacon(x, y);
      else s += landmark(x, y);
      s += lab(-30);
    }
    for (const l of f.labels || []) {
      if ((cfg.drop || []).includes(l[2])) continue;
      const lo = (cfg.labelAt || {})[l[2]] || {}, [x, y] = P(lo.x ?? l[0], lo.y ?? l[1]);
      s += txt(x, y, l[2], { s: lo.s || 34, a: lo.a || l[3] || 'middle' });
    }
    s += (extra.mid || []).map(o => item(o, P, k)).join('');
    if (f.boat && !extra.noBoat) { const [x, y] = P(f.boat[0], f.boat[1]); s += boat(x, y, f.boat[2], { you: true, scale: 2.3 }); }
    s += (extra.over || []).map(o => item(o, P, k)).join('');
    return s;
  };
}
const chartAvoid = f => [...(f.depths || []), ...(f.marks || []), ...(f.labels || []), ...(f.boat ? [f.boat] : []),
  ...(f.track ? parsePath(f.track).flatMap(sub => sub.filter(x => x.c !== 'Z').flatMap(x => x.p)) : [])].map(p => [p[0], p[1]]);

/* overlay items for the plans, in the figure's own coordinates */
function item(o, P, k) {
  const C = c => c === 'red' ? SCOL.wind : c === 'ink' ? 'var(--ink)' : c === 'accent' ? 'var(--accent)' : c === 'muted' ? 'var(--muted)' : c === 'magenta' ? LIGHT : SCOL.course;
  switch (o.t) {
    case 'arrow': { const [a, b] = [P(...o.a), P(...o.b)]; return arrow(a[0], a[1], b[0], b[1], { c: C(o.c), w: o.w || 6, dash: o.dash, h: o.h }); }
    case 'line': { const q = o.pts.map(p => P(...p)); return `<path d="${q.map((p, i) => (i ? 'L' : 'M') + f1(p[0]) + ' ' + f1(p[1])).join(' ')}" fill="none" stroke="${C(o.c)}" stroke-width="${o.w || 5}" stroke-linecap="round" stroke-linejoin="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/>` + (o.arrow ? (() => { const [a, b] = q.slice(-2); return arrow(a[0], a[1], b[0], b[1], { c: C(o.c), w: o.w || 5, h: 24 }); })() : ''); }
    case 'curve': { const q = o.pts.map(p => P(...p)); return `<path d="M${q[0].map(f1).join(' ')} C ${q.slice(1).map(p => p.map(f1).join(' ')).join(' ')}" fill="none" stroke="${C(o.c)}" stroke-width="${o.w || 6}" stroke-linecap="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/>` + (o.arrow ? (() => { const [a, b] = q.slice(-2); return headAt(a, b, C(o.c), o.w || 6); })() : ''); }
    case 'zone': { const q = o.pts.map(p => P(...p)); return `<path d="${q.map((p, i) => (i ? 'L' : 'M') + f1(p[0]) + ' ' + f1(p[1])).join(' ')} Z" fill="${o.fill || 'rgba(224,37,27,.12)'}" stroke="${C(o.c || 'red')}" stroke-width="5" stroke-dasharray="${o.dash || '14 10'}"/>`; }
    case 'circle': { const [x, y] = P(o.x, o.y); return `<circle cx="${f1(x)}" cy="${f1(y)}" r="${f1(o.r * k)}" fill="${o.fill || 'none'}" stroke="${C(o.c)}" stroke-width="${o.w || 6}" stroke-dasharray="${o.dash || '16 12'}"/>`; }
    case 'pill': { const [x, y] = P(o.x, o.y); return pill(x + (o.dx || 0), y + (o.dy || 0), o.text, o.kind || 'light', o.size || 30); }
    case 'text': { const [x, y] = P(o.x, o.y); return txt(x + (o.dx || 0), y + (o.dy || 0), o.text, { s: o.size || 34, a: o.a, f: o.f }); }
    case 'spot': { const [x, y] = P(o.x, o.y); return spotRing(x, y, o.label, o.r); }
    case 'boat': { const [x, y] = P(o.x, o.y); return boat(x, y, o.hdg, { scale: o.scale || 2.3, fill: 'var(--muted)', ghost: true }); }
    case 'anchor': { const [x, y] = P(o.x, o.y); return anchorGlyph(x, y, o.s || 0.9); }
    case 'dim': { const [a, b] = [P(...o.a), P(...o.b)], an = Math.atan2(b[1] - a[1], b[0] - a[0]), nx = -Math.sin(an) * (o.off || 0), ny = Math.cos(an) * (o.off || 0);
      const tick = (x, y) => `<line x1="${f1(x - Math.sin(an) * 14)}" y1="${f1(y + Math.cos(an) * 14)}" x2="${f1(x + Math.sin(an) * 14)}" y2="${f1(y - Math.cos(an) * 14)}" stroke="var(--ink)" stroke-width="4"/>`;
      return `<g><line x1="${f1(a[0] + nx)}" y1="${f1(a[1] + ny)}" x2="${f1(b[0] + nx)}" y2="${f1(b[1] + ny)}" stroke="var(--ink)" stroke-width="4"/>${tick(a[0] + nx, a[1] + ny)}${tick(b[0] + nx, b[1] + ny)}${pill((a[0] + b[0]) / 2 + nx + (o.pdx || 0), (a[1] + b[1]) / 2 + ny + (o.pdy || 0), o.text, o.kind || 'light', o.size || 28)}</g>`; }
    case 'windAt': { // a wind arrow blowing past a point, from o.from, ending short of it, with an optional pill at its tail
      const [x, y] = P(o.x, o.y), L = o.len || 150, gap = o.gap ?? 70, [hx, hy] = pol(x, y, gap, o.from), [tx, ty] = pol(x, y, gap + L, o.from);
      return arrow(tx, ty, hx, hy, { c: SCOL.wind, w: o.w || 10, h: 30 }) + (o.text ? pill(tx + (o.pdx || 0), ty + (o.pdy || 0), o.text, 'red', 30) : ''); }
    case 'windCorner': { // the schematic's wind arrow, top right, with its pill
      const x = W - 110, y = 95, [ax, ay] = pol(x, y, 48, o.from), [bx, by] = pol(x, y, 48, o.from + 180);
      return arrow(ax, ay, bx, by, { c: SCOL.wind, w: 9, h: 26 }) + pill(x, y + 86, o.text, 'red', 30); }
    case 'raw': return o.svg(P, k);
  }
  return '';
}

/* ---------------- isobars ---------------- */
const ICX = 120, ICY = 92;
const ringsOf = f => f.tight ? [18, 34, 50, 66, 82, 98, 114, 130, 146, 162] : [26, 52, 78, 104];
const onRing = (cx, cy, r, brg) => [cx + 1.15 * r * Math.sin(brg * RAD), cy - r * Math.cos(brg * RAD)];
function isoDraw(f, extra = {}) {
  return (P, k, Ha) => {
    let s = '';
    const system = (cx, cy, rings, letter, values = []) => {
      let g = rings.map(r => { const [x, y] = P(cx, cy); return `<ellipse cx="${f1(x)}" cy="${f1(y)}" rx="${f1(1.15 * r * k)}" ry="${f1(r * k)}" fill="none" stroke="var(--ink)" stroke-width="5"/>`; }).join('');
      g += values.map((v, i) => { const [x, y] = P(cx, cy - rings[i]); return pill(x, y, v, 'light', 30); }).join('');
      const [x, y] = P(cx, cy); return g + txt(x, y + 32, letter, { s: 92, halo: false });
    };
    s += system(ICX, ICY, ringsOf(f), f.center || 'L', f.values || []);
    if (extra.second) s += system(...extra.second);
    s += (extra.under || []).map(o => item(o, P, k)).join('');
    if (f.boat) { const [x, y] = P(f.boat[0], f.boat[1]); s += boat(x, y, 0, { you: true, scale: 2.1 }); const at = extra.youAt || (y + 140 < Ha ? 'below' : 'above'); const [dx, dy] = { below: [0, 92], above: [0, -92], left: [-100, 0], right: [100, 0] }[at]; s += pill(x + dx, y + dy, 'You', 'accent', 30); }
    s += (extra.over || []).map(o => item(o, P, k)).join('');
    return s;
  };
}
// wind arrows round a system: anticlockwise and angled in round a low, clockwise and angled out round a high
const circ = (letter, cx, cy, r, brgs, o = {}) => brgs.map(b => { const [x, y] = onRing(cx, cy, r, b), dir = letter === 'L' ? b - 105 : b + 75, L = o.len || 26;
  const [ax, ay] = pol(x, y, -L, dir), [bx, by] = pol(x, y, L, dir); return { t: 'arrow', a: [ax, ay], b: [bx, by], c: 'red', w: o.w || 7 }; });

/* ---------------- lights: the description taken apart, and rhythms ---------------- */
function strip(x0, x1, y, h, T, flashes) {   // flashes: [[t0, dur, colour]]
  const px = (x1 - x0) / T; let s = `<rect x="${x0}" y="${y}" width="${x1 - x0}" height="${h}" rx="8" fill="#141b26"/>`;
  for (const [t, d, c] of flashes) if (t < T) s += `<rect x="${f1(x0 + t * px)}" y="${y + 6}" width="${f1(Math.max(6, Math.min(d, T - t) * px))}" height="${h - 12}" rx="5" fill="${c === 'r' ? SCOL.r : '#fff3c4'}"/>`;
  return s;
}
const ticks = (x0, x1, y, T, every) => { let s = ''; for (let t = 0; t <= T; t += every) s += txt(x0 + (x1 - x0) * t / T, y, `${t} s`, { s: 28, w: 400, f: 'var(--muted)', halo: false }); return s; };
const repeat = (period, T, groups) => { const out = []; for (let k0 = 0; k0 * period < T; k0++) for (const [t, d, c] of groups) out.push([k0 * period + t, d, c]); return out; };
function lightCard({ tokens, hi = [], rhythm, note, title, key, extra = '' }) {
  return frame({ title, key, noCompass: true, draw: (P, k, Ha) => {
    let s = '', gap = 34; const size = 50, ms = 32, ty = rhythm ? 190 : note ? Ha / 2 - 90 : Ha / 2 - 30;
    const ws = tokens.map(([t, m]) => Math.max(tw(t, size) + size * 1.3, tw(m, ms) + 10));
    let x = (W - ws.reduce((a, b) => a + b, 0) - gap * (tokens.length - 1)) / 2;
    tokens.forEach(([t, m], i) => { const cx = x + ws[i] / 2, on = hi.includes(i);
      s += pill(cx, ty, t, on ? 'accent' : 'light', size) + txt(cx, ty + 100, m, { s: ms, w: on ? 700 : 400, f: on ? 'var(--ink)' : 'var(--muted)' });
      if (on) s += `<line x1="${f1(cx)}" y1="${ty + 42}" x2="${f1(cx)}" y2="${ty + 66}" stroke="var(--accent)" stroke-width="5"/>`; x += ws[i] + gap; });
    s += txt(W / 2, ty - 98, 'On the chart', { s: 32, f: 'var(--muted)', halo: false });
    if (rhythm) s += txt(150, 400, rhythm.label, { s: 32, a: 'start', halo: false }) + strip(150, 1130, 420, 86, rhythm.T, rhythm.flashes) + ticks(150, 1130, 548, rhythm.T, rhythm.every || 5);
    if (note) s += pill(W / 2, ty + 210, note, 'accent', 34);
    return s + extra;
  } });
}
function rhythmRows({ rows, T, every = 5, title, key }) {
  return frame({ title, key, cols: 1, noCompass: true, draw: () => {
    const x0 = 320, x1 = 1220, rowH = 120; let s = '';
    rows.forEach((r, i) => { const y = 60 + i * rowH;
      if (r.hi) s += `<rect x="20" y="${y - 16}" width="${W - 40}" height="${rowH - 14}" rx="18" fill="rgba(255,230,0,.16)" stroke="${SCOL.course}" stroke-width="5"/>`;
      s += txt(44, y + 56, r.label, { s: 38, a: 'start', halo: false }) + strip(x0, x1, y + 8, 74, T, r.flashes); });
    return s + ticks(x0, x1, 60 + rows.length * rowH + 20, T, every);
  } });
}

/* ---------------- per-figure settings for the question image ---------------- */
const TSS = { zones: [0] };
const CFG = {
  'bs-048': { labelAt: { 'keep in line': { x: 172, y: 135, a: 'start' } } },
  'bs-049': { track: 'bearing', drop: ['cocked hat'] },                       // the label names the answer
  'bs-077': { dropMarks: ['drop here'], drop: ['3–4 boat lengths'] },        // where and when to drop is the answer
  'bs-396': TSS, 'bs-397': TSS, 'bs-398': TSS, 'bs-399': { ...TSS, labelAt: { 'separation zone': { x: 150, y: 122 } } }, 'bs-400': TSS, 'bs-401': TSS, 'bs-403': TSS,
  'bs-461': { track: 'plain' },
  'bs-478': { area: [[40, 76], [280, 110]] },
  'bs-493': { markLabel: { rear: { dx: -26, dy: 10, a: 'end' }, front: { dx: -26, dy: 10, a: 'end' } } },
  'bs-497': { track: 'bearing' },
  'bs-498': { track: 'clearing', labelAt: { 'clearing line 060°T': { x: 186, y: 92, a: 'start' } } },
  'bs-503': { track: 'bearing' },
  'bs-504': { track: 'bearing' },
  'bs-566': { markLabel: { 'W cardinal': { dx: -40, dy: 10, a: 'end' } } },
  'bs-570': { markLabel: { 'N cardinal': { dy: -100 } } },
  'bs-572': { markLabel: { 'N cardinal': { dx: 46, dy: 10, a: 'start' }, 'S cardinal': { dx: 46, dy: 10, a: 'start' } } },
  'bs-584': { markLabel: { 'Fl 5s 18m 12M': { dx: -30, dy: 10, a: 'end' } } },
  'bs-585': { markLabel: { 'Oc(2) 8s': { dx: -30, dy: 10, a: 'end' } } },
  'bs-587': { markLabel: { 'Fl(3) WR 15s 23m 18/15M': { dx: -30, dy: 10, a: 'end' } } },
  'bs-588': { markLabel: { 'Fl(3) WR 15s 23m 18/15M': { dx: -30, dy: 10, a: 'end' } } },
  'bs-597': { markLabel: { 'Al WR 10s': { dx: -30, dy: 10, a: 'end' } } },
  'bs-598': { markLabel: { 'Fl(2) 10s 15m 10M': { dx: -30, dy: 10, a: 'end' } } },
  'bs-589': { markLabel: { 'A  Fl 5s': { dy: 52 }, 'B  Fl(3) 15s': { dy: 52 }, 'C  Fl(2) 10s': { dy: 52 } } },
  'bs-590': { markLabel: { 'A  Fl 10s': { dy: 52 }, 'B  Oc 10s': { dy: 52 }, 'C  Iso 10s': { dy: 52 } } },
  'bs-766': { track: 'gps' },
  'bs-771': { markLabel: { rock: { dy: -58 } } },
  'bs-925': { track: 'distance', markLabel: { 'Sounion lt': { dx: 30, dy: 10, a: 'start' } } },
};
const keyOf = (f, id) => { const p = [...(f.panel || [])]; if (id === 'bs-925') return [p[0], p[1] + ' ' + p[2]]; return p; };
const titleOf = f => f.note || 'Depths in metres below chart datum';

/* ---------------- the plans (answer drawings) ---------------- */
const X = (a, b, c, d) => { const [x1, y1] = a, [x2, y2] = b, [x3, y3] = c, [x4, y4] = d, den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4), t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den; return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)]; };
const lanesFlow = [{ t: 'arrow', a: [300, 84], b: [200, 84], c: 'magenta', w: 6 }, { t: 'arrow', a: [200, 162], b: [300, 162], c: 'magenta', w: 6 }];
const PLAN = {
  'bs-046': f => ({ title: 'Depth over the shoal at 14:00', key: ['Charted 1.5 m + height of tide 1.2 m = 2.7 m of water', 'Draft 1.9 m: about 0.8 m under the keel'],
    under: [{ t: 'zone', pts: [[128, 98], [176, 96], [178, 128], [126, 130]] }], over: [{ t: 'pill', x: 238, y: 112, text: '1.5 + 1.2 = 2.7 m', kind: 'red' }] }),
  'bs-049': f => { const L = [[[40, 36], [170, 150]], [[160, 36], [172, 160]], [[290, 36], [166, 156]]], a = X(...L[0], ...L[1]), b = X(...L[1], ...L[2]), c = X(...L[0], ...L[2]);
    return { title: 'Three bearings · the cocked hat', key: ['A small triangle: you are inside it', 'Take the corner nearest danger as your position'],
      over: [{ t: 'zone', pts: [a, b, c], fill: 'rgba(224,37,27,.35)', dash: '0' }, { t: 'circle', x: (a[0] + b[0] + c[0]) / 3, y: (a[1] + b[1] + c[1]) / 3, r: 9, c: 'red', w: 5, dash: '0' }, { t: 'pill', x: 236, y: 172, text: 'cocked hat', kind: 'red' }] }; },
  'bs-077': f => ({ title: 'Stern-to · when to drop the anchor', key: ['Drop about 3–4 boat lengths out, already reversing', 'Pay out chain as you go astern, then snug it up'],
    over: [{ t: 'anchor', x: 160, y: 170 }, { t: 'pill', x: 232, y: 172, text: 'drop here', kind: 'accent' }, { t: 'dim', a: [100, 40], b: [100, 170], text: '3–4 boat lengths', pdx: -10 }] }),
  'bs-396': f => ({ title: 'Crossing a traffic separation scheme', key: ['Cross on a heading at right angles to the traffic flow', 'The stream sets you east: keep the heading square'],
    over: [{ t: 'arrow', a: [210, 150], b: [210, 40], c: 'course', w: 7 }, { t: 'line', pts: [[214, 160], [262, 36]], c: 'red', w: 5, dash: '12 10' }, { t: 'pill', x: 150, y: 36, text: 'heading 000°', kind: 'accent' }, { t: 'pill', x: 268, y: 186, text: 'track over ground', kind: 'red', size: 26 }] }),
  'bs-397': f => ({ title: 'Joining a traffic lane', key: ['Join at the end of the lane, or from the side at a small angle', 'Then follow the flow: this lane runs east'],
    over: [{ t: 'curve', pts: [[210, 176], [230, 160], [250, 150], [300, 147]], c: 'accent', w: 7, arrow: true }, { t: 'arrow', a: [-30, 148], b: [30, 148], c: 'accent', w: 7 }, { t: 'pill', x: 268, y: 186, text: 'small angle', kind: 'accent', size: 28 }, { t: 'pill', x: 40, y: 178, text: 'at the end', kind: 'accent', size: 28 }] }),
  'bs-399': f => ({ title: 'Separation zone · keep out', key: ['Enter the zone only to cross, join, leave or in an emergency', 'Bound east: follow the eastbound lane'], noTrack: true,
    over: [{ t: 'line', pts: [[30, 118], [300, 118]], c: 'red', w: 6, dash: '16 11' }, { t: 'pill', x: 230, y: 96, text: 'not along the zone', kind: 'red', size: 28 }, { t: 'arrow', a: [40, 160], b: [300, 160], c: 'accent', w: 7 }, { t: 'pill', x: 230, y: 182, text: 'follow the eastbound lane', kind: 'accent', size: 28 }] }),
  'bs-400': f => ({ title: 'Traffic lanes · go with the flow', key: ['In a lane, go in the general direction of the traffic flow', 'This lane runs east: heading 270° is the wrong way'],
    under: lanesFlow, over: [{ t: 'pill', x: 232, y: 186, text: 'against the flow', kind: 'red' }] }),
  'bs-401': f => ({ title: 'The end of a scheme', key: ['Where a scheme ends, ships change course and converge', 'Navigate with particular caution, or keep well clear'],
    under: [{ t: 'arrow', a: [196, 148], b: [300, 112], c: 'ink', w: 5 }, { t: 'arrow', a: [196, 150], b: [304, 150], c: 'ink', w: 5 }, { t: 'arrow', a: [304, 40], b: [208, 88], c: 'ink', w: 5 }, { t: 'arrow', a: [310, 86], b: [210, 94], c: 'ink', w: 5 }],
    over: [{ t: 'pill', x: 262, y: 26, text: 'ships alter course here', kind: 'red', size: 28 }] }),
  'bs-403': f => ({ title: 'Crossing under sail', key: ['Wind from the north: you can\'t sail across at right angles', 'Motor-sail to hold a heading near 90° to the lanes'],
    over: [{ t: 'arrow', a: [210, 150], b: [210, 40], c: 'course', w: 7 }, { t: 'pill', x: 210, y: 24, text: 'motor-sail · heading 000°', kind: 'accent', size: 28 }, { t: 'windCorner', from: 0, text: 'Wind N' }] }),
  'bs-461': f => ({ title: 'Latitude · read it off the side of the chart', key: ['The parallels are 10′ apart: the boat is three-quarters up', '37°40′ + 7.5′ = 37°47.5′ N'],
    over: [{ t: 'dim', a: [120, 26], b: [120, 63], text: '2.5′' }, { t: 'dim', a: [120, 63], b: [120, 174], text: '7.5′' }, { t: 'line', pts: [[120, 63], [300, 63]], c: 'accent', w: 4, dash: '10 8' }, { t: 'pill', x: 250, y: 92, text: '37°47.5′ N', kind: 'accent', size: 34 }] }),
  'bs-465': f => ({ title: 'Latitude by distance run north', key: ['Due north, one mile = one minute of latitude', '36°50.0′ + 12.0′ = 37°02.0′ N'],
    over: [{ t: 'pill', x: 236, y: 168, text: '36°50.0′ N', size: 30 }, { t: 'spot', x: 150, y: 40 }, { t: 'pill', x: 236, y: 40, text: '37°02.0′ N', kind: 'accent', size: 34 }, { t: 'pill', x: 196, y: 100, text: '12 M', size: 30 }] }),
  'bs-468': f => ({ title: 'A drying rock at 10:00', key: ['Underlined 1.5: the rock dries 1.5 m above chart datum', 'Tide 0.6 m: it shows 1.5 − 0.6 = 0.9 m above the water'],
    under: [{ t: 'zone', pts: [[128, 74], [172, 74], [174, 112], [126, 112]] }], over: [{ t: 'pill', x: 236, y: 92, text: 'shows 0.9 m', kind: 'red' }] }),
  'bs-469': f => ({ title: 'Water over a drying patch at 15:30', key: ['Underlined 0.4: the patch dries 0.4 m above chart datum', 'Tide 1.6 m: water over it 1.6 − 0.4 = 1.2 m'],
    under: [{ t: 'zone', pts: [[138, 88], [184, 88], [186, 116], [136, 116]] }], over: [{ t: 'pill', x: 186, y: 64, text: '1.6 − 0.4 = 1.2 m', kind: 'red' }] }),
  'bs-493': f => ({ title: 'Checking the compass on a transit', key: ['Transit 315°T − variation 3°E = 312°M', 'Compass reads 317°, 5° more: deviation 5°W'],
    over: [{ t: 'pill', x: 236, y: 120, text: '312°M · compass 317°', kind: 'accent' }] }),
  'bs-495': f => ({ title: 'Choosing objects for a fix', key: ['A, C and D: near you and well spread round you', 'B lies behind A on the same line: it adds nothing'],
    under: [{ t: 'line', pts: [[160, 155], [62, 96]], c: 'accent', w: 6 }, { t: 'line', pts: [[62, 96], [13, 66]], c: 'red', w: 5, dash: '10 9' }, { t: 'line', pts: [[160, 155], [165, 30]], c: 'accent', w: 6 }, { t: 'line', pts: [[160, 155], [275, 93]], c: 'accent', w: 6 }],
    over: [{ t: 'pill', x: 70, y: 150, text: 'B: same line as A', kind: 'red', size: 28 }] }),
  'bs-496': f => ({ title: 'The order of the bearings', key: ['Ahead and astern (P, R) change slowly: take them first', 'On the beam (Q) it changes fastest: take it last'],
    under: [{ t: 'line', pts: [[160, 112], [300, 100]], c: 'accent', w: 5 }, { t: 'line', pts: [[160, 112], [20, 40]], c: 'accent', w: 5 }, { t: 'line', pts: [[160, 112], [160, 40]], c: 'accent', w: 5, dash: '12 9' }],
    over: [{ t: 'spot', x: 300, y: 130, label: '1', r: 26 }, { t: 'spot', x: 46, y: 64, label: '2', r: 26 }, { t: 'spot', x: 190, y: 70, label: '3', r: 26 }] }),
  'bs-497': f => { const L = [[[50, 42], [230, 152]], [[170, 40], [144, 186]], [[280, 36], [130, 176]]], a = X(...L[0], ...L[1]), b = X(...L[1], ...L[2]), c = X(...L[0], ...L[2]);
    const near = [a, b, c].reduce((m, p) => Math.hypot(p[0] - 104, p[1] - 132) < Math.hypot(m[0] - 104, m[1] - 132) ? p : m);
    return { title: 'A large cocked hat', key: ['A large triangle means an error in a bearing', 'Re-take them; till then, use the corner nearest the rocks'],
      under: [{ t: 'zone', pts: [a, b, c], fill: 'rgba(224,37,27,.18)', dash: '0' }], over: [{ t: 'spot', x: near[0], y: near[1], r: 22 }, { t: 'pill', x: near[0] + 74, y: near[1] + 26, text: 'assume this corner', kind: 'red', size: 28 }] }; },
  'bs-498': f => ({ title: 'Clearing line · church less than 060°T', key: ['South of the line the church bears less than 060°T', 'More than 060°: you are standing into danger'],
    under: [{ t: 'zone', pts: [[84, 74], [136, 74], [138, 100], [82, 100]] }],
    over: [{ t: 'pill', x: 112, y: 150, text: 'church < 060°: safe', kind: 'accent', size: 28 }, { t: 'pill', x: 60, y: 126, text: 'church > 060°: reef side', kind: 'red', size: 26 }] }),
  'bs-503': f => { const fix = [157, 126]; return { title: 'A bearing and a sounding', key: ['The 20 m sounding puts you on the 20 m contour', 'Where it meets the bearing: a rough fix'],
    under: [{ t: 'curve', pts: [[20, 116], [70, 132], [110, 130], [160, 126]], c: 'accent', w: 5, dash: '12 9' }, { t: 'curve', pts: [[160, 126], [215, 134], [270, 128], [320, 116]], c: 'accent', w: 5, dash: '12 9' }],
    over: [{ t: 'spot', x: fix[0], y: fix[1], r: 24 }, { t: 'pill', x: 250, y: 150, text: 'rough fix', kind: 'accent' }, { t: 'pill', x: 60, y: 146, text: '20 m contour', size: 26 }] }; },
  'bs-504': f => ({ title: 'One bearing: a position line', key: ['One bearing gives one position line, not a fix', 'Cross it with a second line to fix your position'],
    under: [{ t: 'line', pts: [[200, 36], [115, 177]], c: 'accent', w: 9 }], over: [{ t: 'pill', x: 236, y: 154, text: 'you are somewhere on it', kind: 'accent', size: 28 }] }),
  'bs-507': f => ({ title: 'Estimated position at 11:00', key: ['Course 090°T, log 6.0 M → DR', 'Tide 180°T 1.5 kn for the hour → EP'], noTrack: true,
    over: [{ t: 'arrow', a: [55, 120], b: [240, 120], c: 'ink', w: 5 }, { t: 'arrow', a: [262, 128], b: [262, 168], c: 'course', w: 6 }, { t: 'line', pts: [[55, 122], [248, 174]], c: 'red', w: 4, dash: '12 10' },
      { t: 'spot', x: 262, y: 120, label: 'DR', r: 30 }, { t: 'spot', x: 262, y: 176, label: 'EP', r: 30 }, { t: 'pill', x: 150, y: 100, text: '6 M by log', size: 28 }, { t: 'pill', x: 302, y: 148, text: 'tide 1.5 M', kind: 'accent', size: 26 }] }),
  'bs-513': f => ({ title: 'Dead reckoning at 15:30', key: ['14:00 to 15:30 is 1.5 h × 4.0 kn = 6.0 M', 'DR: 6.0 M along 270°T from the fix; no tide in a DR'], noTrack: true,
    over: [{ t: 'arrow', a: [255, 140], b: [74, 140], c: 'ink', w: 5 }, { t: 'spot', x: 50, y: 140, label: 'DR', r: 30 }, { t: 'pill', x: 160, y: 118, text: '6.0 M', size: 30 }, { t: 'pill', x: 50, y: 170, text: '15:30', kind: 'accent', size: 28 }] }),
  'bs-515': f => { const A = [58, 120], B = [58, 170], C = [58 + Math.sqrt(150 ** 2 - 50 ** 2), 120];
    return { title: 'Course to steer across the stream', key: ['One hour: tide 2 M south, then 6 M to cut the track', 'Steer about 070°T, 20° up into the stream'],
      over: [{ t: 'arrow', a: A, b: B, c: 'red', w: 6 }, { t: 'arrow', a: B, b: C, c: 'accent', w: 7 }, { t: 'pill', x: 112, y: 182, text: 'tide 2 M', kind: 'red', size: 26 }, { t: 'pill', x: 150, y: 84, text: 'steer 070°T', kind: 'accent', size: 32 }] }; },
  'bs-538': f => ({ title: 'Rounding a breakwater head', key: ['Rubble and shoals lie off breakwater heads', 'Round it wide, then turn in'],
    under: [{ t: 'circle', x: 124, y: 130, r: 30, c: 'red', fill: 'rgba(224,37,27,.10)' }],
    over: [{ t: 'curve', pts: [[238, 156], [180, 185], [70, 190], [62, 80]], c: 'accent', w: 7, arrow: true }, { t: 'pill', x: 210, y: 118, text: 'shoal off the head', kind: 'red', size: 28 }] }),
  'bs-566': f => ({ title: 'Passing a west cardinal', key: ['West cardinal: the safe water is to the west', 'Alter to port and leave it to starboard'], noTrack: true,
    cfg: { markLabel: { 'W cardinal': { dy: 72 } } },
    over: [{ t: 'curve', pts: [[150, 146], [118, 126], [98, 106], [98, 30]], c: 'accent', w: 7, arrow: true }, { t: 'pill', x: 44, y: 172, text: 'pass west', kind: 'accent' }] }),
  'bs-570': f => ({ title: 'Passing a north cardinal', key: ['North cardinal: the safe water is to the north', 'Alter to starboard and leave it to port'], noTrack: true,
    cfg: { markLabel: { 'N cardinal': { dx: -46, dy: 10, a: 'end' } } },
    over: [{ t: 'curve', pts: [[245, 112], [250, 60], [200, 44], [96, 46]], c: 'accent', w: 7, arrow: true }, { t: 'pill', x: 292, y: 84, text: 'pass north', kind: 'accent' }] }),
  'bs-572': f => ({ title: 'Two cardinals, one shoal', key: ['Safe water: north of the N mark, south of the S mark', 'Never pass between them'],
    under: [{ t: 'zone', pts: [[108, 86], [214, 80], [214, 116], [108, 120]] }],
    over: [{ t: 'curve', pts: [[64, 90], [100, 0], [220, 4], [300, 24]], c: 'accent', w: 6, arrow: true }, { t: 'curve', pts: [[64, 110], [100, 200], [220, 196], [300, 176]], c: 'accent', w: 6, arrow: true }, { t: 'pill', x: 262, y: 100, text: 'shoal between them', kind: 'red', size: 28 }] }),
  'bs-754': f => ({ title: 'Swinging to a north wind', key: ['Wind N: you lie south of the anchor, 35 m of chain away', 'That is on the 1.2 m shoal: re-anchor further north'], noBoat: true,
    under: [{ t: 'circle', x: 150, y: 112, r: 46, c: 'ink', w: 4 }, { t: 'boat', x: 150, y: 156, hdg: 0 }, { t: 'boat', x: 150, y: 62, hdg: 180, scale: 2.3 }],
    over: [{ t: 'pill', x: 266, y: 172, text: '1.2 m: aground', kind: 'red' }, { t: 'arrow', a: [182, 100], b: [182, 46], c: 'accent', w: 6 }, { t: 'pill', x: 226, y: 30, text: 're-anchor further north', kind: 'accent', size: 26 }, { t: 'windCorner', from: 0, text: 'Wind N' }] }),
  'bs-766': f => ({ title: 'Swinging or dragging?', key: ['Swinging draws an arc round the anchor', 'A straight line downwind (SE): the anchor is dragging'],
    over: [{ t: 'pill', x: 80, y: 82, text: 'earlier: swinging', size: 28 }, { t: 'pill', x: 268, y: 108, text: 'now: dragging', kind: 'red', size: 28 }, { t: 'windCorner', from: 315, text: 'Wind NW' }] }),
  'bs-771': f => ({ title: 'Swing room when the wind goes west', key: ['Chain 40 m, depth + bow 6 m: about 39.5 m along the bottom', '+ boat 13 m ≈ 52 m of swing: the rock at 45 m is inside it'],
    under: [{ t: 'circle', x: 90, y: 150, r: 173, c: 'red', w: 5 }],
    over: [{ t: 'boat', x: 244, y: 150, hdg: 270, scale: 3.4 }, { t: 'dim', a: [90, 118], b: [263, 118], text: '≈ 52 m', kind: 'red' }, { t: 'windCorner', from: 270, text: 'Wind W' }] }),
  'ci-318': f => ({ title: 'No fix: the last stored position', key: ['Until it has satellites the plotter shows the last fix, Fri 18:10',
    'Wait for a lock, then check the boat sits on its berth'], noBoat: true,
    over: [{ t: 'raw', svg: (P) => { const [x, y] = P(240, 150); return boat(x, y, 0, { scale: 2.3, fill: 'var(--muted)', ghost: true }); } },
      { t: 'line', pts: [[230, 148], [180, 142], [148, 92]], c: 'red', w: 4, dash: '10 9' },
      { t: 'raw', svg: (P) => { const [x, y] = P(142, 76); return boat(x, y, 0, { you: true, scale: 2.0 }); } },
      { t: 'pill', x: 236, y: 182, text: 'stale fix, Fri 18:10', kind: 'red', size: 28 }, { t: 'pill', x: 218, y: 70, text: 'the boat: on its berth', kind: 'accent', size: 28 }] }),
  'bs-925': f => ({ title: 'Position from a landmark', key: ['Give the true bearing FROM the landmark, then the distance', '"180 degrees from Cape Sounion light, 2 miles"'],
    over: [{ t: 'arrow', a: [98, 80], b: [98, 142], c: 'accent', w: 6 }, { t: 'pill', x: 226, y: 100, text: '180° from the light, 2 miles', kind: 'accent', size: 28 }] }),
};
// isobars plans
const ISOPLAN = {
  'bs-061': f => ({ title: 'Isobars packed tight', key: ['Close isobars: a steep pressure gradient', 'Strong wind: stay in port or reef early'],
    over: [...[[114, 78], [130, 88], [146, 98]].flatMap(([r, b]) => circ('L', ICX, ICY, r, [b], { len: 26, w: 9 })), { t: 'pill', x: 262, y: 30, text: 'strong wind', kind: 'red' }] }),
  'bs-062': f => ({ title: 'Wind round a low', key: ['Anticlockwise round a low, angled in towards it', 'Low to your NW: wind from the SW, veering as it passes'],
    over: [...circ('L', ICX, ICY, 78, [0, 90, 180, 270]), { t: 'windAt', x: 260, y: 160, from: 225, len: 90, gap: 50 }, { t: 'pill', x: 196, y: 186, text: 'wind SW', kind: 'red' }] }),
  'bs-066': f => ({ title: 'The meltemi (Aegean, July)', key: ['High to the NW, heat low over Anatolia to the E', 'Steady N wind, F5–7, strongest in the afternoon'],
    youAt: 'above', over: [{ t: 'arrow', a: [232, 40], b: [232, 110], c: 'red', w: 10 }, { t: 'arrow', a: [205, 60], b: [205, 122], c: 'red', w: 8 }, { t: 'pill', x: 290, y: 20, text: 'meltemi N 6–7', kind: 'red' }] }),
  'bs-655': f => ({ title: 'Wind round a high', key: ['Clockwise round a high, angled out of it', 'East of the high: the wind comes from the north'],
    over: [...circ('H', ICX, ICY, 78, [70, 200, 290]), { t: 'windAt', x: 255, y: 92, from: 0, len: 110, gap: 56, text: 'wind N', pdx: 80, pdy: 10 }] }),
  'bs-656': f => ({ title: 'Wind round a low', key: ['Anticlockwise round a low, angled in towards it', 'SW of the low: the wind comes from the north-west'],
    over: [...circ('L', ICX, ICY, 78, [60, 120, 300]), { t: 'windAt', x: 40, y: 170, from: 315, len: 90, gap: 52 }, { t: 'pill', x: 40, y: 112, text: 'wind NW', kind: 'red' }] }),
  'bs-661': f => { const [bx, by] = [255, 60];
    return { title: 'Surface wind at sea', key: ['Nearly along the isobars, angled in towards the low', 'At sea, friction turns it 10–15° across them'],
      over: [...circ('L', ICX, ICY, 78, [150, 240]), { t: 'line', pts: [pol(292, 74, -56, 347), pol(292, 74, 56, 347)], c: 'ink', w: 4, dash: '10 9' },
        { t: 'arrow', a: pol(292, 74, -50, 332), b: pol(292, 74, 50, 332), c: 'red', w: 9 }, { t: 'pill', x: 288, y: 150, text: '10–15° in', kind: 'red' }] }; },
};
const ISOSECOND = { 'bs-066': [306, 140, [20, 40], 'L', []] };
const YOUAT = { 'bs-066': 'left', 'bs-656': 'right', 'bs-062': 'below', 'bs-061': 'left', 'bs-361': 'left' };

/* ---------------- Russian for every string we draw ---------------- */
const RU = {
  'No fix: the last stored position': 'Нет фикса: последняя сохранённая позиция',
  'Until it has satellites the plotter shows the last fix, Fri 18:10': 'Пока нет спутников, плоттер показывает последний фикс, пт 18:10',
  'Wait for a lock, then check the boat sits on its berth': 'Дождитесь фикса и проверьте, что яхта стоит у своего причала',
  'stale fix, Fri 18:10': 'старый фикс, пт 18:10', 'the boat: on its berth': 'яхта: у своего причала',
  N: 'С', You: 'Вы', 'Northern hemisphere': 'Северное полушарие', 'Depths in metres below chart datum': 'Глубины в метрах от нуля глубин',
  'You: 2 M due south of the light': 'Вы: 2 мили к югу от маяка',
  // plans
  'Depth over the shoal at 14:00': 'Глубина над мелью в 14:00', 'Charted 1.5 m + height of tide 1.2 m = 2.7 m of water': 'По карте 1,5 м + высота прилива 1,2 м = 2,7 м воды',
  'Draft 1.9 m: about 0.8 m under the keel': 'Осадка 1,9 м: под килем около 0,8 м', '1.5 + 1.2 = 2.7 m': '1,5 + 1,2 = 2,7 м',
  'Three bearings · the cocked hat': 'Три пеленга · треугольник погрешностей', 'A small triangle: you are inside it': 'Маленький треугольник: вы внутри него',
  'Take the corner nearest danger as your position': 'За место берите вершину, ближайшую к опасности', 'cocked hat': 'треуг. погрешностей',
  'Stern-to · when to drop the anchor': 'Кормой к причалу · когда отдать якорь', 'Drop about 3–4 boat lengths out, already reversing': 'Отдайте якорь в 3–4 корпусах от причала, уже на заднем ходу',
  'Pay out chain as you go astern, then snug it up': 'Травите цепь на заднем ходу, затем выберите слабину', 'drop here': 'отдать здесь', '3–4 boat lengths': '3–4 корпуса',
  'Crossing a traffic separation scheme': 'Пересечение системы разделения движения', 'Cross on a heading at right angles to the traffic flow': 'Пересекайте курсом под прямым углом к потоку',
  'The stream sets you east: keep the heading square': 'Течение сносит на восток: курс всё равно под прямым углом', 'heading 000°': 'курс 000°', 'track over ground': 'путь над грунтом',
  'Joining a traffic lane': 'Вход в полосу движения', 'Join at the end of the lane, or from the side at a small angle': 'Входите с конца полосы или сбоку под малым углом',
  'Then follow the flow: this lane runs east': 'Затем идите по потоку: эта полоса — на восток', 'small angle': 'под малым углом', 'at the end': 'с конца полосы',
  'Separation zone · keep out': 'Разделительная зона · не входить', 'Enter the zone only to cross, join, leave or in an emergency': 'В зону — только чтобы пересечь, войти, выйти или при аварии',
  'Bound east: follow the eastbound lane': 'Курс на восток: идите по полосе на восток', 'not along the zone': 'не вдоль зоны', 'follow the eastbound lane': 'по полосе на восток',
  'Traffic lanes · go with the flow': 'Полосы движения · по потоку', 'In a lane, go in the general direction of the traffic flow': 'В полосе идите в общем направлении потока',
  'This lane runs east: heading 270° is the wrong way': 'Эта полоса — на восток: курс 270° против потока', 'against the flow': 'против потока',
  'The end of a scheme': 'Конец системы разделения', 'Where a scheme ends, ships change course and converge': 'В конце системы суда меняют курс и сходятся',
  'Navigate with particular caution, or keep well clear': 'Будьте особенно осторожны или держитесь подальше', 'ships alter course here': 'здесь суда меняют курс',
  'Crossing under sail': 'Пересечение под парусом', "Wind from the north: you can't sail across at right angles": 'Ветер северный: под прямым углом под парусом не пройти',
  'Motor-sail to hold a heading near 90° to the lanes': 'Идите под мотором и парусами курсом около 90° к полосам', 'motor-sail · heading 000°': 'мотор и паруса · курс 000°', 'Wind N': 'Ветер С',
  'Latitude · read it off the side of the chart': 'Широта · по боковой рамке карты', 'The parallels are 10′ apart: the boat is three-quarters up': 'Параллели через 10′: яхта на трёх четвертях вверх',
  '37°40′ + 7.5′ = 37°47.5′ N': '37°40′ + 7,5′ = 37°47,5′ N', '2.5′': '2,5′', '7.5′': '7,5′', '37°47.5′ N': '37°47,5′ N',
  'Latitude by distance run north': 'Широта по плаванию на север', 'Due north, one mile = one minute of latitude': 'Строго на север одна миля = одна минута широты',
  '36°50.0′ + 12.0′ = 37°02.0′ N': '36°50,0′ + 12,0′ = 37°02,0′ N', '36°50.0′ N': '36°50,0′ N', '37°02.0′ N': '37°02,0′ N', '12 M': '12 миль',
  'A drying rock at 10:00': 'Осыхающая скала в 10:00', 'Underlined 1.5: the rock dries 1.5 m above chart datum': 'Подчёркнуто 1,5: скала осыхает на 1,5 м выше нуля глубин',
  'Tide 0.6 m: it shows 1.5 − 0.6 = 0.9 m above the water': 'Прилив 0,6 м: над водой 1,5 − 0,6 = 0,9 м', 'shows 0.9 m': '0,9 м над водой',
  'Water over a drying patch at 15:30': 'Вода над осыхающей банкой в 15:30', 'Underlined 0.4: the patch dries 0.4 m above chart datum': 'Подчёркнуто 0,4: банка осыхает на 0,4 м выше нуля глубин',
  'Tide 1.6 m: water over it 1.6 − 0.4 = 1.2 m': 'Прилив 1,6 м: над ней 1,6 − 0,4 = 1,2 м воды', '1.6 − 0.4 = 1.2 m': '1,6 − 0,4 = 1,2 м',
  'Checking the compass on a transit': 'Проверка компаса на створе', 'Transit 315°T − variation 3°E = 312°M': 'Створ ИК 315° − склонение 3°E = МК 312°',
  'Compass reads 317°, 5° more: deviation 5°W': 'Компас 317°, на 5° больше: девиация 5°W', '312°M · compass 317°': 'МК 312° · компас 317°',
  'Choosing objects for a fix': 'Выбор ориентиров для обсервации', 'A, C and D: near you and well spread round you': 'A, C и D: недалеко и хорошо разнесены вокруг',
  'B lies behind A on the same line: it adds nothing': 'B за A на той же линии: ничего не добавляет', 'B: same line as A': 'B: та же линия, что A',
  'The order of the bearings': 'Порядок пеленгов', 'Ahead and astern (P, R) change slowly: take them first': 'Впереди и позади (P, R) пеленг меняется медленно: их первыми',
  'On the beam (Q) it changes fastest: take it last': 'На траверзе (Q) быстрее всего: его последним',
  'A large cocked hat': 'Большой треугольник погрешностей', 'A large triangle means an error in a bearing': 'Большой треугольник — ошибка в пеленге',
  'Re-take them; till then, use the corner nearest the rocks': 'Возьмите пеленги заново; пока — вершина ближе к скалам', 'assume this corner': 'считайте место здесь',
  'Clearing line · church less than 060°T': 'Ограждающий пеленг · церковь меньше 060°', 'South of the line the church bears less than 060°T': 'Южнее линии ИП церкви меньше 060°',
  'More than 060°: you are standing into danger': 'Больше 060°: вы идёте на опасность', 'church < 060°: safe': 'церковь < 060°: безопасно', 'church > 060°: reef side': 'церковь > 060°: сторона рифа',
  'A bearing and a sounding': 'Пеленг и глубина', 'The 20 m sounding puts you on the 20 m contour': 'Глубина 20 м ставит вас на изобату 20 м',
  'Where it meets the bearing: a rough fix': 'Пересечение с пеленгом — приблизительное место', 'rough fix': 'примерное место', '20 m contour': 'изобата 20 м',
  'One bearing: a position line': 'Один пеленг — линия положения', 'One bearing gives one position line, not a fix': 'Один пеленг даёт линию положения, а не место',
  'Cross it with a second line to fix your position': 'Для обсервации нужна вторая линия', 'you are somewhere on it': 'вы где-то на ней',
  'Estimated position at 11:00': 'Счислимое место в 11:00', 'Course 090°T, log 6.0 M → DR': 'ИК 090°, лаг 6,0 мили → DR', 'Tide 180°T 1.5 kn for the hour → EP': 'Течение 180° 1,5 уз за час → EP',
  '6 M by log': '6 миль по лагу', 'tide 1.5 M': 'течение 1,5 мили', DR: 'DR', EP: 'EP',
  'Dead reckoning at 15:30': 'Счисление на 15:30', '14:00 to 15:30 is 1.5 h × 4.0 kn = 6.0 M': 'С 14:00 до 15:30: 1,5 ч × 4,0 уз = 6,0 мили',
  'DR: 6.0 M along 270°T from the fix; no tide in a DR': 'DR: 6,0 мили по 270° от обсервации, без течения', '6.0 M': '6,0 мили', '15:30': '15:30',
  'Course to steer across the stream': 'Курс с учётом течения', 'One hour: tide 2 M south, then 6 M to cut the track': 'За час: течение 2 мили на юг, затем 6 миль до линии пути',
  'Steer about 070°T, 20° up into the stream': 'Держите около 070°, на 20° против течения', 'tide 2 M': 'течение 2 мили', 'steer 070°T': 'держать 070°',
  'Rounding a breakwater head': 'Огибание оконечности мола', 'Rubble and shoals lie off breakwater heads': 'У оконечности мола — камни и мели',
  'Round it wide, then turn in': 'Обходите широко, затем поворачивайте', 'shoal off the head': 'мель у оконечности',
  'Passing a west cardinal': 'Обход западного знака', 'West cardinal: the safe water is to the west': 'Западный знак: безопасная вода к западу',
  'Alter to port and leave it to starboard': 'Подверните влево и оставьте знак справа', 'pass west': 'проходите западнее',
  'Passing a north cardinal': 'Обход северного знака', 'North cardinal: the safe water is to the north': 'Северный знак: безопасная вода к северу',
  'Alter to starboard and leave it to port': 'Подверните вправо и оставьте знак слева', 'pass north': 'проходите севернее',
  'Two cardinals, one shoal': 'Два кардинальных знака, одна мель', 'Safe water: north of the N mark, south of the S mark': 'Безопасно: севернее северного, южнее южного знака',
  'Never pass between them': 'Никогда не проходите между ними', 'shoal between them': 'между ними мель',
  'Swinging to a north wind': 'Разворот на северный ветер', 'Wind N: you lie south of the anchor, 35 m of chain away': 'Ветер С: яхта встанет к югу от якоря, на 35 м цепи',
  'That is on the 1.2 m shoal: re-anchor further north': 'Это мель 1,2 м: переставьте якорь севернее', '1.2 m: aground': '1,2 м: на мели', 're-anchor further north': 'переставить якорь севернее',
  'Swinging or dragging?': 'Рыскание или дрейф якоря?', 'Swinging draws an arc round the anchor': 'Рыскание рисует дугу вокруг якоря',
  'A straight line downwind (SE): the anchor is dragging': 'Прямая по ветру (на ЮВ): якорь ползёт', 'earlier: swinging': 'раньше: рыскание', 'now: dragging': 'сейчас: якорь ползёт', 'Wind NW': 'Ветер СЗ',
  'Swing room when the wind goes west': 'Место для разворота при западном ветре', 'Chain 40 m, depth + bow 6 m: about 39.5 m along the bottom': 'Цепь 40 м, глубина + нос 6 м: по грунту около 39,5 м',
  '+ boat 13 m ≈ 52 m of swing: the rock at 45 m is inside it': '+ яхта 13 м ≈ 52 м: камень в 45 м внутри круга', '≈ 52 m': '≈ 52 м', 'Wind W': 'Ветер З',
  'Position from a landmark': 'Место от ориентира', 'Give the true bearing FROM the landmark, then the distance': 'Называйте истинный пеленг ОТ ориентира, затем дистанцию',
  '"180 degrees from Cape Sounion light, 2 miles"': '«180 градусов от маяка Сунион, 2 мили»', '180° from the light, 2 miles': '180° от маяка, 2 мили',
  // lights
  'On the chart': 'На карте', 'What the chart description says': 'Что значит описание огня', 'flashing': 'проблесковый', 'period 5 s': 'период 5 с', 'height 18 m': 'высота 18 м', 'range 12 M': 'дальность 12 миль',
  'One white flash every 5 seconds': 'Один белый проблеск каждые 5 секунд', 'No colour letter: the light is white': 'Без буквы цвета — огонь белый', 'Fl 5s': 'Fl 5s',
  '2 eclipses': '2 затмения', 'period 8 s': 'период 8 с', 'Mostly on, with two short eclipses every 8 s': 'Горит почти всё время, два коротких затмения за 8 с',
  'Occulting: the light is on longer than it is off': 'Затмевающийся: свет дольше темноты', 'Oc(2) 8s': 'Oc(2) 8s',
  '3 flashes': '3 проблеска', 'white, red': 'белый, красный', 'period 15 s': 'период 15 с', 'height 23 m': 'высота 23 м', 'range 18 / 15 M': 'дальность 18 / 15 миль',
  '23m: the height of the light above sea level': '23m: высота огня над уровнем моря', 'The higher the light, the further off it is seen': 'Чем выше огонь, тем дальше его видно',
  '18/15M: nominal range, 18 M white, 15 M red': '18/15M: номинальная дальность, белый 18, красный 15 миль', 'The red is weaker, so it is seen less far': 'Красный слабее, его видно ближе',
  'alternating': 'переменный', 'period 10 s': 'период 10 с', 'Al WR 10s': 'Al WR 10s', 'Al WR: white and red in turn, wherever you are': 'Al WR: белый и красный по очереди, где бы вы ни были',
  'A sector light changes colour only with your bearing': 'Секторный огонь меняет цвет только с пеленгом',
  '2 flashes': '2 проблеска', 'height 15 m': 'высота 15 м', 'range 10 M': 'дальность 10 миль', 'no colour letter: white': 'нет буквы цвета: белый',
  'No colour letter in the description: the light is white': 'Нет буквы цвета в описании — огонь белый', 'Light A, B or C?': 'Огонь A, B или C?', 'Timing the light': 'Засекаем огонь',
  '3 flashes, then dark, every 15 s: Fl(3) 15s, light B': '3 проблеска, затем темно, каждые 15 с: Fl(3) 15s — огонь B', 'Fl 5s and Fl(2) 10s give one and two flashes': 'Fl 5s и Fl(2) 10s дают один и два проблеска',
  'Steady, briefly dark every 10 s: occulting, light B': 'Горит, на миг гаснет каждые 10 с: затмевающийся — огонь B', 'Fl: mostly dark · Iso: equal light and dark': 'Fl: в основном темно · Iso: свет и темнота поровну',
  // isobars plans
  'Isobars packed tight': 'Тесные изобары', 'Close isobars: a steep pressure gradient': 'Тесные изобары: большой барический градиент',
  'Strong wind: stay in port or reef early': 'Сильный ветер: оставайтесь в порту или рифьтесь заранее', 'strong wind': 'сильный ветер',
  'Wind round a low': 'Ветер вокруг циклона', 'Anticlockwise round a low, angled in towards it': 'Против часовой вокруг циклона, с отклонением внутрь',
  'Low to your NW: wind from the SW, veering as it passes': 'Циклон к СЗ: ветер ЮЗ, заходит по мере прохода', 'wind SW': 'ветер ЮЗ',
  'The meltemi (Aegean, July)': 'Мельтеми (Эгейское море, июль)', 'High to the NW, heat low over Anatolia to the E': 'Антициклон к СЗ, термический циклон над Анатолией к В',
  'Steady N wind, F5–7, strongest in the afternoon': 'Устойчивый северный ветер 5–7 баллов, сильнее всего после полудня', 'meltemi N 6–7': 'мельтеми С 6–7',
  'Wind round a high': 'Ветер вокруг антициклона', 'Clockwise round a high, angled out of it': 'По часовой вокруг антициклона, с отклонением наружу',
  'East of the high: the wind comes from the north': 'К востоку от антициклона ветер дует с севера', 'wind N': 'ветер С',
  'SW of the low: the wind comes from the north-west': 'К ЮЗ от циклона ветер дует с северо-запада', 'wind NW': 'ветер СЗ',
  'Surface wind at sea': 'Приземный ветер над морем', 'Nearly along the isobars, angled in towards the low': 'Почти вдоль изобар, с отклонением к циклону',
  'At sea, friction turns it 10–15° across them': 'Над морем трение отклоняет его на 10–15°', '10–15° in': 'внутрь на 10–15°',
};
for (let t = 0; t <= 30; t++) RU[`${t} s`] = `${t} с`;
Object.assign(RU, { L: 'Н', H: 'В' });

/* the light plans */
const FLW = (t, d = 0.6) => [t, d, 'w'];
const LIGHTPLAN = {
  'bs-584': () => lightCard({ title: 'What the chart description says', key: ['One white flash every 5 seconds', 'No colour letter: the light is white'],
    tokens: [['Fl', 'flashing'], ['5s', 'period 5 s'], ['18m', 'height 18 m'], ['12M', 'range 12 M']], hi: [0, 1], rhythm: { label: 'Fl 5s', T: 15, flashes: repeat(5, 15, [FLW(0.5)]) } }),
  'bs-585': () => lightCard({ title: 'What the chart description says', key: ['Mostly on, with two short eclipses every 8 s', 'Occulting: the light is on longer than it is off'],
    tokens: [['Oc(2)', '2 eclipses'], ['8s', 'period 8 s']], hi: [0, 1], rhythm: { label: 'Oc(2) 8s', T: 16, every: 4, flashes: repeat(8, 16, [[0, 4.5, 'w'], [5.5, 1, 'w'], [7.5, 0.5, 'w']]) } }),
  'bs-587': () => lightCard({ title: 'What the chart description says', key: ['23m: the height of the light above sea level', 'The higher the light, the further off it is seen'],
    tokens: [['Fl(3)', '3 flashes'], ['WR', 'white, red'], ['15s', 'period 15 s'], ['23m', 'height 23 m'], ['18/15M', 'range 18 / 15 M']], hi: [3] }),
  'bs-588': () => lightCard({ title: 'What the chart description says', key: ['18/15M: nominal range, 18 M white, 15 M red', 'The red is weaker, so it is seen less far'],
    tokens: [['Fl(3)', '3 flashes'], ['WR', 'white, red'], ['15s', 'period 15 s'], ['23m', 'height 23 m'], ['18/15M', 'range 18 / 15 M']], hi: [1, 4] }),
  'bs-597': () => lightCard({ title: 'What the chart description says', key: ['Al WR: white and red in turn, wherever you are', 'A sector light changes colour only with your bearing'],
    tokens: [['Al', 'alternating'], ['WR', 'white, red'], ['10s', 'period 10 s']], hi: [0, 1], rhythm: { label: 'Al WR 10s', T: 20, flashes: repeat(10, 20, [[0, 4.6, 'w'], [5, 4.6, 'r']]) } }),
  'bs-598': () => lightCard({ title: 'What the chart description says', key: ['No colour letter in the description: the light is white'],
    tokens: [['Fl(2)', '2 flashes'], ['10s', 'period 10 s'], ['15m', 'height 15 m'], ['10M', 'range 10 M']], hi: [], note: 'no colour letter: white' }),
  'bs-589': () => rhythmRows({ title: 'Timing the light', key: ['3 flashes, then dark, every 15 s: Fl(3) 15s, light B', 'Fl 5s and Fl(2) 10s give one and two flashes'], T: 30,
    rows: [{ label: 'A  Fl 5s', flashes: repeat(5, 30, [FLW(0)]) }, { label: 'B  Fl(3) 15s', hi: true, flashes: repeat(15, 30, [FLW(0), FLW(1.6), FLW(3.2)]) }, { label: 'C  Fl(2) 10s', flashes: repeat(10, 30, [FLW(0), FLW(1.6)]) }] }),
  'bs-590': () => rhythmRows({ title: 'Light A, B or C?', key: ['Steady, briefly dark every 10 s: occulting, light B', 'Fl: mostly dark · Iso: equal light and dark'], T: 30,
    rows: [{ label: 'A  Fl 10s', flashes: repeat(10, 30, [[0, 1, 'w']]) }, { label: 'B  Oc 10s', hi: true, flashes: repeat(10, 30, [[0, 8.5, 'w']]) }, { label: 'C  Iso 10s', flashes: repeat(10, 30, [[0, 5, 'w']]) }] }),
};

/* ---------------- run ---------------- */
const report = { q: 0, plan: 0, missing: [] };
function emit(e, q, plan) {
  const dir = join(DIR, e.id); mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'q.json'), JSON.stringify({ svg: q }) + '\n'); report.q++;
  const pp = join(dir, 'plan.json'); if (plan) { writeFileSync(pp, JSON.stringify({ svg: plan }) + '\n'); report.plan++; } else if (existsSync(pp)) rmSync(pp);
  const ru = {};
  for (const s of [...USED].sort()) { const r = ruOf(s); if (r === s && /[A-Za-z]/.test(s) && !/^[A-D]$|^[PQR]$|^(DR|EP|ODAS|Foul|S|M|R|Sn|Wd|S\.Sh|25 Wk|\+ PA|Fl|Oc|Iso|Al|WR|\d+[sm]|\d+M|Fl\(\d\)|Oc\(\d\)|\d+\/\d+M|[A-C]  .*|Fl .*|Oc.*|Al WR.*|\d.*'N|37°.*)$/.test(s)) report.missing.push(`${e.id}: ${s}`); ru[s] = r; }
  writeFileSync(join(dir, 'ru.json'), JSON.stringify(ru, null, 1) + '\n');
}
const only = ARGS.filter((a, i) => a !== '--level' && ARGS[i - 1] !== '--level')[0];
const list = name => existsSync(join(DIR, name)) ? JSON.parse(readFileSync(join(DIR, name), 'utf8')) : [];
let CUR = '';
for (const e of list('chart.json')) {
  if (only && e.id !== only) continue;
  CUR = e.id; const f = e.figure, cfg = CFG[e.id] || {}; USED = new Set(); RUMAP = e.ru || {};
  const q = frame({ title: titleOf(f), key: keyOf(f, e.id), draw: chartDraw(f, cfg), avoid: chartAvoid(f) });
  let plan = null;
  if (PLAN[e.id]) { const p = PLAN[e.id](f); plan = frame({ title: p.title, key: p.key, draw: chartDraw(f, { ...cfg, noTrack: p.noTrack, ...(p.cfg || {}) }, p), avoid: chartAvoid(f), cols: 1 }); }
  else if (LIGHTPLAN[e.id]) plan = LIGHTPLAN[e.id]();
  emit(e, q, plan);
}
for (const e of list('isobars.json')) {
  if (only && e.id !== only) continue;
  CUR = e.id; const f = e.figure; USED = new Set(); RUMAP = e.ru || {};
  const sec = { ...(ISOSECOND[e.id] ? { second: ISOSECOND[e.id] } : {}), youAt: YOUAT[e.id] };
  const avoid = [[ICX, ICY], f.boat, [ICX - 140, ICY], [ICX, ICY - 110]];
  const q = frame({ title: f.hemisphere || 'Northern hemisphere', key: f.note ? [f.note] : [], draw: isoDraw(f, sec), avoid, cols: 1 });
  let plan = null; if (ISOPLAN[e.id]) { const p = ISOPLAN[e.id](f); plan = frame({ title: p.title, key: p.key, draw: isoDraw(f, { ...sec, ...p, youAt: p.youAt || sec.youAt }), avoid, cols: 1 }); }
  emit(e, q, plan);
}
console.log(`q.json ${report.q}, plan.json ${report.plan}`);
if (report.missing.length) console.log('no Russian for:\n  ' + report.missing.join('\n  '));
