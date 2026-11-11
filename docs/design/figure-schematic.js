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
const TS = 1.7;   // every label 70% larger than first drawn: a question shows its plan ~340 px wide on a phone
const stxt = (x, y, s, o = {}) => `<text x="${x}" y="${y}" font-size="${Math.round((o.s || 26) * TS)}" font-weight="${o.w || 700}" fill="${o.f || 'var(--muted)'}" text-anchor="${o.a || 'middle'}" ${o.extra || ''}>${esc(s)}</text>`;
const fmt3 = d => String(Math.round(((d % 360) + 360) % 360)).padStart(3, '0') + '°';

/* ---- primitives (plan view, pixel space) ---- */
/* a boat symbol: a plain hull, no sail, length ~ 44 before scale; the own boat gets the accent dot */
function sBoat(x, y, hdg, o = {}) {
  const s = o.scale || 2.6, fill = o.fill || 'var(--ink)';
  const body = `<path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="${fill}" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round"/>` +
    // the deck from above: a toe rail inside the sheer, the coachroof, the cockpit well, the mast and the bow pulpit
    `<path d="M0 -19 C 5.5 -12.5 6.4 5 4.8 16.2 L -4.8 16.2 C -6.4 5 -5.5 -12.5 0 -19 Z" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width=".7"/>` +
    `<rect x="-3.6" y="-8" width="7.2" height="11" rx="2" fill="#fff" fill-opacity=".2"/><rect x="-3.4" y="5.5" width="6.8" height="9" rx="1.2" fill="#000" fill-opacity=".3"/>` +
    `<circle cx="0" cy="-9.5" r="1.5" fill="#fff" fill-opacity=".85"/><path d="M-2.6 -17 Q0 -21.5 2.6 -17" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width=".7"/>`;
  const dot = o.you ? `<circle cx="0" cy="-2" r="4" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.2"/>` : '';
  return `<g transform="translate(${x} ${y}) rotate(${hdg}) scale(${s})">${body}${dot}</g>`;
}
function sArrow(x1, y1, x2, y2, o = {}) {
  const c = o.c || 'var(--muted)', w = o.w || 4, a = Math.atan2(y2 - y1, x2 - x1), h = o.h || 16;
  const p1 = [x2 - h * Math.cos(a - .5), y2 - h * Math.sin(a - .5)], p2 = [x2 - h * Math.cos(a + .5), y2 - h * Math.sin(a + .5)];
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${o.dash ? `stroke-dasharray="${o.dash}"` : ''}/><path d="M${x2} ${y2} L${p1[0]} ${p1[1]} L${p2[0]} ${p2[1]} Z" fill="${c}"/>`;
}
function sPill(x, y, text, kind = 'light', size = 26) {
  size = Math.round(size * TS);
  const w = text.length * size * 0.58 + size * 1.4, h = size * 1.7, fill = kind === 'accent' ? 'var(--accent)' : kind === 'red' ? SCOL.wind : 'var(--bg)';
  const ink = kind === 'light' ? 'var(--ink)' : '#fff', stroke = kind === 'light' ? 'var(--tag-line)' : fill;
  return `<rect x="${x - w / 2}" y="${y - h / 2}" width="${w}" height="${h}" rx="${h / 2}" fill="${fill}" stroke="${stroke}" stroke-width="3"/>${stxt(x, y + size * 0.36, text, { f: ink, s: size / TS })}`;
}
function sCompass(x, y) {
  const ticks = [0, 45, 90, 135, 180, 225, 270, 315].map(d => { const [a, b] = spol(x, y, d % 90 ? 34 : 30, d), [c, e] = spol(x, y, 40, d); return `<line x1="${a}" y1="${b}" x2="${c}" y2="${e}" stroke="var(--ink)" stroke-width="${d % 90 ? 2 : 3}"/>`; }).join('');
  return `<g><circle cx="${x}" cy="${y}" r="40" fill="var(--bg)" stroke="var(--tag-line)" stroke-width="3"/>${ticks}${sArrow(x, y + 24, x, y - 24, { c: 'var(--ink)', w: 4, h: 14 })}${stxt(x, y - 52, st('N'), { s: 26, f: 'var(--ink)' })}</g>`;
}
function sWind(x, y, from) {
  const [ax, ay] = spol(x, y, 50, from), [bx, by] = spol(x, y, 50, from + 180);
  return `<g>${sArrow(ax, ay, bx, by, { c: SCOL.wind, w: 9, h: 24 })}${sPill(x, y + 104, `${st('Wind')} ${fmt3(from)}`, 'red', 24)}</g>`;
}
function sScale(x, y, mpp, metres) {
  const px = metres / mpp;
  // a chart's scale bar: four alternating ink and white segments in a frame
  let bars = ''; for (let i = 0; i < 4; i++) bars += `<rect x="${x + i * px / 4}" y="${y - 5}" width="${px / 4}" height="10" fill="${i % 2 ? 'var(--bg)' : 'var(--ink)'}"/>`;
  // starts with a line at x 30: the pages drop the scale bar (noScale) by matching <g><line x1="30"
  return `<g><line x1="${x}" y1="${y}" x2="${x}" y2="${y}" stroke="none"/>${bars}<rect x="${x}" y="${y - 5}" width="${px}" height="10" fill="none" stroke="var(--ink)" stroke-width="2.5"/>${stxt(Math.max(x + px / 2, x + 56), y - 18, `${metres} m`, { s: 24, f: 'var(--ink)' })}</g>`;
}
/* a heading line with the course in degrees at its tip */
function sHeading(x, y, hdg, L, side = 0, clamp) {
  const [tx, ty] = spol(x, y, L, hdg), [lx0, ly0] = spol(x, y, L + 58, hdg), [sx, sy] = spol(0, 0, 54 * side, hdg + 90);
  let lx = side ? tx + sx : lx0, ly = side ? ty + sy : ly0;
  if (clamp) { const z = 26 * TS; [lx, ly] = clamp(lx, ly - z * 0.35, 4 * z * 0.55, z * 1.1); ly += z * 0.35; }
  return sArrow(x, y, tx, ty, { c: SCOL.course, w: 6, h: 20, dash: '14 10' }) + stxt(lx, ly + (clamp ? 0 : 15), fmt3(hdg), { s: 26, f: 'var(--ink)' });
}
/* a bearing line between two points, the relative bearing and distance on a pill beside its middle */
function sBearing(x1, y1, x2, y2, relDeg, metres, side = 1, placer) {
  const t = 0.42, mx = x1 + (x2 - x1) * t, my = y1 + (y2 - y1) * t, a = Math.atan2(y2 - y1, x2 - x1), nx = -Math.sin(a) * 78 * side, ny = Math.cos(a) * 78 * side;
  const label = `${relDeg >= 0 ? st('stbd') : st('port')} ${String(Math.abs(Math.round(relDeg))).padStart(3, '0')}° · ${Math.round(metres)} m`;
  let [px, py, sz] = [mx + nx, my + ny, 22]; if (placer) [px, py, sz] = placer(px, py, label, 22);
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--muted)" stroke-width="3" stroke-dasharray="6 10"/>` + sPill(px, py, label, 'light', sz);
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
  } else if (['iso', 'safe', 'special', 'wreck'].includes(kind)) {
    const box = `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="none" stroke="var(--ink)" stroke-width="3"/>`;
    if (kind === 'iso') ['k', 'r', 'k'].forEach((b, i) => { g += `<rect x="${x - r}" y="${y - r + (2 * r) * i / 3}" width="${2 * r}" height="${(2 * r) / 3 + 0.5}" fill="${SCOL[b]}"/>`; });
    if (kind === 'special') g += `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="${SCOL.y}"/>`;
    if (kind === 'safe' || kind === 'wreck') { const [c1, c2] = kind === 'safe' ? [SCOL.r, '#ffffff'] : ['#1446a0', SCOL.y]; for (let i = 0; i < 4; i++) g += `<rect x="${x - r + i * r / 2}" y="${y - r}" width="${r / 2 + 0.5}" height="${2 * r}" fill="${i % 2 ? c2 : c1}"/>`; }
    g += box;
    const ty = y - r - 22;
    if (kind === 'iso') g += `<circle cx="${x}" cy="${ty}" r="11" fill="var(--ink)"/><circle cx="${x}" cy="${ty - 26}" r="11" fill="var(--ink)"/>`;
    if (kind === 'safe') g += `<circle cx="${x}" cy="${ty}" r="13" fill="${SCOL.r}" stroke="var(--ink)" stroke-width="2"/>`;
    if (kind === 'special') g += `<path d="M${x - 14} ${ty - 14} L${x + 14} ${ty + 14} M${x + 14} ${ty - 14} L${x - 14} ${ty + 14}" stroke="${SCOL.y}" stroke-width="9" stroke-linecap="round"/><path d="M${x - 14} ${ty - 14} L${x + 14} ${ty + 14} M${x + 14} ${ty - 14} L${x - 14} ${ty + 14}" stroke="var(--ink)" stroke-width="2" stroke-linecap="round" opacity=".5"/>`;
    if (kind === 'wreck') g += `<path d="M${x} ${ty - 18} L${x} ${ty + 14} M${x - 15} ${ty - 2} L${x + 15} ${ty - 2}" stroke="${SCOL.y}" stroke-width="9" stroke-linecap="round"/>`;
  }
  if (o.hi) g = `<circle cx="${x}" cy="${y - 14}" r="${r + 40}" fill="rgba(255,230,0,.16)" stroke="${SCOL.course}" stroke-width="5"/>` + g;
  if (label) g += stxt(x, y + r + 54, label, { s: 24, f: 'var(--ink)' });
  return `<g>${g}</g>`;
}

