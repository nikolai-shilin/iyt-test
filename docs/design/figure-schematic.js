/* Schematic plan views: the companion to every realistic figure. The same situation drawn from above in the
   app's figure language (figures.js): flat, theme tokens, Carlito, every marking explicit — headings, relative
   bearings, distances, wind, light arcs, mark types, who is who. Sized for a phone: big symbols, big type,
   the action filling the frame. schematic(spec) returns an SVG string. Coordinates: metres, north up, own boat
   at the origin unless the spec says otherwise; the frame is fitted round every boat and mark automatically. */

const SCH_TEXT = {};
const st = s => SCH_TEXT[s] ?? s;
const SRAD = Math.PI / 180;
const spol = (cx, cy, r, deg) => [cx + r * Math.sin(deg * SRAD), cy - r * Math.cos(deg * SRAD)];
const SCOL = { r: '#e0251b', g: '#1aa34a', w: '#ffffff', y: '#ffa800', k: 'var(--ink)', wind: '#e8231a', course: '#e0b400' };
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const stxt = (x, y, s, o = {}) => `<text x="${x}" y="${y}" font-size="${o.s || 26}" font-weight="${o.w || 700}" fill="${o.f || 'var(--muted)'}" text-anchor="${o.a || 'middle'}" ${o.extra || ''}>${esc(s)}</text>`;
const fmt3 = d => String(Math.round(((d % 360) + 360) % 360)).padStart(3, '0') + '°';

/* ---- primitives (plan view, pixel space) ---- */
/* a boat symbol: a plain hull, no sail, length ~ 44 before scale; the own boat gets the accent dot */
function sBoat(x, y, hdg, o = {}) {
  const s = o.scale || 2.6, fill = o.fill || 'var(--ink)';
  const body = `<path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="${fill}" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round"/>`;
  const dot = o.you ? `<circle cx="0" cy="-2" r="4" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.2"/>` : '';
  return `<g transform="translate(${x} ${y}) rotate(${hdg}) scale(${s})">${body}${dot}</g>`;
}
function sArrow(x1, y1, x2, y2, o = {}) {
  const c = o.c || 'var(--muted)', w = o.w || 4, a = Math.atan2(y2 - y1, x2 - x1), h = o.h || 16;
  const p1 = [x2 - h * Math.cos(a - .5), y2 - h * Math.sin(a - .5)], p2 = [x2 - h * Math.cos(a + .5), y2 - h * Math.sin(a + .5)];
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/><path d="M${x2} ${y2} L${p1[0]} ${p1[1]} L${p2[0]} ${p2[1]} Z" fill="${c}"/>`;
}
function sPill(x, y, text, kind = 'light', size = 26) {
  const w = text.length * size * 0.58 + size * 1.4, h = size * 1.7, fill = kind === 'accent' ? 'var(--accent)' : kind === 'red' ? SCOL.wind : 'var(--bg)';
  const ink = kind === 'light' ? 'var(--ink)' : '#fff', stroke = kind === 'light' ? 'var(--tag-line)' : fill;
  return `<rect x="${x - w / 2}" y="${y - h / 2}" width="${w}" height="${h}" rx="${h / 2}" fill="${fill}" stroke="${stroke}" stroke-width="3"/>${stxt(x, y + size * 0.36, text, { f: ink, s: size })}`;
}
function sCompass(x, y) {
  return `<g><circle cx="${x}" cy="${y}" r="40" fill="var(--bg)" stroke="var(--tag-line)" stroke-width="3"/>${sArrow(x, y + 24, x, y - 24, { c: 'var(--ink)', w: 4, h: 14 })}${stxt(x, y - 50, st('N'), { s: 26, f: 'var(--ink)' })}</g>`;
}
function sWind(x, y, from) {
  const [ax, ay] = spol(x, y, 50, from), [bx, by] = spol(x, y, 50, from + 180);
  return `<g>${sArrow(ax, ay, bx, by, { c: SCOL.wind, w: 9, h: 24 })}${sPill(x, y + 86, `${st('Wind')} ${fmt3(from)}`, 'red', 24)}</g>`;
}
function sScale(x, y, mpp, metres) {
  const px = metres / mpp;
  return `<g><line x1="${x}" y1="${y}" x2="${x + px}" y2="${y}" stroke="var(--ink)" stroke-width="4"/><line x1="${x}" y1="${y - 10}" x2="${x}" y2="${y + 10}" stroke="var(--ink)" stroke-width="4"/><line x1="${x + px}" y1="${y - 10}" x2="${x + px}" y2="${y + 10}" stroke="var(--ink)" stroke-width="4"/>${stxt(x + px / 2, y - 16, `${metres} m`, { s: 24 })}</g>`;
}
/* a heading line with the course in degrees at its tip */
function sHeading(x, y, hdg, L, side = 0) {
  const [tx, ty] = spol(x, y, L, hdg), [lx0, ly0] = spol(x, y, L + 34, hdg), [sx, sy] = spol(0, 0, 54 * side, hdg + 90);
  const lx = side ? tx + sx : lx0, ly = side ? ty + sy : ly0;
  return sArrow(x, y, tx, ty, { c: SCOL.course, w: 6, h: 20, dash: '14 10' }) + stxt(lx, ly + 9, fmt3(hdg), { s: 26, f: 'var(--ink)' });
}
/* a bearing line between two points, the relative bearing and distance on a pill beside its middle */
function sBearing(x1, y1, x2, y2, relDeg, metres, side = 1) {
  const t = 0.42, mx = x1 + (x2 - x1) * t, my = y1 + (y2 - y1) * t, a = Math.atan2(y2 - y1, x2 - x1), nx = -Math.sin(a) * 56 * side, ny = Math.cos(a) * 56 * side;
  const label = `${relDeg >= 0 ? st('stbd') : st('port')} ${String(Math.abs(Math.round(relDeg))).padStart(3, '0')}° · ${Math.round(metres)} m`;
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--muted)" stroke-width="3" stroke-dasharray="6 10"/>` + sPill(mx + nx, my + ny, label, 'light', 22);
}
/* light arcs: one compact ring hugging the hull. Red 112.5° to port, green 112.5° to starboard, white 135° astern;
   under power the white masthead arc (225° forward) is a thin second ring just outside. */
