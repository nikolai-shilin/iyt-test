/* IYT Test figures: every drawn question is a small JSON spec rendered to SVG here (one renderer per type).
   320×200 viewBox, theme tokens for ink/muted/bg; fixed colours only for lights and buoys (red, green, yellow, white).
   Usage: figSvg(spec) → svg string; paintFigures(root) fills every [data-fig] element.
   Built-in labels go through ft(); fill FIG_TEXT ({ 'You': 'Вы', … }) to draw them in another language. */
const FIG_TEXT = {};
const ft = (s) => FIG_TEXT[s] ?? s;

const FIG = {};
const NS = (w = 320, h = 200, extra = '', y0 = 0) => `<svg viewBox="0 ${y0} ${w} ${h}" width="100%" preserveAspectRatio="xMidYMid meet" font-family="Carlito, Arial, sans-serif" ${extra}>`;
const RAD = Math.PI / 180;
const pol = (cx, cy, r, deg) => [cx + r * Math.sin(deg * RAD), cy - r * Math.cos(deg * RAD)];
const txt = (x, y, s, o = {}) => `<text x="${x}" y="${y}" font-size="${o.s || 11}" font-weight="${o.w || 700}" fill="${o.f || 'var(--muted)'}" text-anchor="${o.a || 'middle'}" ${o.extra || ''}>${s}</text>`;
// The colours of real things (marks, lights, shapes, flags) are fixed: black is black in the night theme too.
const COL = { r: '#e0251b', g: '#1aa34a', w: '#ffffff', y: '#ffa800', k: '#000000' };
// Figures of things whose colours carry the meaning are drawn as seen by day in either theme: their box gets the
// class "day" (flows.css), which sets the day tokens for everything inside, as "night" does for the lights.
const FIG_DAY = new Set(['buoy', 'dayshape', 'flag', 'radio']);