/* a lettered spot: a yellow ring with its letter, as the questions mark candidate anchorages */
function sSpot(x, y, letter) {
  return `<circle cx="${x}" cy="${y}" r="34" fill="rgba(255,230,0,.16)" stroke="${SCOL.course}" stroke-width="7"/>${stxt(x, y + 14, letter, { s: 24, f: 'var(--ink)' })}`;
}
/* an anchor glyph: ring, shank, stock and arms */
function sAnchor(x, y, s = 1) {
  const k = 'var(--ink)';
  return `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${k}" stroke-width="6" stroke-linecap="round"><circle cx="0" cy="-30" r="8"/><line x1="0" y1="-22" x2="0" y2="28"/><line x1="-16" y1="-10" x2="16" y2="-10"/><path d="M-26 8 C -24 26 -12 32 0 32 C 12 32 24 26 26 8"/><path d="M-30 14 L-26 6 L-18 12 M30 14 L26 6 L18 12"/></g>`;
}
/* a rock: the chart's danger, an awash rock in a dotted danger line */
function sRock(x, y) {
  return `<g><circle cx="${x}" cy="${y}" r="40" fill="none" stroke="var(--ink)" stroke-width="3" stroke-dasharray="3 7"/><path d="M${x - 20} ${y} L${x + 20} ${y} M${x} ${y - 20} L${x} ${y + 20}" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/><circle cx="${x - 12}" cy="${y - 12}" r="4" fill="var(--ink)"/><circle cx="${x + 12}" cy="${y - 12}" r="4" fill="var(--ink)"/><circle cx="${x - 12}" cy="${y + 12}" r="4" fill="var(--ink)"/><circle cx="${x + 12}" cy="${y + 12}" r="4" fill="var(--ink)"/></g>`;
}
/* a wreck: the chart's dangerous-wreck symbol, a hull line with masts inside a dotted danger line */
function sWreck(x, y) {
  return `<g><ellipse cx="${x}" cy="${y}" rx="52" ry="34" fill="none" stroke="var(--ink)" stroke-width="3" stroke-dasharray="3 7"/><path d="M${x - 34} ${y} L${x + 34} ${y} M${x - 16} ${y - 14} L${x - 16} ${y + 14} M${x} ${y - 18} L${x} ${y + 18} M${x + 16} ${y - 14} L${x + 16} ${y + 14}" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/></g>`;
}
/* a measured distance: a thin line with end ticks and the figure on a pill */
function sDim(x1, y1, x2, y2, text, off = 0) {
  const a = Math.atan2(y2 - y1, x2 - x1), nx = -Math.sin(a) * off, ny = Math.cos(a) * off;
  const t = (x, y) => `<line x1="${x - Math.sin(a) * 14}" y1="${y + Math.cos(a) * 14}" x2="${x + Math.sin(a) * 14}" y2="${y - Math.cos(a) * 14}" stroke="var(--ink)" stroke-width="4"/>`;
  return `<g><line x1="${x1 + nx}" y1="${y1 + ny}" x2="${x2 + nx}" y2="${y2 + ny}" stroke="var(--ink)" stroke-width="4"/>${t(x1 + nx, y1 + ny)}${t(x2 + nx, y2 + ny)}${sPill((x1 + x2) / 2 + nx, (y1 + y2) / 2 + ny, text, 'light', 24)}</g>`;
}