function sLightArcs(x, y, hdg, R, o = {}) {
  const arc = (from, to, c, r, w) => { const [ax, ay] = spol(x, y, r, hdg + from), [bx, by] = spol(x, y, r, hdg + to); const big = (to - from) > 180 ? 1 : 0; return `<path d="M${ax} ${ay} A${r} ${r} 0 ${big} 1 ${bx} ${by}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="butt"/>`; };
  let s = arc(-112.5, 0, SCOL.r, R, 10) + arc(0, 112.5, SCOL.g, R, 10) + arc(112.5, 247.5, '#c9ced3', R, 10);
  if (o.power) s += arc(-112.5, 112.5, '#c9ced3', R + 12, 5);
  return `<g>${s}</g>`;
}
/* IALA mark symbols (region A): big enough to read the bands and the topmark */
function sMark(x, y, kind, o = {}) {
  const r = 26, label = o.label;
  let g = '';
  if (kind.startsWith('card')) {
    const bands = { 'card-n': ['k', 'y'], 'card-s': ['y', 'k'], 'card-e': ['k', 'y', 'k'], 'card-w': ['y', 'k', 'y'] }[kind], n = bands.length;
    bands.forEach((b, i) => { g += `<rect x="${x - r}" y="${y - r + (2 * r) * i / n}" width="${2 * r}" height="${(2 * r) / n + 0.5}" fill="${SCOL[b]}"/>`; });
    g += `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="none" stroke="var(--ink)" stroke-width="3"/>`;
    const cone = (cy, up) => `<path d="M${x - 16} ${up ? cy + 14 : cy - 14} L${x} ${up ? cy - 14 : cy + 14} L${x + 16} ${up ? cy + 14 : cy - 14} Z" fill="var(--ink)"/>`;
    const tm = { 'card-n': [1, 1], 'card-s': [0, 0], 'card-e': [1, 0], 'card-w': [0, 1] }[kind];
    g += cone(y - r - 52, tm[0]) + cone(y - r - 20, tm[1]);
  } else if (kind === 'lat-port') {
    g += `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="${SCOL.r}" stroke="var(--ink)" stroke-width="3"/><rect x="${x - 14}" y="${y - r - 36}" width="28" height="28" fill="${SCOL.r}"/>`;
  } else if (kind === 'lat-stbd') {
    g += `<path d="M${x - r} ${y + r} L${x} ${y - r} L${x + r} ${y + r} Z" fill="${SCOL.g}" stroke="var(--ink)" stroke-width="3"/><path d="M${x - 14} ${y - r - 8} L${x} ${y - r - 40} L${x + 14} ${y - r - 8} Z" fill="${SCOL.g}"/>`;
  }
  if (label) g += stxt(x, y + r + 34, label, { s: 24, f: 'var(--ink)' });
  return `<g>${g}</g>`;
}