/* boat silhouette, top view, pointing up (north) at 0,0; length ~ 44 */
function boat(x, y, hdg, o = {}) {
  const c = o.sail ? 'var(--bg)' : 'var(--ink)', s = o.scale || 1;
  const body = `<path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="${o.fill || c}" stroke="var(--ink)" stroke-width="2" stroke-linejoin="round"/>`;
  const sail = o.sail ? `<path d="M0 -14 L0 10 L ${o.boom || -14} 10 Z" fill="var(--ink)" opacity=".85"/>` : '';
  const dot = o.you ? `<circle cx="0" cy="-2" r="3" fill="var(--accent)"/>` : '';
  const lab = o.label ? `<text x="0" y="${o.labelY || 38}" font-size="11" font-weight="700" fill="var(--ink)" text-anchor="middle" transform="rotate(${-hdg})">${o.label}</text>` : '';
  return `<g transform="translate(${x} ${y}) rotate(${hdg}) scale(${s})">${body}${sail}${dot}${o.label ? `<g transform="scale(${1 / s})">${lab}</g>` : ''}</g>`;
}
/* arrow from (x1,y1) to (x2,y2) */
function arrow(x1, y1, x2, y2, o = {}) {
  const c = o.c || 'var(--muted)', w = o.w || 2;
  const a = Math.atan2(y2 - y1, x2 - x1), h = 7;
  const p1 = [x2 - h * Math.cos(a - .5), y2 - h * Math.sin(a - .5)], p2 = [x2 - h * Math.cos(a + .5), y2 - h * Math.sin(a + .5)];
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${o.dash ? 'stroke-dasharray="5 4"' : ''}/><path d="M${x2} ${y2} L${p1[0]} ${p1[1]} L${p2[0]} ${p2[1]} Z" fill="${c}"/>`;
}
/* wind arrow in a corner: wind FROM direction deg */
function windArrow(deg, x = 290, y = 34) {
  const [ax, ay] = pol(x, y, 22, deg), [bx, by] = pol(x, y, 22, deg + 180);
  return `<g>${arrow(ax, ay, bx, by, { c: 'var(--accent)', w: 2.5 })}${txt(x, y + 40, ft('wind'), { s: 10, f: 'var(--accent)' })}</g>`;
}
function compassN(x = 30, y = 30) { return `<g>${arrow(x, y + 14, x, y - 14, { c: 'var(--muted)' })}${txt(x, y - 18, ft('N'), { s: 11 })}</g>`; }

/* ---------- encounter: own boat centre, other vessel by relative bearing; headings; optional wind ---------- */
FIG.encounter = f => {
  const cx = 160, cy = 108, you = f.you || {}, oth = f.other || {};
  const yh = you.hdg ?? 0;
  const solo = (oth.dist ?? 80) < 1;  /* dist 0: a single-boat picture, no other vessel */
  const [ox, oy] = pol(cx, cy, oth.dist ?? 80, yh + (oth.bearing ?? 45));
  // a vessel near the top or bottom edge, with its label 38 below its centre, would be cut off: grow the frame
  const otherLabel = !solo && (oth.label || ft('Other'));
  const bottom = Math.max(cy + 44, solo ? 0 : oy + (otherLabel ? 44 : 26));
  const top = solo ? 0 : Math.min(0, Math.floor(oy - 28));
  const H = Math.max(200, Math.ceil(bottom + (f.note ? 16 : 4)));
  let s = NS(320, H - top, '', top);
  s += compassN();
  if (f.wind != null) s += windArrow(f.wind);
  if (f.bearingLine) s += `<line x1="${cx}" y1="${cy}" x2="${ox}" y2="${oy}" stroke="var(--tag-line)" stroke-width="2" stroke-dasharray="4 5"/>`;
  const hl = (x, y, hdg, L) => { const [tx, ty] = pol(x, y, L, hdg); return arrow(x, y, tx, ty, { c: 'var(--muted)', dash: true }); };
  s += hl(cx, cy, yh, 58) + (solo ? '' : hl(ox, oy, oth.hdg ?? 180, 58));
  s += boat(cx, cy, yh, { sail: you.sail, boom: you.boom, you: true, label: you.label || ft('You') });
  if (!solo) s += boat(ox, oy, oth.hdg ?? 180, { sail: oth.sail, boom: oth.boom, label: oth.label || ft('Other'), scale: oth.scale || 1 });
  if (f.note) s += txt(160, H - 8, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- lights: a night view; lights as glowing dots on a 320×200 grid; optional faint hull hint ---------- */
FIG.lights = f => {
  let s = NS(320, 200, 'style="background:#07101a;border-radius:16px"');
  s += `<rect width="320" height="200" fill="#07101a"/><line x1="0" y1="150" x2="320" y2="150" stroke="#14263a" stroke-width="1"/>`;
  if (f.hull) s += `<path d="${f.hull}" fill="#0c1a28"/>`;
  (f.lights || []).forEach(l => {
    const r = l.r || 6, c = COL[l.c] || l.c;
    s += `<circle cx="${l.x}" cy="${l.y}" r="${r * 2.2}" fill="${c}" opacity=".18"/><circle cx="${l.x}" cy="${l.y}" r="${r}" fill="${c}"/>`;
    if (l.t) s += txt(l.x + r * 2.2 + 4, l.y + 4, l.t, { s: 10, f: '#8aa0b8', w: 400, a: 'start' });
  });
  s += txt(160, 188, f.note || ft('Night · lights seen ahead'), { s: 11, f: '#8aa0b8', w: 400 });
  return s + '</svg>';
};

/* ---------- buoy: IALA marks (region A unless f.region === 'B') with topmark, optional night rhythm ---------- */
FIG.buoy = f => {
  const k = f.kind, B = f.region === 'B';
  const bands = { // list of [colour, height share]
    'card-n': [['k', .5], ['y', .5]], 'card-s': [['y', .5], ['k', .5]], 'card-e': [['k', .33], ['y', .34], ['k', .33]], 'card-w': [['y', .33], ['k', .34], ['y', .33]],
    'lat-port': [[B ? 'g' : 'r', 1]], 'lat-stbd': [[B ? 'r' : 'g', 1]], 'iso': [['k', .35], ['r', .3], ['k', .35]], 'safe': 'stripes', 'special': [['y', 1]], 'wreck': 'wreck',
  }[k] || [['k', 1]];
  const x = 128, top = 70, w = 48, h = 90;
  let s = NS() + `<path d="M10 178c16-10 32-10 48 0s32 10 48 0 32-10 48 0 32 10 48 0 32-10 48 0 32 10 48 0" fill="none" stroke="var(--faint)" stroke-width="2" stroke-linecap="round"/>`;
  // body
  const shape = k === 'lat-port' ? 'can' : k === 'lat-stbd' ? 'cone' : k === 'safe' ? 'sphere' : 'pillar';
  if (shape === 'can') s += `<rect x="${x - w / 2}" y="${top}" width="${w}" height="${h}" fill="${COL[bands[0][0]]}"/>`;
  else if (shape === 'cone') s += `<path d="M${x - w / 2} ${top + h} L${x} ${top} L${x + w / 2} ${top + h} Z" fill="${COL[bands[0][0]]}"/>`;
  else if (shape === 'sphere') s += `<clipPath id="sp"><circle cx="${x}" cy="${top + 45}" r="40"/></clipPath><g clip-path="url(#sp)">${[0, 1, 2, 3, 4, 5, 6, 7].map(i => `<rect x="${x - 40 + i * 10}" y="${top}" width="10" height="90" fill="${i % 2 ? '#fff' : COL.r}" stroke="var(--line)" stroke-width=".5"/>`).join('')}</g><circle cx="${x}" cy="${top + 45}" r="40" fill="none" stroke="var(--ink)" stroke-width="1"/>`;
  else if (bands === 'wreck') s += `<rect x="${x - w / 2}" y="${top}" width="${w}" height="${h}" fill="#2a5bd7"/>${[0, 1, 2, 3].map(i => `<rect x="${x - w / 2 + i * 12}" y="${top}" width="12" height="${h}" fill="${i % 2 ? COL.y : '#2a5bd7'}"/>`).join('')}`;
  else { let y = top; bands.forEach(([c, p]) => { s += `<rect x="${x - w / 2}" y="${y}" width="${w}" height="${h * p}" fill="${COL[c]}"/>`; y += h * p; }); }
  // topmark
  const cone = (cy, up) => `<path d="M${x - 10} ${up ? cy + 10 : cy - 10} L${x} ${up ? cy - 6 : cy + 6} L${x + 10} ${up ? cy + 10 : cy - 10} Z" fill="var(--ink)"/>`;
  const ball = cy => `<circle cx="${x}" cy="${cy}" r="8" fill="${k === 'safe' ? COL.r : 'var(--ink)'}"/>`;
  const tm = { 'card-n': cone(56, 1) + cone(38, 1), 'card-s': cone(56, 0) + cone(38, 0), 'card-e': cone(40, 1) + cone(58, 0), 'card-w': cone(38, 0) + cone(58, 1),
    'iso': ball(58) + ball(40), 'safe': ball(22), 'special': `<path d="M${x - 9} ${42} L${x + 9} ${60} M${x + 9} ${42} L${x - 9} ${60}" stroke="${COL.y}" stroke-width="4" stroke-linecap="round"/>`,
    'lat-port': f.topmark ? `<rect x="${x - 8}" y="${top - 18}" width="16" height="16" fill="${COL[bands[0][0]]}"/>` : '', 'lat-stbd': f.topmark ? `<path d="M${x - 9} ${top - 2} L${x} ${top - 20} L${x + 9} ${top - 2} Z" fill="${COL[bands[0][0]]}"/>` : '', 'wreck': `<path d="M${x - 9} 42 L${x + 9} 60 M${x + 9} 42 L${x - 9} 60" stroke="${COL.y}" stroke-width="4" stroke-linecap="round"/>` }[k] || '';
  s += `<line x1="${x}" y1="${top}" x2="${x}" y2="${k === 'safe' ? 30 : 32}" stroke="var(--ink)" stroke-width="2"/>` + tm;
  // light + rhythm panel on the right
  if (f.rhythm) {
    const lc = { 'lat-port': B ? COL.g : COL.r, 'lat-stbd': B ? COL.r : COL.g, 'special': COL.y, 'wreck': COL.y }[k] || '#fff';
    s += `<rect x="196" y="60" width="114" height="80" rx="14" fill="#07101a"/><circle cx="222" cy="92" r="9" fill="${lc}"/><circle cx="222" cy="92" r="18" fill="${lc}" opacity=".18"/>`;
    if (k === 'wreck') s += `<path d="M222 83 A9 9 0 0 0 222 101 Z" fill="#2a5bd7"/>`;  /* alternating blue/yellow: half and half */
    s += txt(236, 88, ft('Light at night'), { s: 10, f: '#8aa0b8', w: 400, a: 'start' }) + txt(236, 104, f.rhythm, { s: 13, f: '#fff', a: 'start' });
    if (f.rhythmNote) s += txt(253, 128, f.rhythmNote, { s: 10, f: '#8aa0b8', w: 400 });
  }
  if (f.note) s += txt(160, 194, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- compass: rose with true north, magnetic north offset by variation; a course line ---------- */
FIG.compass = f => {
  const cx = 110, cy = 100, r = 72, v = f.variation || 0; // variation: +E, −W (degrees)
  let s = NS() + `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--tag-line)" stroke-width="2"/>`;
  for (let d = 0; d < 360; d += 30) { const [a, b] = pol(cx, cy, r, d), [c, e] = pol(cx, cy, r - (d % 90 ? 6 : 12), d); s += `<line x1="${a}" y1="${b}" x2="${c}" y2="${e}" stroke="var(--muted)" stroke-width="2"/>`; }
  const [tx, ty] = pol(cx, cy, r + 14, 0); s += txt(tx + (v < 0 ? 8 : -8), ty + 4, ft('N (true)'), { s: 11, a: v < 0 ? 'start' : 'end' });
  const [mx, my] = pol(cx, cy, r - 2, v); s += arrow(cx, cy, mx, my, { c: 'var(--accent)', w: 2.5 });
  const [lx, ly] = pol(cx, cy, r + 16, v); s += txt(lx + (v < 0 ? -10 : 10), ly + 4, ft('MN'), { s: 11, f: 'var(--accent)', a: v < 0 ? 'end' : 'start' });
  if (f.course != null) { const [qx, qy] = pol(cx, cy, r - 2, f.course); s += arrow(cx, cy, qx, qy, { c: 'var(--ink)', w: 3 }); }
  s += `<rect x="206" y="52" width="104" height="96" rx="16" fill="var(--band)"/>`;
  s += txt(258, 74, `${ft('Variation')} ${Math.abs(v)}°${ft(v < 0 ? 'W' : 'E')}`, { s: 13, f: 'var(--ink)' });
  if (f.course != null) s += txt(258, 96, `${f.courseLabel || ft('True course')} ${String(f.course).padStart(3, '0')}°`, { s: 12, f: 'var(--ink)', w: 400 });
  if (f.deviation != null) s += txt(258, 116, `${ft('Deviation')} ${Math.abs(f.deviation)}°${ft(f.deviation < 0 ? 'W' : 'E')}`, { s: 12, f: 'var(--ink)', w: 400 });
  if (f.note) s += txt(258, 138, f.note, { s: 10, w: 400 });
  return s + '</svg>';
};