/* the key band along the bottom: the title and its lines, wrapped to the frame's width so the larger type fits */
function sKeyLines(spec, W) {
  const wrap = (text, size) => { const max = Math.floor((W - 60) / (size * TS * 0.58)), out = []; let cur = '';
    for (const w of String(text).split(' ')) { if (cur && (cur + ' ' + w).length > max) { out.push(cur); cur = w; } else cur = cur ? cur + ' ' + w : w; }
    if (cur) out.push(cur); return out; };
  const lines = [];
  wrap(spec.title || '', 30).forEach(t => lines.push({ t, s: 30, w: 700, h: lines.length ? 54 : 0 }));
  for (const k of spec.key || []) wrap('· ' + k, 27).forEach((t, i) => lines.push({ t: i ? '  ' + t : t, s: 27, w: 400, h: i ? 50 : 60 }));
  const keyH = 66 + lines.reduce((a, l) => a + l.h, 0) + 30;
  // the drawing keeps the height it had with the first, smaller key (800 less 40 a line); the frame grows to fit the key
  return { lines, keyH, H: 800 - (40 + 40 * (spec.key || []).length + 24) + keyH };
}
function sKey(lines, W, top, keyH) {
  let s = `<rect x="0" y="${top}" width="${W}" height="${keyH}" fill="var(--band)"/>`, ky = top + 64;
  for (const l of lines) { ky += l.h; s += stxt(30, ky, l.t, { s: l.s, w: l.w, f: 'var(--ink)', a: 'start', extra: 'xml:space="preserve"' }); }
  return s;
}

