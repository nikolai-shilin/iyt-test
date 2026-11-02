/* IYT Test figures: every drawn question is a small JSON spec rendered to SVG here (one renderer per type).
   320×200 viewBox, theme tokens for ink/muted/bg; fixed colours only for lights and buoys (red, green, yellow, white).
   Usage: figSvg(spec) → svg string; paintFigures(root) fills every [data-fig] element. */

const FIG = {};
const NS = (w = 320, h = 200, extra = '') => `<svg viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="xMidYMid meet" font-family="Carlito, Arial, sans-serif" ${extra}>`;
const RAD = Math.PI / 180;
const pol = (cx, cy, r, deg) => [cx + r * Math.sin(deg * RAD), cy - r * Math.cos(deg * RAD)];
const txt = (x, y, s, o = {}) => `<text x="${x}" y="${y}" font-size="${o.s || 11}" font-weight="${o.w || 700}" fill="${o.f || 'var(--muted)'}" text-anchor="${o.a || 'middle'}" ${o.extra || ''}>${s}</text>`;
const COL = { r: '#e0251b', g: '#1aa34a', w: '#ffffff', y: '#ffa800', k: 'var(--ink)' };

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
  return `<g>${arrow(ax, ay, bx, by, { c: 'var(--accent)', w: 2.5 })}${txt(x, y + 40, 'wind', { s: 10, f: 'var(--accent)' })}</g>`;
}
function compassN(x = 30, y = 30) { return `<g>${arrow(x, y + 14, x, y - 14, { c: 'var(--muted)' })}${txt(x, y - 18, 'N', { s: 11 })}</g>`; }

/* ---------- encounter: own boat centre, other vessel by relative bearing; headings; optional wind ---------- */
FIG.encounter = f => {
  const cx = 160, cy = 108, you = f.you || {}, oth = f.other || {};
  const yh = you.hdg ?? 0;
  const solo = (oth.dist ?? 80) < 1;  /* dist 0: a single-boat picture, no other vessel */
  const [ox, oy] = pol(cx, cy, oth.dist ?? 80, yh + (oth.bearing ?? 45));
  let s = NS();
  s += compassN();
  if (f.wind != null) s += windArrow(f.wind);
  if (f.bearingLine) s += `<line x1="${cx}" y1="${cy}" x2="${ox}" y2="${oy}" stroke="var(--tag-line)" stroke-width="2" stroke-dasharray="4 5"/>`;
  const hl = (x, y, hdg, L) => { const [tx, ty] = pol(x, y, L, hdg); return arrow(x, y, tx, ty, { c: 'var(--muted)', dash: true }); };
  s += hl(cx, cy, yh, 58) + (solo ? '' : hl(ox, oy, oth.hdg ?? 180, 58));
  s += boat(cx, cy, yh, { sail: you.sail, boom: you.boom, you: true, label: you.label || 'You' });
  if (!solo) s += boat(ox, oy, oth.hdg ?? 180, { sail: oth.sail, boom: oth.boom, label: oth.label || 'Other', scale: oth.scale || 1 });
  if (f.note) s += txt(160, 192, f.note, { s: 11, w: 400 });
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
  s += txt(160, 188, f.note || 'Night · lights seen ahead', { s: 11, f: '#8aa0b8', w: 400 });
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
    const lc = { 'lat-port': B ? COL.g : COL.r, 'lat-stbd': B ? COL.r : COL.g, 'special': COL.y }[k] || '#fff';
    s += `<rect x="196" y="60" width="114" height="80" rx="14" fill="#07101a"/><circle cx="222" cy="92" r="9" fill="${lc}"/><circle cx="222" cy="92" r="18" fill="${lc}" opacity=".18"/>`;
    s += txt(236, 88, 'Light at night', { s: 10, f: '#8aa0b8', w: 400, a: 'start' }) + txt(236, 104, f.rhythm, { s: 13, f: '#fff', a: 'start' });
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
  const [tx, ty] = pol(cx, cy, r + 14, 0); s += txt(tx + (v < 0 ? 8 : -8), ty + 4, 'N (true)', { s: 11, a: v < 0 ? 'start' : 'end' });
  const [mx, my] = pol(cx, cy, r - 2, v); s += arrow(cx, cy, mx, my, { c: 'var(--accent)', w: 2.5 });
  const [lx, ly] = pol(cx, cy, r + 16, v); s += txt(lx + (v < 0 ? -10 : 10), ly + 4, 'MN', { s: 11, f: 'var(--accent)', a: v < 0 ? 'end' : 'start' });
  if (f.course != null) { const [qx, qy] = pol(cx, cy, r - 2, f.course); s += arrow(cx, cy, qx, qy, { c: 'var(--ink)', w: 3 }); }
  s += `<rect x="206" y="52" width="104" height="96" rx="16" fill="var(--band)"/>`;
  s += txt(258, 74, `Variation ${Math.abs(v)}°${v < 0 ? 'W' : 'E'}`, { s: 13, f: 'var(--ink)' });
  if (f.course != null) s += txt(258, 96, `${f.courseLabel || 'True course'} ${String(f.course).padStart(3, '0')}°`, { s: 12, f: 'var(--ink)', w: 400 });
  if (f.deviation != null) s += txt(258, 116, `Deviation ${Math.abs(f.deviation)}°${f.deviation < 0 ? 'W' : 'E'}`, { s: 12, f: 'var(--ink)', w: 400 });
  if (f.note) s += txt(258, 138, f.note, { s: 10, w: 400 });
  return s + '</svg>';
};