/* ---------- chart: soundings, a drying patch, a track; tide and draft in a panel ---------- */
FIG.chart = f => {
  let s = NS(320, 214) + `<rect width="320" height="200" fill="var(--band)" rx="16"/>`;
  if (f.land) s += `<path d="${f.land}" fill="var(--tag-line)" opacity=".9"/>`;
  (f.depths || []).forEach(d => s += txt(d[0], d[1], d[2], { s: 13, f: 'var(--ink)', w: 400, extra: d[3] ? 'text-decoration="underline"' : '' }));
  (f.marks || []).forEach(m => s += `<circle cx="${m[0]}" cy="${m[1]}" r="5" fill="${COL[m[2]] || 'var(--ink)'}" stroke="var(--ink)" stroke-width="1"/>` + (m[3] ? txt(m[0], m[1] - 9, m[3], { s: 10 }) : ''));
  if (f.track) s += `<path d="${f.track}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-dasharray="7 5"/>`;
  (f.labels || []).forEach(l => s += txt(l[0], l[1], l[2], { s: 11, f: 'var(--muted)', w: 700, a: l[3] || 'middle' }));
  if (f.boat) s += boat(f.boat[0], f.boat[1], f.boat[2], { you: true, scale: .7 });
  if (f.panel) { s += `<rect x="190" y="12" width="118" height="${18 + 18 * f.panel.length}" rx="12" fill="var(--bg)" stroke="var(--line)"/>`; f.panel.forEach((p, i) => s += txt(200, 30 + 18 * i, p, { s: 12, f: 'var(--ink)', w: i ? 400 : 700, a: 'start' })); }
  s += txt(26, 210, f.note || ft('Depths in metres below chart datum'), { s: 10, w: 400, a: 'start' });
  return s + '</svg>';
};

/* ---------- anchor: side view, depth and chain; scope question ---------- */
FIG.anchor = f => {
  const wl = 60, bed = 160, bx = 220;
  let s = NS() + `<rect x="0" y="${wl}" width="320" height="${bed - wl}" fill="var(--band)"/><path d="M0 ${bed} h320 v40 H0z" fill="var(--tag-line)"/>`;
  s += `<path d="M${bx - 42} ${wl - 2} L${bx + 42} ${wl - 2} L${bx + 30} ${wl + 16} L${bx - 30} ${wl + 16} Z" fill="var(--ink)"/><line x1="${bx + 4}" y1="${wl - 2}" x2="${bx + 4}" y2="${wl - 44}" stroke="var(--ink)" stroke-width="3"/>`;
  const ax = 60, ay = bed - 4;
  s += `<path d="M${bx - 40} ${wl + 4} Q ${bx - 60} ${bed - 20} ${ax} ${ay}" fill="none" stroke="var(--ink)" stroke-width="2.5" stroke-dasharray="3 4"/>`;
  s += `<path d="M${ax} ${ay - 14} v16 M${ax - 10} ${ay - 2} q10 10 20 0" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/>`;
  // the depth and the state of tide sit left of the depth line, in open water under the boat (drawn to the right of the
  // line at x 300 they ran off the 320-wide figure)
  s += `<line x1="292" y1="${wl}" x2="292" y2="${bed}" stroke="var(--accent)" stroke-width="2"/>` + txt(286, (wl + bed) / 2 + 4, f.depth, { s: 12, f: 'var(--accent)', a: 'end' });
  if (f.tide) s += txt(286, (wl + bed) / 2 + 20, f.tide, { s: 10, f: 'var(--accent)', a: 'end', w: 400 });
  s += txt(16, 30, f.title || ft('Anchoring'), { s: 13, f: 'var(--ink)', a: 'start' });
  (f.lines || []).forEach((l, i) => s += txt(16, 50 + 16 * i, l, { s: 12, f: 'var(--ink)', a: 'start', w: 400 }));
  if (f.wind != null) s += windArrow(f.wind, 150, 30);
  return s + '</svg>';
};

/* ---------- isobars: a low or high with concentric isobars, a boat, hemisphere note ---------- */
FIG.isobars = f => {
  const cx = 120, cy = 92;
  let s = NS();
  [22, 42, 62, 82].forEach((r, i) => s += `<ellipse cx="${cx}" cy="${cy}" rx="${r * 1.15}" ry="${r}" fill="none" stroke="var(--muted)" stroke-width="${f.tight && i > 1 ? 2.5 : 1.5}"/>`);
  if (f.tight) [96, 108].forEach(r => s += `<ellipse cx="${cx}" cy="${cy}" rx="${r * 1.15}" ry="${r}" fill="none" stroke="var(--muted)" stroke-width="2.5"/>`);
  s += txt(cx, cy + 8, f.center || 'L', { s: 28, f: 'var(--ink)' });
  (f.values || []).forEach((v, i) => s += txt(cx + 8, cy - 30 - i * 24, v, { s: 10, a: 'start', w: 400 }));
  if (f.boat) s += boat(f.boat[0], f.boat[1], f.boat[2] || 0, { you: true, scale: .75 });
  s += txt(300, 24, f.hemisphere || ft('Northern hemisphere'), { s: 11, a: 'end' });
  if (f.note) s += `<rect x="150" y="172" width="160" height="22" rx="11" fill="var(--bg)" opacity=".85"/>` + txt(230, 187, f.note, { s: 10.5, w: 400 });
  return s + '</svg>';
};