/* ---- the plan: a 1280 × 800 frame fitted round the action, the key along the bottom ---- */
function schematic(spec) {
  const W = 1280, { lines: keyLines, keyH, H } = sKeyLines(spec, W), boatPx = 44 * 3;
  // fit: the extent of all boats and marks, with room for labels, into the area above the key
  const pts = [...(spec.boats || []), ...(spec.marks || []), ...(spec.spots || []), ...(spec.anchors || []), ...(spec.rocks || []), ...(spec.wrecks || []), ...(spec.texts || []).filter(t => !t.free), ...(spec.fit || [])].map(p => [p.x, p.z]);
  for (const c of spec.circles || []) pts.push([c.x - c.r, c.z - c.r], [c.x + c.r, c.z + c.r]);
  for (const pth of [...(spec.paths || []), ...(spec.zones || [])]) for (const [x, z] of pth.pts) pts.push([x, z]);
  const xs = pts.map(p => p[0]), zs = pts.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minZ = Math.min(...zs), maxZ = Math.max(...zs);
  const padPx = spec.padPx ?? 170, areaW = W - 2 * padPx, areaH = H - keyH - 2 * padPx;
  const spanX = Math.max(maxX - minX, 1), spanZ = Math.max(maxZ - minZ, 1);
  const mpp = spec.mpp ?? Math.max(spanX / areaW, spanZ / areaH, spec.minMpp ?? 0.08);
  const cx = W / 2 - (minX + maxX) / 2 / mpp + (spec.dx ?? 0), cy = padPx + areaH / 2 - (minZ + maxZ) / 2 / mpp + (spec.dz ?? 0);
  const P = (mx, mz) => [cx + mx / mpp, cy + mz / mpp]; // scene x east, z south (three.js: -z is north)
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">`;
  s += `<rect width="${W}" height="${H}" fill="var(--bg)"/><rect width="${W}" height="${H - keyH}" fill="rgba(60,140,190,.07)"/>`;
  // a faint grid at a round number of metres
  const stepM = [5, 10, 20, 50, 100, 200, 500].find(m => m / mpp >= 110) || 500, step = stepM / mpp;
  for (let gx = cx % step; gx < W; gx += step) s += `<line x1="${gx}" y1="0" x2="${gx}" y2="${H - keyH}" stroke="var(--line)" stroke-width="2"/>`;
  for (let gy = cy % step; gy < H - keyH; gy += step) s += `<line x1="0" y1="${gy}" x2="${W}" y2="${gy}" stroke="var(--line)" stroke-width="2"/>`;
  // label placement: every label stays inside the drawing, and the free notes (spec.texts) move to the nearest clear
  // spot so the larger type does not cover a boat, a mark, the wind or another label
  const planB = H - keyH, boxes = [[16, 30, 136, 166]];
  const solids = [], lands = [], inPoly = (q, px, py) => { let c = false; for (let i = 0, j = q.length - 1; i < q.length; j = i++) { const [xi, yi] = q[i], [xj, yj] = q[j]; if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) c = !c; } return c; };
  const onLand = (b) => lands.reduce((n, q) => n + [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]], [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]].filter(([x, y]) => inPoly(q, x, y)).length, 0), ov = (b, o) => Math.max(0, Math.min(b[2], o[2]) - Math.max(b[0], o[0])) * Math.max(0, Math.min(b[3], o[3]) - Math.max(b[1], o[1]));
  const hit = (b, pill = true) => b[0] < 14 || b[2] > W - 14 || b[1] < 10 || b[3] > planB - 10 || boxes.some(o => ov(b, o) > 0) || (pill && (solids.some(o => ov(b, o) > 0) || onLand(b) > 0));
  const pillWH = (text, size) => { const z = Math.round(size * TS); return [String(text).length * z * 0.58 + z * 1.4, z * 1.7]; };
  const inFrame = (x, y, w, h) => [Math.min(Math.max(x, w / 2 + 16), W - w / 2 - 16), Math.min(Math.max(y, h / 2 + 12), planB - h / 2 - 12)];
  const box = (x, y, w, h) => [x - w / 2, y - h / 2, x + w / 2, y + h / 2];
  // the nearest clear spot; when there is none, the spot that covers least of what is already there
  const place = (x, y, w, h, pill = true, reach = 5) => { const cands = [];
    for (let k = 0; k <= reach; k++) for (const [dx, dy] of [[0, 0], [0, -1], [0, 1], [1, 0], [-1, 0], [1, -1], [-1, -1], [1, 1], [-1, 1]]) if (k || (!dx && !dy)) cands.push([x + dx * k * w * 0.3, y + dy * k * h * 0.7]);
    // cost: what the label would cover, plus how far it strays from its spot, so a far clear place does not win over a
    // slight overlap close by and a label stays next to what it names
    let best = null, bestCost = Infinity;
    for (const [cx, cy] of cands) { const [px, py] = inFrame(cx, cy, w, h), b = box(px, py, w, h);
      const cost = boxes.reduce((a, o) => a + ov(b, o), 0) * 10 + (pill ? (solids.reduce((a, o) => a + ov(b, o), 0) + onLand(b) * w * h / 5) * 3 : 0) + Math.hypot(px - x, py - y) * h * 1.2;
      if (cost < bestCost) { bestCost = cost; best = [px, py]; } }
    boxes.push(box(best[0], best[1], w, h)); return best; };
  // a label stays at the spot it was designed for, or a short step from it; where that would cover something it
  // gets a size smaller (1.7x, then about 1.45x and 1.25x of the first drawings) rather than wander off from what it names
  const fit = (x, y, text, size, pill = true) => {
    const dims = (sz) => pill ? pillWH(text, sz) : [String(text).length * sz * TS * 0.56, sz * TS * 1.1];
    const near = (w, h) => { const c = []; for (let k = 0; k <= 2; k++) for (const [dx, dy] of [[0, 0], [0, -1], [0, 1], [1, 0], [-1, 0], [1, -1], [-1, -1], [1, 1], [-1, 1]]) if (k || (!dx && !dy)) c.push([x + dx * k * Math.min(w * 0.2, 70), y + dy * k * h * 0.6]); return c; };
    for (const k of [1, 0.85, 0.74]) { const sz = size * k, [w, h] = dims(sz);
      for (const [cx, cy] of near(w, h)) { const [px, py] = inFrame(cx, cy, w, h), b = box(px, py, w, h); if (!hit(b, pill)) { boxes.push(b); return [px, py, sz]; } } }
    const sz = size * 0.74, [w, h] = dims(sz); let best = null, bestCost = Infinity;
    for (const [cx, cy] of near(w, h)) { const [px, py] = inFrame(cx, cy, w, h), b = box(px, py, w, h);
      const cost = boxes.reduce((a, o) => a + ov(b, o), 0) * 10 + (pill ? (solids.reduce((a, o) => a + ov(b, o), 0) + onLand(b) * w * h / 5) * 3 : 0) + Math.hypot(px - x, py - y) * h;
      if (cost < bestCost) { bestCost = cost; best = [px, py]; } }
    boxes.push(box(best[0], best[1], w, h)); return [best[0], best[1], sz];
  };
  const clampText = (x, y) => [Math.min(Math.max(x, 50), W - 50), Math.min(Math.max(y, 44), planB - 12)];
  if (spec.wind != null) { const [ww, wh] = pillWH(`${st('Wind')} 000°`, 24); boxes.push([W - 170 - Math.max(60, ww / 2), 20, W - 170 + Math.max(60, ww / 2), 80 + 104 + wh / 2]); }
  { const sb = [5, 10, 20, 50, 100, 200, 500].find(m => m / mpp >= 110) || 500; boxes.push([20, planB - 30 - 52, 40 + sb / mpp, planB - 18]); }
  // land: sand and scrub, a dark coastline
  for (const poly of spec.land || []) {
    const q = poly.map(([x, z]) => P(x, z)); lands.push(q); const d = q.map((p, i) => (i ? 'L' : 'M') + p.map(v => v.toFixed(1)).join(' ')).join(' ') + ' Z';
    const inside = (px, py) => { let c = false; for (let i = 0, j = q.length - 1; i < q.length; j = i++) { const [xi, yi] = q[i], [xj, yj] = q[j]; if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) c = !c; } return c; };
    const cid = 'land' + (s.length % 100000);
    s += `<clipPath id="${cid}"><path d="${d}"/></clipPath><path d="${d}" fill="#e6d9b4" stroke="none"/><path d="${d}" fill="none" stroke="#f1e9cd" stroke-width="40" stroke-linejoin="round" clip-path="url(#${cid})"/>`;
    let scrub = ''; for (let gx = 20; gx < W; gx += 58) for (let gy = 20; gy < H - keyH; gy += 50) { const jx = gx + ((gy * 7) % 23) - 11, jy = gy + ((gx * 5) % 19) - 9;
      if (inside(jx, jy) && inside(jx + 26, jy) && inside(jx - 26, jy) && inside(jx, jy + 26) && inside(jx, jy - 26)) scrub += `<circle cx="${jx}" cy="${jy}" r="${5 + (gx + gy) % 4}" fill="#9aae6e" fill-opacity=".75"/>`; }
    s += scrub + `<path d="${d}" fill="none" stroke="#6b5a3a" stroke-width="5" stroke-linejoin="round"/>`;
  }
  for (const q of spec.quays || []) { const [x1, y1] = P(q.x1, q.z1), [x2, y2] = P(q.x2, q.z2); solids.push([Math.min(x1, x2), Math.min(y1, y2), Math.max(x1, x2), Math.max(y1, y2)]); s += `<rect x="${Math.min(x1, x2)}" y="${Math.min(y1, y2)}" width="${Math.abs(x2 - x1)}" height="${Math.abs(y2 - y1)}" fill="#bdb8ad" stroke="var(--ink)" stroke-width="4"/>`; }
  // zones: an area on the chart, dashed outline and a pale fill
  for (const z of spec.zones || []) { const q = z.pts.map(([x, zz]) => P(x, zz)); const c = z.c === 'red' ? SCOL.wind : z.c === 'ink' ? 'var(--ink)' : SCOL.course;
    s += `<path d="${q.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')} Z" fill="${z.fill || 'rgba(255,200,0,.12)'}" stroke="${c}" stroke-width="5" stroke-dasharray="${z.dash || '14 10'}"/>`; }
  // circles: a swing circle, dashed
  for (const c of spec.circles || []) { const [x, y] = P(c.x, c.z); s += `<circle cx="${x}" cy="${y}" r="${c.r / mpp}" fill="${c.fill || 'none'}" stroke="${c.c === 'red' ? SCOL.wind : c.c === 'ink' ? 'var(--ink)' : SCOL.course}" stroke-width="6" stroke-dasharray="${c.dash || '16 12'}"/>`; }
  // paths: a track, a course, a mooring line
  for (const pth of spec.paths || []) { const q = pth.pts.map(([x, z]) => P(x, z)); const c = pth.c === 'line' ? '#8a6a3a' : pth.c === 'red' ? SCOL.wind : pth.c === 'ink' ? 'var(--ink)' : SCOL.course;
    s += `<path d="${q.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')}" fill="none" stroke="${c}" stroke-width="${pth.w || 6}" stroke-linecap="round" stroke-linejoin="round" ${pth.dash ? `stroke-dasharray="${pth.dash}"` : ''}/>`;
    if (pth.arrow) { const [a, b] = q.slice(-2); s += sArrow(a[0], a[1], b[0], b[1], { c, w: pth.w || 6, h: 22 }); } }
  for (const d of spec.dims || []) { const [x1, y1] = P(d.a[0], d.a[1]), [x2, y2] = P(d.b[0], d.b[1]); s += sDim(x1, y1, x2, y2, d.text, d.off || 0); const a = Math.atan2(y2 - y1, x2 - x1), o = d.off || 0, [w, h] = pillWH(d.text, 24); boxes.push(box((x1 + x2) / 2 - Math.sin(a) * o, (y1 + y2) / 2 + Math.cos(a) * o, w, h)); }
  for (const r of spec.wrecks || []) { const [x, y] = P(r.x, r.z); s += sWreck(x, y); boxes.push([x - 56, y - 40, x + 56, y + (r.label ? 104 : 40)]); if (r.label) s += stxt(x, y + 90, r.label, { s: 24, f: 'var(--ink)' }); }
  for (const r of spec.rocks || []) { const [x, y] = P(r.x, r.z); s += sRock(x, y); boxes.push([x - 44, y - 44, x + 44, y + (r.label ? 106 : 44)]); if (r.label) s += stxt(x, y + 92, r.label, { s: 24, f: 'var(--ink)' }); }
  for (const a of spec.anchors || []) { const [x, y] = P(a.x, a.z); s += sAnchor(x, y, a.s || 1); boxes.push([x - 34 * (a.s || 1), y - 40 * (a.s || 1), x + 34 * (a.s || 1), y + (a.label ? 102 : 36 * (a.s || 1))]); if (a.label) s += stxt(x, y + 88, a.label, { s: 24, f: 'var(--ink)' }); }
  for (const sp of spec.spots || []) { const [x, y] = P(sp.x, sp.z); s += sSpot(x, y, sp.label); boxes.push([x - 40, y - 40, x + 40, y + 40]); }
  // marks
  for (const m of spec.marks || []) { const [x, y] = P(m.x, m.z); s += sMark(x, y, m.kind, { label: m.label, hi: m.hi }); boxes.push(m.hi ? [x - 70, y - 100, x + 70, y + (m.label ? 80 : 56)] : [x - 40, y - 100, x + 40, y + (m.label ? 80 : 30)]); }
  // bearing lines, under the boats
  for (const b of spec.boats || []) { const [x, y] = P(b.x, b.z), R0 = 26 * (spec.trueScale ? ((b.L || 12) / mpp) / 40 : (b.scale || 2.6)); boxes.push([x - R0, y - R0, x + R0, y + R0]); }
  for (const b of spec.boats || []) if (b.stack) { const [x, y] = P(b.x, b.z), R0 = 26 * (b.scale || 2.6), sx = x + (b.stackDx ?? R0 + 70), n = b.stack.length, sy0 = y - (n - 1) * 23; boxes.push([sx - 30, sy0 - 34, sx + 30, sy0 + (n - 1) * 46 + 34]); }
  for (const b of spec.boats || []) if (!b.plain && !b.noHeading) { const [x, y] = P(b.x, b.z), R0 = 26 * (spec.trueScale ? ((b.L || 12) / mpp) / 40 : (b.scale || 2.6)), L = R0 + 70, side = b.courseSide || 0;
    const [tx, ty] = spol(x, y, L, b.hdg), [lx0, ly0] = spol(x, y, L + 58, b.hdg), [sx, sy] = spol(0, 0, 54 * side, b.hdg + 90), z = 26 * TS, w = 4 * z * 0.55, h = z * 1.1;
    const [px, py] = inFrame(side ? tx + sx : lx0, (side ? ty + sy : ly0) - z * 0.35, w, h); boxes.push(box(px, py, w, h)); }
  // each boat's name pill is reserved next to her first (below, above, then beside), before the bearings and notes
  const boatLab = new Map();
  for (const b of spec.boats || []) { if (b.plain) continue;
    const [x, y] = P(b.x, b.z), R0 = 26 * (spec.trueScale ? ((b.L || 12) / mpp) / 40 : (b.scale || 2.6)) + (spec.night && b.power ? 14 : 0);
    const lab = b.label || (b.you ? st('You') : st('Other')), g = 12;
    const others = (spec.boats || []).filter(o => o !== b).map(o => P(o.x, o.z)), mine = (px, py) => others.every(([ox, oy]) => Math.hypot(px - ox, py - oy) > Math.hypot(px - x, py - y));
    const tw = b.tag ? String(b.tag).length * 24 * TS * 0.52 : 0, th = 24 * TS * 1.15;
    const spots = (w, h) => { const below = [x, y + R0 + g + h / 2], above = [x, y - R0 - g - h / 2 - 8], right = [x + R0 + g + w / 2, y], left = [x - R0 - g - w / 2, y]; return b.labelAbove ? [above, below, right, left] : [below, above, right, left]; };
    const tagBox = (px, py, h, up) => box(px, up ? py - h / 2 - 10 - th / 2 : py + h / 2 + 10 + th / 2, tw, th);
    // beside her at full size, then a size smaller; never nearer another boat than her own
    let pos = null, up = false, lsz = 28, w, h;
    for (const k of [1, 0.85]) { lsz = 28 * k; [w, h] = pillWH(lab, lsz);
      for (const [cx, cy] of spots(w, h)) { const [px, py] = inFrame(cx, cy, w, h), bb = box(px, py, w, h); if (hit(bb) || !mine(px, py)) continue;
        if (!b.tag || !hit(tagBox(px, py, h, false))) { pos = [px, py]; break; } if (!hit(tagBox(px, py, h, true))) { pos = [px, py]; up = true; break; } }
      if (pos) break; }
    if (!pos) { lsz = 28 * 0.85; [w, h] = pillWH(lab, lsz); let best = Infinity;   // nowhere clear: the spot beside her that covers least
      for (const [cx, cy] of spots(w, h)) { const [px, py] = inFrame(cx, cy, w, h); if (!mine(px, py)) continue;
        for (const u of b.tag ? [false, true] : [false]) { const bs = [box(px, py, w, h), ...(b.tag ? [tagBox(px, py, h, u)] : [])];
          const cost = bs.reduce((a, bb) => a + boxes.reduce((t, o) => t + ov(bb, o), 0) + (bb[3] > planB - 10 || bb[1] < 10 ? w * h : 0), 0);
          if (cost < best) { best = cost; pos = [px, py]; up = u; } } }
      if (!pos) { const c = spots(w, h); pos = inFrame(...c[0], w, h); } }
    boxes.push(box(pos[0], pos[1], w, h)); if (b.tag) boxes.push(tagBox(pos[0], pos[1], h, up)); boatLab.set(b, { lab, pos, h, up, lsz });
  }
  const you = (spec.boats || []).find(b => b.you);
  const bearingTo = (t) => { const [x1, y1] = P(you.x, you.z), [x2, y2] = P(t.x, t.z); const dx = t.x - you.x, dz = t.z - you.z, abs = Math.atan2(dx, -dz) / SRAD, rel = ((abs - you.hdg + 540) % 360) - 180; return sBearing(x1, y1, x2, y2, rel, Math.hypot(dx, dz), t.side || 1, fit); };
  for (const b of spec.boats || []) if (!b.you && !b.plain && you && b.bearing !== false) s += bearingTo(b);
  for (const m of spec.marks || []) if (you && m.bearing !== false) s += bearingTo(m);
  // boats: light ring at night, heading, hull, label, tag
  for (const b of spec.boats || []) {
    const [x, y] = P(b.x, b.z), sc = spec.trueScale ? ((b.L || 12) / mpp) / 40 : (b.scale || 2.6), R = 26 * sc;
    if (b.plain) { s += sBoat(x, y, b.hdg, { scale: sc, fill: 'var(--muted)' }); continue; }
    if (spec.night && b.anchorLight) s += `<circle cx="${x}" cy="${y}" r="${R + 18}" fill="none" stroke="#ffffff" stroke-width="10"/><circle cx="${x}" cy="${y}" r="${R + 18}" fill="none" stroke="var(--ink)" stroke-width="2"/>`;
    else if (spec.night) s += sLightArcs(x, y, b.hdg, R, { power: b.power });
    if (!b.noHeading) s += sHeading(x, y, b.hdg, R + 70, b.courseSide || 0, (hx, hy, w, h) => inFrame(hx, hy, w, h));
    s += sBoat(x, y, b.hdg, { you: b.you, scale: sc, fill: b.fill });
    const above = b.labelAbove, ly = above ? y - R - (spec.night && b.power ? 14 : 0) - 80 : y + R + (spec.night && b.power ? 14 : 0) + 48;
    const { lab, pos: [lpx, lpy], h: lh, up: tagUp, lsz } = boatLab.get(b);
    s += sPill(lpx, lpy, lab, b.you ? 'accent' : 'light', lsz);
    if (b.tag) { const ty = tagUp ? lpy - lh / 2 - 10 - 24 * TS * 0.3 : lpy + lh / 2 + 10 + 24 * TS * 0.85; s += stxt(lpx, ty, b.tag, { s: 24, f: 'var(--ink)', w: 400 }); }
    if (b.stack) { const sx = x + (b.stackDx ?? R + 70), n = b.stack.length, sy0 = y - (n - 1) * 23;
      s += `<rect x="${sx - 26}" y="${sy0 - 30}" width="52" height="${(n - 1) * 46 + 60}" rx="26" fill="#10161f"/>`;
      b.stack.forEach((c, i) => { s += `<circle cx="${sx}" cy="${sy0 + i * 46}" r="16" fill="${SCOL[c]}" stroke="${c === 'w' ? '#9aa4ae' : 'none'}" stroke-width="2"/>`; }); }
  }
  for (const t of spec.texts || []) { const [x, y] = P(t.x, t.z);
    if (t.pill === false) { const s0 = (t.size || 26) * 1.45 / TS, [px, py, sz] = fit(x, y - s0 * TS * 0.35, t.text, s0, false); s += stxt(px, py + sz * TS * 0.35, t.text, { s: sz, f: 'var(--ink)' }); }
    else { const [px, py, sz] = fit(x, y, t.text, t.size || 24); s += sPill(px, py, t.text, t.kind || 'light', sz); } }
  // the compass, the wind and the scale bar on top of land and quays
  s += sCompass(76, 116);
  if (spec.wind != null) s += sWind(W - 170, 80, spec.wind);
  s += sScale(30, H - keyH - 30, mpp, stepM);
  // key along the bottom
  s += sKey(keyLines, W, H - keyH, keyH);
  return s + '</svg>';
}