/* ---------- chart: soundings, a drying patch, a track; tide and draft in a panel ---------- */
FIG.chart = f => {
  let s = NS() + `<rect width="320" height="200" fill="var(--band)" rx="16"/>`;
  if (f.land) s += `<path d="${f.land}" fill="var(--tag-line)" opacity=".9"/>`;
  (f.depths || []).forEach(d => s += txt(d[0], d[1], d[2], { s: 13, f: 'var(--ink)', w: 400, extra: d[3] ? 'text-decoration="underline"' : '' }));
  (f.marks || []).forEach(m => s += `<circle cx="${m[0]}" cy="${m[1]}" r="5" fill="${COL[m[2]] || 'var(--ink)'}" stroke="var(--ink)" stroke-width="1"/>` + (m[3] ? txt(m[0], m[1] - 9, m[3], { s: 10 }) : ''));
  if (f.track) s += `<path d="${f.track}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-dasharray="7 5"/>`;
  (f.labels || []).forEach(l => s += txt(l[0], l[1], l[2], { s: 11, f: 'var(--muted)', w: 700, a: l[3] || 'middle' }));
  if (f.boat) s += boat(f.boat[0], f.boat[1], f.boat[2], { you: true, scale: .7 });
  if (f.panel) { s += `<rect x="190" y="12" width="118" height="${18 + 18 * f.panel.length}" rx="12" fill="var(--bg)" stroke="var(--line)"/>`; f.panel.forEach((p, i) => s += txt(200, 30 + 18 * i, p, { s: 12, f: 'var(--ink)', w: i ? 400 : 700, a: 'start' })); }
  s += txt(26, 190, f.note || 'Depths in metres below chart datum', { s: 10, w: 400, a: 'start' });
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
  s += `<line x1="292" y1="${wl}" x2="292" y2="${bed}" stroke="var(--accent)" stroke-width="2"/>` + txt(300, (wl + bed) / 2 + 4, f.depth, { s: 12, f: 'var(--accent)', a: 'start' });
  if (f.tide) s += txt(300, wl + 14, f.tide, { s: 10, f: 'var(--accent)', a: 'start', w: 400 });
  s += txt(16, 30, f.title || 'Anchoring', { s: 13, f: 'var(--ink)', a: 'start' });
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
  s += txt(300, 24, f.hemisphere || 'Northern hemisphere', { s: 11, a: 'end' });
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

/* ---------- dayshape: a boat with a day shape hoisted ---------- */
FIG.dayshape = f => {
  let s = NS() + `<path d="M10 150c16-10 32-10 48 0s32 10 48 0 32-10 48 0 32 10 48 0 32-10 48 0 32 10 48 0" fill="none" stroke="var(--faint)" stroke-width="2"/>`;
  s += `<path d="M70 140 L250 140 L232 160 L88 160 Z" fill="var(--ink)"/><line x1="160" y1="140" x2="160" y2="40" stroke="var(--ink)" stroke-width="3"/>`;
  if (f.sail) s += `<path d="M163 44 L163 134 L228 134 Z" fill="var(--band)" stroke="var(--ink)" stroke-width="1.5"/>`;
  const sh = { ball: `<circle cx="160" cy="62" r="12" fill="var(--ink)"/>`, 'cone-down': `<path d="M148 54 L172 54 L160 76 Z" fill="var(--ink)"/>`, 'two-balls': `<circle cx="160" cy="50" r="10" fill="var(--ink)"/><circle cx="160" cy="76" r="10" fill="var(--ink)"/>`,
    'ball-diamond-ball': `<circle cx="160" cy="44" r="8" fill="var(--ink)"/><path d="M160 54 L170 66 L160 78 L150 66 Z" fill="var(--ink)"/><circle cx="160" cy="88" r="8" fill="var(--ink)"/>`, cylinder: `<rect x="150" y="48" width="20" height="30" fill="var(--ink)"/>`, 'two-cones': `<path d="M148 40 L172 40 L160 60 Z" fill="var(--ink)"/><path d="M148 84 L172 84 L160 64 Z" fill="var(--ink)"/>`, 'three-balls': `<circle cx="160" cy="46" r="8" fill="var(--ink)"/><circle cx="146" cy="68" r="8" fill="var(--ink)"/><circle cx="174" cy="68" r="8" fill="var(--ink)"/>` }[f.shape] || '';
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

function figSvg(spec) { const r = FIG[spec.type]; return r ? r(spec) : NS() + txt(160, 100, 'figure: ' + spec.type) + '</svg>'; }
function paintFigures(root = document) {
  root.querySelectorAll('[data-fig]').forEach(el => { if (el.dataset.figDone) return; try { el.innerHTML = figSvg(JSON.parse(el.dataset.fig)); } catch (e) { el.textContent = 'bad figure: ' + e.message; } el.dataset.figDone = 1; });
}
if (typeof module !== 'undefined') module.exports = { FIG, figSvg };