/* ---- the plan: a 1280 × 800 frame fitted round the action, the key along the bottom ---- */
function schematic(spec) {
  const W = 1280, H = 800, keyH = 40 + 40 * (spec.key || []).length + 24, boatPx = 44 * 3;
  // fit: the extent of all boats and marks, with room for labels, into the area above the key
  const pts = [...(spec.boats || []), ...(spec.marks || [])].map(p => [p.x, p.z]);
  const xs = pts.map(p => p[0]), zs = pts.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minZ = Math.min(...zs), maxZ = Math.max(...zs);
  const padPx = spec.padPx ?? 170, areaW = W - 2 * padPx, areaH = H - keyH - 2 * padPx;
  const spanX = Math.max(maxX - minX, 1), spanZ = Math.max(maxZ - minZ, 1);
  const mpp = spec.mpp ?? Math.max(spanX / areaW, spanZ / areaH, spec.minMpp ?? 0.08);
  const cx = W / 2 - (minX + maxX) / 2 / mpp + (spec.dx ?? 0), cy = padPx + areaH / 2 - (minZ + maxZ) / 2 / mpp + (spec.dz ?? 0);
  const P = (mx, mz) => [cx + mx / mpp, cy + mz / mpp]; // scene x east, z south (three.js: -z is north)
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">`;
  s += `<rect width="${W}" height="${H}" fill="var(--bg)"/>`;
  // a faint grid at a round number of metres
  const stepM = [5, 10, 20, 50, 100, 200, 500].find(m => m / mpp >= 110) || 500, step = stepM / mpp;
  for (let gx = cx % step; gx < W; gx += step) s += `<line x1="${gx}" y1="0" x2="${gx}" y2="${H - keyH}" stroke="var(--line)" stroke-width="2"/>`;
  for (let gy = cy % step; gy < H - keyH; gy += step) s += `<line x1="0" y1="${gy}" x2="${W}" y2="${gy}" stroke="var(--line)" stroke-width="2"/>`;
  s += sCompass(70, 76);
  if (spec.wind != null) s += sWind(W - 90, 90, spec.wind);
  s += sScale(30, H - keyH - 30, mpp, stepM);
  // marks
  for (const m of spec.marks || []) { const [x, y] = P(m.x, m.z); s += sMark(x, y, m.kind, { label: m.label }); }
  // bearing lines, under the boats
  const you = (spec.boats || []).find(b => b.you);
  const bearingTo = (t) => { const [x1, y1] = P(you.x, you.z), [x2, y2] = P(t.x, t.z); const dx = t.x - you.x, dz = t.z - you.z, abs = Math.atan2(dx, -dz) / SRAD, rel = ((abs - you.hdg + 540) % 360) - 180; return sBearing(x1, y1, x2, y2, rel, Math.hypot(dx, dz), t.side || 1); };
  for (const b of spec.boats || []) if (!b.you && you && b.bearing !== false) s += bearingTo(b);
  for (const m of spec.marks || []) if (you && m.bearing !== false) s += bearingTo(m);
  // boats: light ring at night, heading, hull, label, tag
  for (const b of spec.boats || []) {
    const [x, y] = P(b.x, b.z), sc = b.scale || 2.6, R = 26 * sc;
    if (spec.night) s += sLightArcs(x, y, b.hdg, R, { power: b.power });
    s += sHeading(x, y, b.hdg, R + 70, b.courseSide || 0);
    s += sBoat(x, y, b.hdg, { you: b.you, scale: sc, fill: b.fill });
    const above = b.labelAbove, ly = above ? y - R - (spec.night && b.power ? 14 : 0) - 64 : y + R + (spec.night && b.power ? 14 : 0) + 30;
    s += sPill(x, ly, b.label || (b.you ? st('You') : st('Other')), b.you ? 'accent' : 'light', 28);
    if (b.tag) s += stxt(x, above ? ly + 52 : ly + 52, b.tag, { s: 24, f: 'var(--ink)', w: 400 });
  }
  // key along the bottom
  s += `<rect x="0" y="${H - keyH}" width="${W}" height="${keyH}" fill="var(--band)"/>`;
  let ky = H - keyH + 40;
  s += stxt(30, ky, spec.title || '', { s: 30, f: 'var(--ink)', a: 'start' });
  for (const line of spec.key || []) { ky += 40; s += stxt(30, ky, '· ' + line, { s: 27, w: 400, f: 'var(--ink)', a: 'start' }); }
  return s + '</svg>';
}

if (typeof window !== 'undefined') { window.schematic = schematic; window.SCH_TEXT = SCH_TEXT; }