/* ---- light rhythms: each light a strip of dark with its flashes along a time line ---- */
function schematicRhythm(spec) {
  const W = 1280, { lines: keyLines, keyH, H } = sKeyLines(spec, W), T = spec.T || 15, x0 = 450, x1 = W - 50, px = (x1 - x0) / T;
  const rows = spec.rows, rowH = Math.min(150, (H - keyH - 150) / rows.length), y0 = 70;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="${W}" height="${H}" fill="var(--bg)"/>`;
  for (let t = 0; t <= T; t++) { const x = x0 + t * px; s += `<line x1="${x}" y1="${y0 - 10}" x2="${x}" y2="${y0 + rows.length * rowH}" stroke="var(--line)" stroke-width="2"/>`; if (t % (spec.tick || 5) === 0) s += stxt(x, y0 + rows.length * rowH + 40, t + ' ' + st('s'), { s: 24 }); }
  rows.forEach((r, i) => {
    const y = y0 + i * rowH + rowH * 0.2, h = rowH * 0.56;
    if (r.hi) s += `<rect x="20" y="${y - 14}" width="${W - 40}" height="${h + 28}" rx="18" fill="rgba(255,230,0,.13)" stroke="${SCOL.course}" stroke-width="4"/>`;
    s += stxt(36, y + h / 2 - 4, r.label, { s: 26, f: 'var(--ink)', a: 'start' }); if (r.note) s += stxt(36, y + h / 2 + 30, r.note, { s: 17, w: 400, f: 'var(--ink)', a: 'start' });
    s += `<rect x="${x0}" y="${y}" width="${x1 - x0}" height="${h}" rx="8" fill="#141b26"/>`;
    for (let k = 0; k * r.period < T; k++) for (const [t, d] of r.flashes) { const a = k * r.period + t; if (a >= T) continue; s += `<rect x="${x0 + a * px}" y="${y + 6}" width="${Math.max(6, Math.min(d, T - a) * px)}" height="${h - 12}" rx="5" fill="${SCOL[r.c || 'w'] === '#ffffff' ? '#fff3c4' : SCOL[r.c]}"/>`; }
    if (r.periodMark !== false) { const xe = x0 + r.period * px; if (r.period < T) s += `<line x1="${xe}" y1="${y - 8}" x2="${xe}" y2="${y + h + 8}" stroke="var(--accent)" stroke-width="5"/>`; }
  });
  s += sKey(keyLines, W, H - keyH, keyH);
  return s + '</svg>';
}

/* ---- a side view: the water column at anchor, for scope ---- */
function schematicProfile(spec) {
  const W = 1280, { lines: keyLines, keyH, H } = sKeyLines(spec, W), area = H - keyH;
  const depth = spec.depth, bow = spec.bow, chain = spec.chain, horiz = Math.sqrt(Math.max(1, chain * chain - (depth + bow) * (depth + bow)));
  // horizontal and vertical scales apart: the water column is exaggerated so the depth reads, as on a chart profile
  const mx = (horiz + 18) / (W - 330), my = (depth + bow + 2.5) / (area - 250), sea = 190, bed = sea + depth / my, bowY = sea - bow / my;
  const L = 13 / mx, hx = W - 230 - L, ax = hx - horiz / mx;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="${W}" height="${H}" fill="var(--bg)"/>`;
  // water: a deepening tint, a wavy surface
  s += `<defs><linearGradient id="spw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgba(60,140,190,.12)"/><stop offset="1" stop-color="rgba(40,100,150,.26)"/></linearGradient></defs>`;
  s += `<rect x="0" y="${sea}" width="${W}" height="${bed - sea}" fill="url(#spw)"/>`;
  let wave = `M0 ${sea}`; for (let x = 0; x < W; x += 40) wave += ` q10 -7 20 0 q10 7 20 0`;
  s += `<path d="${wave}" fill="none" stroke="#3c8cbe" stroke-width="5"/>`;
  // the bed: sand with pebbles and a darker line
  s += `<rect x="0" y="${bed}" width="${W}" height="${area - bed}" fill="#e3d6b4"/>`;
  for (let i = 0; i < 46; i++) { const px = (i * 97.3) % W, py = bed + 14 + ((i * 53.7) % Math.max(10, area - bed - 24)); s += `<ellipse cx="${px.toFixed(0)}" cy="${py.toFixed(0)}" rx="${3 + (i % 4)}" ry="${2 + (i % 3)}" fill="#b9a77c"/>`; }
  s += `<line x1="0" y1="${bed}" x2="${W}" y2="${bed}" stroke="#8a7650" stroke-width="5"/>`;
  // the yacht in profile, her bow (left) towards the anchor: hull, keel, rudder, coachroof, mast, boom and stays
  const top = Math.max(18, bowY - 190), mX = hx + L * 0.4, sx = hx + L, wl = sea + 4;
  s += `<path d="M${hx + L * 0.36} ${wl + 14} L${hx + L * 0.42} ${wl + 50} L${hx + L * 0.54} ${wl + 50} L${hx + L * 0.58} ${wl + 14} Z" fill="var(--ink)"/>`;   // fin keel
  s += `<path d="M${hx + L * 0.86} ${wl + 12} L${hx + L * 0.86} ${wl + 36} L${hx + L * 0.91} ${wl + 36} L${hx + L * 0.93} ${wl + 10} Z" fill="var(--ink)"/>`;   // rudder
  s += `<path d="M${hx} ${bowY} L${sx} ${bowY + 10} L${sx - 8} ${sea + 22} L${hx + L * 0.12} ${sea + 26} Z" fill="var(--ink)"/>`;   // hull
  s += `<path d="M${hx + 6} ${bowY + 9} L${sx - 4} ${bowY + 18}" stroke="#fff" stroke-opacity=".35" stroke-width="3"/>`;   // sheer stripe
  s += `<path d="M${hx + L * 0.3} ${bowY + 2} L${hx + L * 0.34} ${bowY - 22} L${hx + L * 0.66} ${bowY - 18} L${hx + L * 0.7} ${bowY + 6} Z" fill="var(--ink)"/>`;   // coachroof
  s += `<line x1="${mX}" y1="${bowY - 20}" x2="${mX}" y2="${top}" stroke="var(--ink)" stroke-width="6"/><line x1="${mX}" y1="${bowY - 50}" x2="${hx + L * 0.86}" y2="${bowY - 38}" stroke="var(--ink)" stroke-width="5"/>`;   // mast, boom
  s += `<line x1="${mX}" y1="${top + 4}" x2="${hx + 4}" y2="${bowY}" stroke="var(--ink)" stroke-width="2"/><line x1="${mX}" y1="${top + 4}" x2="${sx - 2}" y2="${bowY + 8}" stroke="var(--ink)" stroke-width="2"/>`;   // stays
  s += `<circle cx="${hx}" cy="${bowY}" r="10" fill="var(--accent)" stroke="var(--bg)" stroke-width="3"/>`;   // the bow roller
  // the chain: hangs from the roller and lies along the bed for the last stretch before the anchor, as a real rode does
  const touch = hx + (ax - hx) * 0.72, pts = [];
  for (let i = 0; i <= 40; i++) { const t = i / 40, x = hx + (touch - hx) * t, y = bowY + (bed - 6 - bowY) * (1 - Math.pow(1 - t, 2.2)); pts.push(`${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`); }
  const ringX = ax + 44, ringY = bed - 12;
  pts.push(`L${(ringX + 14).toFixed(1)} ${(bed - 6).toFixed(1)}`, `L${ringX.toFixed(1)} ${ringY.toFixed(1)}`);
  s += `<path d="${pts.join(' ')}" fill="none" stroke="#3c4148" stroke-width="10" stroke-linecap="round"/><path d="${pts.join(' ')}" fill="none" stroke="#9aa1a8" stroke-width="4" stroke-dasharray="9 7"/>`;
  // the anchor dug in, its flukes under a little mound of sand
  // a plough anchor side-on: the shank up to the ring where the chain joins, the fluke dug into the sand
  s += `<path d="M${ax} ${bed + 6} L${ax - 44} ${bed + 30} L${ax - 18} ${bed - 8} Z" fill="var(--ink)" fill-opacity=".55" stroke="var(--ink)" stroke-width="3" stroke-linejoin="round"/>`;
  s += `<line x1="${ax - 6}" y1="${bed + 4}" x2="${ringX}" y2="${ringY}" stroke="var(--ink)" stroke-width="8" stroke-linecap="round"/><circle cx="${ringX}" cy="${ringY}" r="7" fill="none" stroke="var(--ink)" stroke-width="4"/>`;
  s += `<path d="M${ax - 60} ${bed + 1} Q${ax - 34} ${bed - 14} ${ax - 4} ${bed + 1} Z" fill="#d4c497" stroke="#8a7650" stroke-width="3"/>`;
  // the measurements: depth beside the hull, bow height at the roller, the chain along its length
  s += sDim(sx + 70, sea, sx + 70, bed, `${st('depth')} ${depth} m`, 0) + sDim(hx - 140, bowY, hx - 140, sea, `${st('bow')} ${bow} m`, 0);
  s += sPill((hx + ax) / 2, bowY + (bed - bowY) * 0.48, `${st('chain')} ${chain} m`, 'accent', 30);
  s += stxt(40, 76, spec.formula || '', { s: 28, f: 'var(--ink)', a: 'start' });
  s += sKey(keyLines, W, area, keyH);
  return s + '</svg>';
}

if (typeof window !== 'undefined') { window.schematic = schematic; window.schematicProfile = schematicProfile; window.schematicRhythm = schematicRhythm; window.SCH_TEXT = SCH_TEXT; }