/* ---------- sail: own boat heading with the wind; points of sail ---------- */
FIG.sail = f => {
  const cx = 160, cy = 104;
  let s = NS() + compassN() + windArrow(f.wind ?? 0);
  s += `<circle cx="${cx}" cy="${cy}" r="70" fill="none" stroke="var(--tag-line)" stroke-width="1.5" stroke-dasharray="4 5"/>`;
  if (f.nogo) { const a = (f.wind ?? 0), [p1x, p1y] = pol(cx, cy, 70, a - 45), [p2x, p2y] = pol(cx, cy, 70, a + 45); s += `<path d="M${cx} ${cy} L${p1x} ${p1y} A70 70 0 0 1 ${p2x} ${p2y} Z" fill="var(--danger)" opacity=".12"/>`; }
  const rel = ((f.hdg - (f.wind ?? 0)) % 360 + 360) % 360, boom = rel < 180 ? 14 : -14;  /* wind over port (rel < 180) → boom to starboard */
  s += boat(cx, cy, f.hdg, { sail: true, boom, you: true, label: f.label });
  if (f.note) s += txt(160, 194, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- race: a racing situation, top view — wind, boats on their tacks, a mark with its zone, a start line, an obstruction ----------
   { type: 'race', wind: 0, scale: .6, boats: [{ x, y, hdg, label, you }], mark: { x, y, zone: true, label }, line: { x1, y1, x2, y2, label },
     obstruction: { x, y, w, h, label } | { path, label }, track: 'M…', note }
   The sail is drawn on the leeward side for the wind, so the tack can be read from the picture; a dashed arrow shows each heading.
   zone: true draws the three-hull-length circle round the mark. The line runs from the pin (x1, y1) to the committee boat (x2, y2). */
FIG.race = f => {
  const sc = f.scale || .6, wind = f.wind ?? 0, len = 44 * sc;
  let s = NS() + windArrow(wind);
  if (f.obstruction) {
    const o = f.obstruction;
    s += o.path ? `<path d="${o.path}" fill="var(--tag-line)"/>` : `<rect x="${o.x}" y="${o.y}" width="${o.w}" height="${o.h}" rx="8" fill="var(--tag-line)"/>`;
    if (o.label) s += txt(o.lx ?? (o.path ? 160 : o.x + o.w / 2), o.ly ?? (o.path ? 20 : o.y + o.h / 2 + 4), o.label, { s: 10 });
  }
  if (f.track) s += `<path d="${f.track}" fill="none" stroke="var(--tag-line)" stroke-width="2" stroke-dasharray="4 5"/>`;
  if (f.line) {
    const l = f.line;
    s += `<line x1="${l.x1}" y1="${l.y1}" x2="${l.x2}" y2="${l.y2}" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="3 4"/>`;
    s += `<circle cx="${l.x1}" cy="${l.y1}" r="5" fill="${COL.y}" stroke="var(--ink)" stroke-width="1.5"/>` + txt(l.x1, l.y1 + 16, ft('pin'), { s: 9 });
    s += boat(l.x2, l.y2, l.hdg ?? wind, { scale: sc * .9 }) + txt(l.x2, l.y2 + len * .7 + 10, ft('RC'), { s: 9 });
    if (l.label) s += txt((l.x1 + l.x2) / 2, Math.min(l.y1, l.y2) - 8, l.label, { s: 10 });
  }
  if (f.mark) {
    const m = f.mark, r = m.zone === true ? 3 * len : (m.zone || 0);
    if (r) s += `<circle cx="${m.x}" cy="${m.y}" r="${r}" fill="var(--accent)" opacity=".06"/><circle cx="${m.x}" cy="${m.y}" r="${r}" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="4 5"/>` + txt(m.x, Math.max(m.y - r + 12, 14), ft('zone'), { s: 9, f: 'var(--accent)' });
    s += `<circle cx="${m.x}" cy="${m.y}" r="7" fill="${COL.y}" stroke="var(--ink)" stroke-width="2"/>`;
    /* the label goes under the mark, or above it when a boat sits just below */
    const below = (f.boats || []).some(b => Math.abs(b.x - m.x) < 40 && b.y > m.y && b.y - m.y < 45);
    if (m.label) s += txt(m.x, m.y + (m.labelY ?? (below ? -14 : 20)), m.label, { s: 10 });
  }
  (f.boats || []).forEach(b => {
    const hdg = b.hdg ?? 0, rel = ((hdg - wind) % 360 + 360) % 360, boom = rel < 180 ? 14 : -14;
    const [tx, ty] = pol(b.x, b.y, len * 1.4, hdg);
    s += arrow(b.x, b.y, tx, ty, { c: 'var(--muted)', dash: true });
    s += boat(b.x, b.y, hdg, { sail: true, boom, you: !!b.you, scale: b.scale || sc, label: b.label ? ft(b.label) : '', labelY: 34 });
  });
  if (f.note) s += txt(160, 194, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- dayshape: a boat with a day shape hoisted ---------- */
FIG.dayshape = f => {
  let s = NS() + `<path d="M10 150c16-10 32-10 48 0s32 10 48 0 32-10 48 0 32 10 48 0 32-10 48 0 32 10 48 0" fill="none" stroke="var(--faint)" stroke-width="2"/>`;
  s += `<path d="M70 140 L250 140 L232 160 L88 160 Z" fill="var(--ink)"/><line x1="160" y1="140" x2="160" y2="40" stroke="var(--ink)" stroke-width="3"/>`;
  if (f.sail) s += `<path d="M163 44 L163 134 L228 134 Z" fill="var(--band)" stroke="var(--ink)" stroke-width="1.5"/>`;
  const sh = { ball: `<circle cx="160" cy="62" r="12" fill="var(--ink)"/>`, 'cone-down': `<path d="M148 54 L172 54 L160 76 Z" fill="var(--ink)"/>`, 'two-balls': `<circle cx="160" cy="50" r="10" fill="var(--ink)"/><circle cx="160" cy="76" r="10" fill="var(--ink)"/>`,
    'ball-diamond-ball': `<circle cx="160" cy="44" r="8" fill="var(--ink)"/><path d="M160 54 L170 66 L160 78 L150 66 Z" fill="var(--ink)"/><circle cx="160" cy="88" r="8" fill="var(--ink)"/>`, cylinder: `<rect x="150" y="48" width="20" height="30" fill="var(--ink)"/>`, 'two-cones': `<path d="M148 40 L172 40 L160 60 Z" fill="var(--ink)"/><path d="M148 84 L172 84 L160 64 Z" fill="var(--ink)"/>`, 'three-balls': `<circle cx="160" cy="44" r="8" fill="var(--ink)"/><circle cx="160" cy="66" r="8" fill="var(--ink)"/><circle cx="160" cy="88" r="8" fill="var(--ink)"/>` }[f.shape] || '';
  s += sh;
  if (f.note) s += txt(160, 190, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- bay: an anchorage with wind and three candidate spots ---------- */
FIG.bay = f => {
  let s = NS() + `<rect width="320" height="200" fill="var(--band)" rx="16"/>`;
  s += `<path d="${f.land || 'M0 0 H320 V60 C 260 70 230 110 200 130 C 170 150 120 140 80 120 C 50 105 20 90 0 100 Z'}" fill="var(--tag-line)"/>`;
  s += windArrow(f.wind ?? 180, 282, 160);
  (f.spots || []).forEach(p => s += `<circle cx="${p[0]}" cy="${p[1]}" r="13" fill="var(--bg)" stroke="var(--ink)" stroke-width="2"/>` + txt(p[0], p[1] + 5, p[2], { s: 13, f: 'var(--ink)' }));
  (f.labels || []).forEach(l => s += txt(l[0], l[1], l[2], { s: 10, w: 400, a: l[3] || 'middle' }));
  if (f.note) s += txt(14, 190, f.note, { s: 10, w: 400, a: 'start' });
  return s + '</svg>';
};

/* ---------- panel: engine / electrics readouts ---------- */
FIG.panel = f => {
  let s = NS() + `<rect x="10" y="14" width="300" height="172" rx="18" fill="var(--band)"/>`;
  const g = (x, label, val, bad) => `<rect x="${x}" y="34" width="86" height="92" rx="14" fill="var(--bg)" stroke="${bad ? 'var(--danger)' : 'var(--line)'}" stroke-width="2"/>` + txt(x + 43, 58, label, { s: 10 }) + txt(x + 43, 90, val, { s: bad ? 18 : 16, f: bad ? 'var(--danger)' : 'var(--ink)' }) + (bad ? txt(x + 43, 112, '!', { s: 14, f: 'var(--danger)' }) : '');
  (f.gauges || []).forEach((q, i) => s += g(22 + i * 96, q[0], q[1], q[2]));
  (f.lines || []).forEach((l, i) => s += txt(24, 150 + 16 * i, l, { s: 12, f: 'var(--ink)', a: 'start', w: 400 }));
  return s + '</svg>';
};

/* ---------- vhf: what you have and where; a situation card ---------- */
FIG.card = f => {
  let s = NS() + `<rect x="10" y="14" width="300" height="172" rx="18" fill="var(--band)"/>`;
  s += txt(26, 44, f.title || '', { s: 14, f: 'var(--ink)', a: 'start' });
  (f.lines || []).forEach((l, i) => s += txt(26, 70 + 20 * i, l, { s: 12.5, f: 'var(--ink)', a: 'start', w: 400 }));
  if (f.tag) s += `<rect x="214" y="30" width="86" height="26" rx="13" fill="var(--danger)"/>` + txt(257, 47, f.tag, { s: 11, f: '#fff' });
  return s + '</svg>';
};

/* ---------- rope: knot photos are out of scope; a labelled line through a fitting ---------- */
FIG.rope = f => {
  let s = NS();
  const kinds = {
    cleat: `<rect x="120" y="96" width="80" height="14" rx="7" fill="var(--ink)"/><rect x="150" y="104" width="20" height="18" fill="var(--ink)"/><path d="M40 60 C 120 60 100 130 200 130 C 240 130 230 80 190 80 C 150 80 150 120 120 120 C 90 120 90 90 125 90" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>`,
    winch: `<circle cx="160" cy="100" r="34" fill="var(--band)" stroke="var(--ink)" stroke-width="3"/><circle cx="160" cy="100" r="8" fill="var(--ink)"/><path d="M30 100 H126 M160 66 A34 34 0 1 1 126 100 M160 134 A34 34 0 0 1 128 108 M194 100 H290" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>${arrow(230, 100, 270, 100, { c: 'var(--accent)', w: 3 })}`,
    rail: `<rect x="20" y="92" width="280" height="10" rx="5" fill="var(--ink)"/><path d="M120 60 C 150 60 150 110 110 110 C 80 110 100 85 140 85 C 180 85 180 120 120 140" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>`,
    ring: `<circle cx="160" cy="80" r="26" fill="none" stroke="var(--ink)" stroke-width="6"/><path d="M160 106 C 130 140 190 150 150 160 C 110 170 220 160 160 180" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>`,
    sheet: `<path d="M60 60 L120 110 L80 150" fill="none" stroke="var(--ink)" stroke-width="7" stroke-linecap="round"/><path d="M260 60 L200 110 L240 150" fill="none" stroke="var(--accent)" stroke-width="12" stroke-linecap="round"/>`,
  };
  s += kinds[f.kind] || '';
  (f.labels || []).forEach(l => s += txt(l[0], l[1], l[2], { s: 11, w: 700, a: l[3] || 'middle' }));
  if (f.note) s += txt(160, 192, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- boat: a sloop with its parts named — in profile ('side'), from above ('plan'), or her mainsail ('sail') ----------
   { type: 'boat', view: 'side' | 'plan' | 'sail', parts: [[key, text], …], note }
   Each part has its place (BOAT_PARTS); the text is the caller's, so a translation gives its own words. A key not in
   the view is skipped. In 'side', draft and freeboard add their dimension arrows; in 'sail', reef adds the reef line. */
const BOAT_PARTS = { // key: [x, y of the part, x, y of the label, text-anchor, colour]; a part with no label place is named on itself
  side: {
    mast: [160, 20, 160, 12, 'middle'], mainsail: [135, 95], jib: [193, 99],
    forestay: [203, 74, 222, 60, 'start'], backstay: [114, 76, 96, 56, 'end'], boom: [112, 105.6, 72, 92, 'end'],
    pushpit: [75, 114, 60, 112, 'end'], stern: [76, 128, 62, 138, 'end'], rudder: [95, 164, 80, 178, 'end'], keel: [150, 174, 136, 190, 'end'],
    pulpit: [238, 109, 250, 100, 'start'], bow: [238, 119, 252, 120, 'start'], freeboard: [214, 132, 252, 138, 'start'], hull: [206, 151, 246, 174, 'start'],
    draft: [196, 166, 203, 180, 'start'], waterline: [312, 158, 312, 158, 'end'],
  },
  plan: {
    ahead: [160, 38, 160, 18, 'middle'], astern: [160, 152, 160, 180, 'middle'],
    'port-bow': [146, 58, 114, 32, 'end'], 'stbd-bow': [174, 58, 206, 32, 'start'], 'port-quarter': [146, 140, 114, 176, 'end'], 'stbd-quarter': [174, 140, 206, 176, 'start'],
    port: [134, 100, 88, 94, 'end', COL.r], starboard: [186, 100, 232, 94, 'start', COL.g], 'abeam-port': [134, 100, 88, 110, 'end'], 'abeam-stbd': [186, 100, 232, 110, 'start'],
  },
  sail: {
    head: [114, 25, 126, 16, 'start'], luff: [104, 96, null, null, 'end'], mast: [104, 44, null, null, 'end'], tack: [114, 158, 102, 178, 'end'],
    foot: [176, 178], clew: [240, 161, 252, 148, 'start'], boom: [236, 163, 252, 172, 'start'], leech: [202, 86, null, null, 'start'],
    batten: [160, 61, 172, 48, 'start'], reef: [166, 122],
  },
};
FIG.boat = f => {
  const v = BOAT_PARTS[f.view] ? f.view : 'side', has = (k) => (f.parts || []).some((p) => p[0] === k);
  const ink = 'stroke="var(--ink)" stroke-linecap="round" stroke-linejoin="round"';
  let s = NS();
  if (v === 'side') {
    s += `<path d="M8 146c13-6 26-6 39 0s26 6 39 0 26-6 39 0 26 6 39 0 26-6 39 0 26 6 39 0 26-6 39 0 26 6 39 0" fill="none" stroke="var(--faint)" stroke-width="2" stroke-linecap="round"/>`;
    s += `<path d="M144 154 L172 154 L168 182 L150 182 Z M92 149 L102 150 L100 174 L94 174 Z" fill="var(--ink)"/>`; // keel, rudder
    s += `<path d="M74 124 L238 118 L226 146 Q156 164 86 146 Z" fill="var(--bg)" ${ink} stroke-width="2"/>`;
    s += `<path d="M118 122.4 L126 113 L178 112 L188 119.8" fill="var(--bg)" ${ink} stroke-width="2"/>`; // coachroof
    s += `<path d="M74 124 V113 H86 V123.5 M238 118 L240 108 L226 108.5 V118.4" fill="none" ${ink} stroke-width="1.5"/>`; // pushpit, pulpit
    s += `<path d="M160 20 L238 118 M160 20 L76 123" fill="none" ${ink} stroke-width="1.5"/>`; // forestay, backstay
    s += `<path d="M158.5 24 V102 L100 104 Z M167.5 30 L233 113 L170 106 Z" fill="var(--bg)" ${ink} stroke-width="1.5"/>`; // mainsail, jib
    s += `<path d="M160 112.5 V20 M160 104 L98 106" fill="none" ${ink} stroke-width="3"/>`; // mast, boom
    const dim = (x, y1, y2) => `<path d="M${x} ${y1} V${y2} M${x - 4} ${y1} h8 M${x - 4} ${y2} h8" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round"/>`;
    if (has('draft')) s += dim(196, 146, 182);
    if (has('freeboard')) s += dim(214, 119.5, 146);
  } else if (v === 'plan') {
    const ray = (x1, y1, x2, y2) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>`;
    const P = BOAT_PARTS.plan;
    if (has('ahead')) s += ray(160, 38, 160, 24);
    if (has('astern')) s += ray(160, 152, 160, 168);
    if (has('port') || has('abeam-port')) s += ray(134, 100, 94, 100);
    if (has('starboard') || has('abeam-stbd')) s += ray(186, 100, 226, 100);
    ['port-bow', 'stbd-bow', 'port-quarter', 'stbd-quarter'].forEach((k) => { if (has(k)) s += ray(P[k][0], P[k][1], P[k][2] + (P[k][4] === 'end' ? 6 : -6), P[k][3] + (P[k][3] < 100 ? 2 : -10)); });
    s += boat(160, 100, 0, { scale: 2.6, fill: 'var(--bg)' }) + `<circle cx="160" cy="86" r="3.5" fill="var(--ink)"/><line x1="160" y1="86" x2="160" y2="128" stroke="var(--ink)" stroke-width="2.5" stroke-linecap="round"/>`; // mast and boom
    s += `<path d="M139.5 104 C 139 82 143 60 160 43" fill="none" stroke="${COL.r}" stroke-width="3" stroke-linecap="round"/><path d="M180.5 104 C 181 82 177 60 160 43" fill="none" stroke="${COL.g}" stroke-width="3" stroke-linecap="round"/>`;
  } else {
    s += `<path d="M114 24 Q196 82 240 161 L114 158 Z" fill="var(--bg)" ${ink} stroke-width="1.5"/>`;
    s += `<path d="M159.8 60.7 L136 63 M186.5 87.2 L158 91 M210.2 115.5 L180 119" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-linecap="round"/>`; // battens
    if (has('reef')) s += `<line x1="114" y1="128" x2="218.8" y2="127.2" stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="5 4"/><circle cx="118" cy="128" r="3" fill="var(--bg)" stroke="var(--accent)" stroke-width="1.5"/><circle cx="214" cy="127.3" r="3" fill="var(--bg)" stroke="var(--accent)" stroke-width="1.5"/>`;
    s += `<path d="M112 182 V18 M112 160 L246 163" fill="none" ${ink} stroke-width="3"/>`; // mast, boom
  }
  (f.parts || []).forEach(([k, raw]) => {
    const p = BOAT_PARTS[v][k], text = String(raw).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    if (!p) return;
    const [px, py, lx, ly, a = 'middle', col] = p, o = { s: lx == null && v === 'side' ? 10 : 11, f: col || 'var(--ink)', a };
    if (lx == null) return void (s += txt(px, py, text, o));
    if (v !== 'plan' && k !== 'waterline') s += `<line x1="${px}" y1="${py}" x2="${a === 'start' ? lx - 3 : a === 'end' ? lx + 3 : lx}" y2="${a === 'middle' ? ly + 3 : ly - 4}" stroke="var(--muted)" stroke-width="1"/><circle cx="${px}" cy="${py}" r="1.8" fill="var(--muted)"/>`;
    s += txt(lx, ly, text, o);
  });
  if (f.note) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* ---------- figures of the theory articles: lines ashore, a VHF set, signal flags, a tidal curve, the celestial sphere,
   a sextant altitude. Labels are the caller's text ([key, text] pairs), so a translation gives its own words; a key the
   figure does not have is skipped. FIG_KEYS lists the keys of each, for data/check_theory.mjs. ---------- */
const fesc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
// Names at their places: map[key] = [x, y of the part, x, y of the label, text-anchor]; with no label place the name sits on the part.
function partLabels(map, parts, leaders = true) {
  return (parts || []).map(([k, raw]) => {
    const p = map[k];
    if (!p) return '';
    const [px, py, lx, ly, a = 'middle'] = p, o = { s: 11, f: 'var(--ink)', a };
    if (lx == null) return txt(px, py, fesc(raw), o);
    const line = leaders ? `<line x1="${px}" y1="${py}" x2="${a === 'start' ? lx - 3 : a === 'end' ? lx + 3 : lx}" y2="${a === 'middle' ? (ly < py ? ly + 3 : ly - 11) : ly - 4}" stroke="var(--muted)" stroke-width="1"/><circle cx="${px}" cy="${py}" r="1.8" fill="var(--muted)"/>` : '';
    return line + txt(lx, ly, fesc(raw), o);
  }).join('');
}

/* lines: a yacht alongside, from above, with her lines numbered and named below
   { type: 'lines', lines: [['bow', 'bow line'], ['stern-spring', 'stern spring'], …], quay: 'PONTOON', note } */
const LINE_ENDS = { // key: [on the boat, on the pontoon, where the number sits along the line (0 = boat end)]
  bow: [[206, 76], [264, 52], .5], stern: [[114, 77], [56, 52], .5], 'bow-spring': [[206, 76], [150, 52], .32], 'stern-spring': [[114, 77], [170, 52], .32],
  'bow-breast': [[206, 76], [206, 52], .5], 'stern-breast': [[114, 77], [114, 52], .5],
};
FIG.lines = f => {
  let s = NS() + `<rect x="20" y="16" width="280" height="36" rx="8" fill="var(--tag-line)"/>` + (f.quay ? txt(160, 38, fesc(f.quay), { s: 10 }) : '');
  s += boat(160, 94, 90, { scale: 3, fill: 'var(--bg)' });
  const list = (f.lines || []).filter(([k]) => LINE_ENDS[k]);
  const badge = (x, y, n) => `<circle cx="${x}" cy="${y}" r="8" fill="var(--bg)" stroke="var(--accent)" stroke-width="1.5"/>` + txt(x, y + 3.5, n, { s: 10, f: 'var(--accent)' });
  list.forEach(([k]) => { const [[x1, y1], [x2, y2]] = LINE_ENDS[k]; s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/><circle cx="${x1}" cy="${y1}" r="2.5" fill="var(--ink)"/><circle cx="${x2}" cy="${y2}" r="2.5" fill="var(--ink)"/>`; });
  list.forEach(([k, text], i) => {
    const [[x1, y1], [x2, y2], at] = LINE_ENDS[k];
    s += badge(x1 + (x2 - x1) * at, y1 + (y2 - y1) * at, i + 1);
    const x = i % 2 ? 176 : 30, y = 144 + Math.floor(i / 2) * 18;
    s += badge(x, y, i + 1) + txt(x + 14, y + 4, fesc(text), { s: 11, f: 'var(--ink)', a: 'start' });
  });
  if (f.note && list.length <= 4) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* radio: a fixed VHF set with its handset
   { type: 'radio', channel: '16', power: 'HI', parts: [['distress', 'DISTRESS, under its cover'], ['squelch', 'squelch'], …], note } */
const RADIO_PARTS = {
  display: [114, 58, 100, 30, 'middle'], volume: [203, 64, 232, 34, 'start'], mic: [277, 70, 282, 58, 'middle'], ptt: [260, 106, 306, 166, 'end'],
  distress: [86, 136, 70, 170, 'middle'], power: [153, 136, 176, 170, 'middle'], ch16: [125, 136, 112, 184, 'middle'], squelch: [203, 130, 232, 184, 'middle'],
};
FIG.radio = f => {
  let s = NS() + `<rect x="50" y="44" width="190" height="104" rx="12" fill="#1b2228"/><rect x="66" y="58" width="96" height="48" rx="6" fill="#d9ead3"/>`;
  s += txt(120, 96, fesc(f.channel || '16'), { s: 32, f: '#10202a' }) + txt(72, 70, fesc(f.power || 'HI'), { s: 9, f: '#10202a', a: 'start' }) + txt(156, 70, 'DSC', { s: 9, f: '#10202a', a: 'end' });
  s += `<circle cx="196" cy="74" r="13" fill="#39444d" stroke="#6b7780" stroke-width="1.5"/><line x1="196" y1="74" x2="196" y2="64" stroke="#fff" stroke-width="2" stroke-linecap="round"/>`;
  s += `<circle cx="196" cy="120" r="13" fill="#39444d" stroke="#6b7780" stroke-width="1.5"/><line x1="196" y1="120" x2="203" y2="113" stroke="#fff" stroke-width="2" stroke-linecap="round"/>`;
  s += `<rect x="66" y="114" width="40" height="22" rx="5" fill="${COL.r}"/><rect x="64" y="112" width="44" height="26" rx="6" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="3 2"/>`;
  s += `<rect x="114" y="114" width="22" height="22" rx="5" fill="#39444d"/>` + txt(125, 129, '16', { s: 10, f: '#fff' }) + `<rect x="142" y="114" width="22" height="22" rx="5" fill="#39444d"/>` + txt(153, 129, 'H/L', { s: 8, f: '#fff' });
  s += `<path d="M240 134 C 256 152 272 150 277 126" fill="none" stroke="#1b2228" stroke-width="3" stroke-linecap="round"/><rect x="262" y="70" width="30" height="56" rx="8" fill="#1b2228"/><rect x="258" y="86" width="5" height="24" rx="2" fill="#6b7780"/>`;
  s += partLabels(RADIO_PARTS, f.parts);
  if (f.note) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* flag: up to four signal flags in a row, each with its name: the code flags sailors meet and the race signals
   { type: 'flag', flags: [['P', 'P · preparatory'], ['first-sub', 'general recall']], note } */
const FLAG_BLUE = '#0b4ea2', FLAG_YEL = '#ffd400';
const FLAGS = { // drawn in a 60 × 40 box
  P: `<rect width="60" height="40" fill="${FLAG_BLUE}"/><rect x="20" y="13" width="20" height="14" fill="#fff"/>`,
  S: `<rect width="60" height="40" fill="#fff"/><rect x="20" y="13" width="20" height="14" fill="${FLAG_BLUE}"/>`,
  I: `<rect width="60" height="40" fill="${FLAG_YEL}"/><circle cx="30" cy="20" r="9" fill="#000"/>`,
  X: `<rect width="60" height="40" fill="#fff"/><rect x="25" width="10" height="40" fill="${FLAG_BLUE}"/><rect y="15" width="60" height="10" fill="${FLAG_BLUE}"/>`,
  N: `<rect width="60" height="40" fill="#fff"/>` + [0, 1, 2, 3].map((r) => [0, 1, 2, 3].filter((c) => (r + c) % 2 === 0).map((c) => `<rect x="${c * 15}" y="${r * 10}" width="15" height="10" fill="${FLAG_BLUE}"/>`).join('')).join(''),
  Z: `<path d="M0 0 L30 20 L0 40Z" fill="#000"/><path d="M0 0 H60 L30 20Z" fill="${FLAG_YEL}"/><path d="M60 0 V40 L30 20Z" fill="${FLAG_BLUE}"/><path d="M0 40 H60 L30 20Z" fill="${COL.r}"/>`,
  U: `<rect width="60" height="40" fill="#fff"/><rect width="30" height="20" fill="${COL.r}"/><rect x="30" y="20" width="30" height="20" fill="${COL.r}"/>`,
  L: `<rect width="60" height="40" fill="#000"/><rect width="30" height="20" fill="${FLAG_YEL}"/><rect x="30" y="20" width="30" height="20" fill="${FLAG_YEL}"/>`,
  M: `<rect width="60" height="40" fill="${FLAG_BLUE}"/><path d="M0 0 L60 40 M60 0 L0 40" stroke="#fff" stroke-width="8"/>`,
  V: `<rect width="60" height="40" fill="#fff"/><path d="M0 0 L60 40 M60 0 L0 40" stroke="${COL.r}" stroke-width="8"/>`,
  Y: `<rect width="60" height="40" fill="${FLAG_YEL}"/><path d="M-30 40 L10 0 M-6 40 L34 0 M18 40 L58 0 M42 40 L82 0" stroke="${COL.r}" stroke-width="8"/>`,
  C: `<rect width="60" height="40" fill="${FLAG_BLUE}"/><rect y="8" width="60" height="24" fill="#fff"/><rect y="16" width="60" height="8" fill="${COL.r}"/>`,
  O: `<path d="M0 0 H60 V40Z" fill="${COL.r}"/><path d="M0 0 L60 40 H0Z" fill="${FLAG_YEL}"/>`,
  H: `<rect width="60" height="40" fill="#fff"/><rect x="30" width="30" height="40" fill="${COL.r}"/>`,
  Q: `<rect width="60" height="40" fill="${FLAG_YEL}"/>`,
  R: `<rect width="60" height="40" fill="${COL.r}"/><rect x="25" width="10" height="40" fill="${FLAG_YEL}"/><rect y="15" width="60" height="10" fill="${FLAG_YEL}"/>`,
  A: `<path d="M0 0 H30 V40 H0Z" fill="#fff"/><path d="M30 0 H60 L46 20 L60 40 H30Z" fill="${FLAG_BLUE}"/>`,
  B: `<path d="M0 0 H60 L46 20 L60 40 H0Z" fill="${COL.r}"/>`,
  AP: [0, 1, 2, 3, 4].map((i) => `<rect x="${i * 12}" width="12" height="40" fill="${i % 2 ? '#fff' : COL.r}"/>`).join(''),
  'first-sub': `<path d="M0 0 L60 20 L0 40Z" fill="${FLAG_BLUE}"/><path d="M0 9 L33 20 L0 31Z" fill="${FLAG_YEL}"/>`,
  black: `<rect width="60" height="40" fill="#000"/>`, blue: `<rect width="60" height="40" fill="${FLAG_BLUE}"/>`, red: `<rect width="60" height="40" fill="${COL.r}"/>`,
  green: `<rect width="60" height="40" fill="${COL.g}"/>`, yellow: `<rect width="60" height="40" fill="${FLAG_YEL}"/>`, orange: `<rect width="60" height="40" fill="#ff7a00"/>`, white: `<rect width="60" height="40" fill="#fff"/>`,
};
const FLAG_SHAPE = { A: 'M0 0 H60 L46 20 L60 40 H0Z', B: 'M0 0 H60 L46 20 L60 40 H0Z', AP: 'M0 0 L60 13 V27 L0 40Z', 'first-sub': 'M0 0 L60 20 L0 40Z' };
let flagN = 0;
FIG.flag = f => {
  const list = (f.flags || []).filter(([k]) => FLAGS[k]).slice(0, 4), n = list.length, step = n > 3 ? 76 : 92, w = n > 3 ? 60 : 72, k = w / 60;
  let s = NS();
  list.forEach(([code, text], i) => {
    const x = 160 - ((n - 1) * step) / 2 + i * step - w / 2, y = 52, id = `fl${++flagN}`, shape = FLAG_SHAPE[code] || 'M0 0 H60 V40 H0Z';
    s += `<g transform="translate(${x} ${y}) scale(${k})"><clipPath id="${id}"><path d="${shape}"/></clipPath><g clip-path="url(#${id})">${FLAGS[code]}</g><path d="${shape}" fill="none" stroke="#7d8a91" stroke-width="1"/></g>`;
    String(text || '').split('|').forEach((line, j) => { s += txt(x + w / 2, y + 40 * k + 18 + j * 14, fesc(line.trim()), { s: 11, f: j ? 'var(--muted)' : 'var(--ink)', w: j ? 400 : 700 }); });
  });
  if (f.note) s += txt(160, 194, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* tide: the rise from low water to high water over six hours, with the rule of twelfths
   { type: 'tide', lw: '08:00 · 0.4 m', hw: '14:00 · 2.2 m', twelfths: true, at: 2, atLabel: '10:00 · 0.85 m', note } */
FIG.tide = f => {
  const x0 = 44, x1 = 284, yL = 150, yH = 46, base = 168, at = (t) => [x0 + (x1 - x0) * t, yL - (yL - yH) * (1 - Math.cos(Math.PI * t)) / 2];
  let s = NS() + `<line x1="34" y1="${base}" x2="296" y2="${base}" stroke="var(--tag-line)" stroke-width="1.5"/>`;
  for (let i = 0; i <= 6; i++) {
    const [x, y] = at(i / 6);
    s += `<line x1="${x}" y1="${base}" x2="${x}" y2="${y}" stroke="var(--tag-line)" stroke-width="1" stroke-dasharray="3 4"/>` + txt(x, base + 13, i === 0 ? ft('LW') : i === 6 ? ft('HW') : `+${i}`, { s: 10 });
    if (f.twelfths && i < 6) s += txt(x + 20, base - 6, `${[1, 2, 3, 3, 2, 1][i]}/12`, { s: 10, f: 'var(--accent)' });
  }
  s += `<path d="M${Array.from({ length: 25 }, (_, i) => at(i / 24).map((v) => v.toFixed(1)).join(' ')).join(' L')}" fill="none" stroke="var(--ink)" stroke-width="2.5" stroke-linecap="round"/>`;
  if (f.lw) s += txt(x0 - 6, yL - 13, fesc(f.lw), { s: 10, f: 'var(--ink)', a: 'start' });
  if (f.hw) s += txt(x1 + 4, yH - 8, fesc(f.hw), { s: 10, f: 'var(--ink)', a: 'end' });
  if (f.at != null) { const [x, y] = at(Math.max(0, Math.min(6, f.at)) / 6); s += `<circle cx="${x}" cy="${y}" r="5" fill="var(--accent)"/>` + (f.atLabel ? txt(x + 9, y + 12, fesc(f.atLabel), { s: 11, f: 'var(--accent)', a: 'start' }) : ''); }
  if (f.note) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* sphere: the celestial sphere round the observer, with the PZX triangle (pole, zenith, body)
   { type: 'sphere', parts: [['Z', 'Z zenith'], ['P', 'P pole'], ['X', 'X body'], ['pz', '90° − latitude'], ['zx', 'zenith distance'], ['px', 'polar distance'], ['horizon', 'horizon'], ['equator', 'celestial equator'], ['observer', 'observer']], note } */
const SPHERE_PARTS = {
  Z: [160, 15], P: [104, 38, null, null, 'end'], X: [213, 73, null, null, 'start'], observer: [160, 114], horizon: [240, 102, null, null, 'start'], equator: [98, 162],
  pz: [134, 28, 116, 14, 'end'], zx: [188, 40, 204, 30, 'start'], px: [150, 46, 128, 86, 'middle'],
};
FIG.sphere = f => {
  let s = NS() + `<circle cx="160" cy="98" r="74" fill="var(--bg)" stroke="var(--ink)" stroke-width="1.5"/>`;
  s += `<path d="M86 98 A74 20 0 0 0 234 98" fill="none" stroke="var(--muted)" stroke-width="1.5"/><path d="M86 98 A74 20 0 0 1 234 98" fill="none" stroke="var(--muted)" stroke-width="1" stroke-dasharray="3 4"/>`;
  s += `<ellipse cx="160" cy="98" rx="74" ry="18" transform="rotate(-40 160 98)" fill="none" stroke="var(--muted)" stroke-width="1" stroke-dasharray="6 4"/>`;
  s += `<line x1="160" y1="98" x2="160" y2="24" stroke="var(--tag-line)" stroke-width="1.5"/><line x1="160" y1="98" x2="112.4" y2="41.3" stroke="var(--tag-line)" stroke-width="1.5"/>`;
  s += `<path d="M112.4 41.3 A74 74 0 0 1 160 24 Q192 34 204 70 Q162 42 112.4 41.3Z" fill="var(--accent)" fill-opacity=".1" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round"/>`;
  s += `<circle cx="160" cy="98" r="3" fill="var(--ink)"/><circle cx="160" cy="24" r="3.5" fill="var(--ink)"/><circle cx="112.4" cy="41.3" r="3.5" fill="var(--ink)"/><circle cx="204" cy="70" r="5.5" fill="${COL.y}" stroke="var(--ink)" stroke-width="1.5"/>`;
  s += partLabels(SPHERE_PARTS, f.parts);
  if (f.note) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

/* altitude: what the sextant measures — the body above the visible horizon, seen from a height of eye
   { type: 'altitude', parts: [['hs', 'sextant altitude'], ['dip', 'dip'], ['horizon', 'visible horizon'], ['horizontal', 'true horizontal'], ['limb', 'lower limb'], ['sun', 'Sun'], ['eye', 'height of eye']], note } */
const ALT_PARTS = {
  sun: [268, 36, null, null, 'start'], limb: [250, 49, 234, 28, 'end'], horizontal: [302, 106, null, null, 'end'], horizon: [302, 166, null, null, 'end'],
  hs: [126, 108, null, null, 'start'], dip: [172, 126, null, null, 'start'], eye: [56, 124, 10, 88, 'start'],
};
FIG.altitude = f => {
  let s = NS() + `<path d="M0 150 H320" stroke="var(--faint)" stroke-width="2"/><path d="M30 150 L78 150 L72 161 L36 161 Z" fill="var(--ink)"/><line x1="56" y1="150" x2="56" y2="112" stroke="var(--ink)" stroke-width="2"/>`;
  s += `<line x1="56" y1="112" x2="304" y2="112" stroke="var(--muted)" stroke-width="1" stroke-dasharray="5 4"/><line x1="56" y1="112" x2="296" y2="148" stroke="var(--ink)" stroke-width="1.5"/><line x1="56" y1="112" x2="250" y2="49" stroke="var(--ink)" stroke-width="1.5"/>`;
  s += `<circle cx="250" cy="40" r="9" fill="${COL.y}" stroke="var(--ink)" stroke-width="1.5"/><circle cx="56" cy="112" r="3.5" fill="var(--ink)"/>`;
  s += `<path d="M119.3 121.5 A64 64 0 0 0 116.9 92.2" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/><path d="M166 112 A110 110 0 0 1 164.8 128.3" fill="none" stroke="var(--danger)" stroke-width="2.5" stroke-linecap="round"/>`;
  s += partLabels(ALT_PARTS, f.parts);
  if (f.note) s += txt(160, 197, f.note, { s: 11, w: 400 });
  return s + '</svg>';
};

// The keys each labelled figure knows, for the checker: FIG_KEYS[type](spec) → { key: … }; the list field is parts, lines or flags.
const FIG_KEYS = { boat: (f) => BOAT_PARTS[f.view] || BOAT_PARTS.side, radio: () => RADIO_PARTS, sphere: () => SPHERE_PARTS, altitude: () => ALT_PARTS, lines: () => LINE_ENDS, flag: () => FLAGS };

function figSvg(spec) { const r = FIG[spec.type]; return r ? r(spec) : NS() + txt(160, 100, 'figure: ' + spec.type) + '</svg>'; }
function paintFigures(root = document) {
  root.querySelectorAll('[data-fig]').forEach(el => { if (el.dataset.figDone) return; try { const spec = JSON.parse(el.dataset.fig); el.innerHTML = figSvg(spec); if (FIG_DAY.has(spec.type)) el.classList.add('day'); } catch (e) { el.textContent = 'bad figure: ' + e.message; } el.dataset.figDone = 1; });
}
if (typeof module !== 'undefined') module.exports = { FIG, figSvg };
