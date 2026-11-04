/* IYT Test icon set — 24×24 grid, 2 px line, round caps and joins, no fill (currentColor), 2 px clear of the edges.
   Drawn in the same hand as the figures (figures.js): the same line, the same simplifications. Shared by the design viewer
   (flows.html, questions.html), the icon sheet (icons.html) and the mini app. Load after icons.js: anything not here
   (Telegram chrome in the mockups: dots, clip, status) still comes from the base set.

   Three groups: the app's own glyphs (tabs, buttons, exam), the nautical glyphs (one per topic of every level, see
   TOPIC_ICONS in the mini app and build_level.py), and old names kept so that saved banks keep working. */

// Three propeller blades: one drawn, two turned about the hub.
const BLADE = '<path d="M12 9.5c-2.8-1.8-3.2-5.2 0-7.5 3.2 2.3 2.8 5.7 0 7.5z"/>';

const TEST_ICONS = {
  /* ---- the app: tabs, buttons, exam ---- */
  book: '<path d="M3 5.5c4.5 0 7 .8 9 2.5v12c-2-1.7-4.5-2.5-9-2.5z"/><path d="M21 5.5c-4.5 0-7 .8-9 2.5v12c2-1.7 4.5-2.5 9-2.5z"/>',
  timer: '<circle cx="12" cy="13.5" r="7.5"/><path d="M12 10v3.5l2.5 1.5"/><path d="M10 2.5h4M12 2.5V6M18.5 6.5 20 5"/>',
  chart: '<path d="M3 21h18"/><path d="M6.5 21v-6M12 21V10M17.5 21V4"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
  play: '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
  next: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  back: '<path d="m15 18-6-6 6-6"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  share: '<path d="M12 3v12"/><path d="m8 7 4-4 4 4"/><path d="M8 11H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-2"/>',
  flag: '<path d="M5 22V4"/><path d="M5 4h12l-2 4 2 4H5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  trophy: '<path d="M8 21h8M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/>',
  fire: '<path d="M12 22c4 0 7-2.7 7-7 0-3-1.5-5-3-6.5 0 2-1 3-2 3.5.5-3-1-6.5-4-8 .3 3-1.7 4.5-3 6.5C5.6 12.4 5 13.3 5 15c0 4.3 3 7 7 7z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',

  /* ---- the boat ---- */
  yacht: '<path d="M3 17h18l-1.8 3.2a1 1 0 0 1-.9.5H5.7a1 1 0 0 1-.9-.5z"/><path d="M12 3v14"/><path d="M10.5 5v10H5c1-3.6 2.9-7 5.5-10z"/><path d="M13.5 6.5V15H19c-.5-3.2-2.4-6.2-5.5-8.5z"/>',
  sail: '<path d="M12 2v18"/><path d="M12 4c5 3.5 7.5 8.5 7.5 14H12"/><path d="M13.5 10h3.5M13.5 14h5"/><path d="M5 20h16"/>',
  wheel: '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/><path d="M12 2.5V10M12 14v7.5M2.5 12H10M14 12h7.5M5.3 5.3l5.3 5.3M13.4 13.4l5.3 5.3M18.7 5.3l-5.3 5.3M10.6 13.4l-5.3 5.3"/>',
  propeller: BLADE + `<g transform="rotate(120 12 12)">${BLADE}</g><g transform="rotate(240 12 12)">${BLADE}</g><circle cx="12" cy="12" r="2.5"/>`,
  gear: '<path d="M12.2 2h-.4a2 2 0 0 0-2 2v.2a2 2 0 0 1-1 1.7l-.4.3a2 2 0 0 1-2 0l-.2-.1a2 2 0 0 0-2.7.7l-.2.4a2 2 0 0 0 .7 2.7l.2.1a2 2 0 0 1 1 1.7v.5a2 2 0 0 1-1 1.8l-.2.1a2 2 0 0 0-.7 2.7l.2.4a2 2 0 0 0 2.7.7l.2-.1a2 2 0 0 1 2 0l.4.3a2 2 0 0 1 1 1.7v.2a2 2 0 0 0 2 2h.4a2 2 0 0 0 2-2v-.2a2 2 0 0 1 1-1.7l.4-.3a2 2 0 0 1 2 0l.2.1a2 2 0 0 0 2.7-.7l.2-.4a2 2 0 0 0-.7-2.7l-.2-.1a2 2 0 0 1-1-1.8v-.5a2 2 0 0 1 1-1.7l.2-.1a2 2 0 0 0 .7-2.7l-.2-.4a2 2 0 0 0-2.7-.7l-.2.1a2 2 0 0 1-2 0l-.4-.3a2 2 0 0 1-1-1.7V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  cleat: '<path d="M8 20h8"/><path d="M12 20v-6"/><path d="M3 11.5c3 0 5 2.5 9 2.5s6-2.5 9-2.5"/><path d="M3 11.5V9M21 11.5V9"/>',
  knot: '<path d="M2 12h3.5c2.5 0 3.5-5 7-5s4.5 2.3 4.5 3.5S15.5 14 13 14H9.5c-2.5 0-4 1.5-4 3s1.5 3 4 3 3.5-4 6-4H22"/>',
  anchor: '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>',

  /* ---- safety ---- */
  lifebuoy: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="m5.6 5.6 3.6 3.6M14.8 14.8l3.6 3.6M18.4 5.6l-3.6 3.6M9.2 14.8l-3.6 3.6"/>',
  lifejacket: '<path d="M6 21V10c0-2.5 1-5 3-7h6c2 2 3 4.5 3 7v11z"/><path d="M12 9v12"/><path d="M9 3c0 2.2 1.3 3.5 3 3.5S15 5.2 15 3"/><path d="M6 15h12"/>',
  medkit: '<rect x="3" y="6" width="18" height="15" rx="2"/><path d="M9 6V3h6v3"/><path d="M12 10v7M8.5 13.5h7"/>',
  flare: '<path d="M12 14 8.5 11.5C8.5 7 9.8 4 12 2c2.2 2 3.5 5 3.5 9.5z"/><path d="M8.5 11.5 6 15h12l-2.5-3.5"/><path d="M12 15v4M9.5 21l2.5 1 2.5-1"/>',
  binoculars: '<rect x="2.5" y="10" width="7" height="10" rx="2.5"/><rect x="14.5" y="10" width="7" height="10" rx="2.5"/><path d="M9.5 14h5"/><path d="M5 10V6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4M15 10V6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4"/>',
  captain: '<path d="M5 21a7 7 0 0 1 14 0"/><path d="M8.8 8a3.5 3.5 0 1 0 6.4 0"/><path d="M6 7.5h12"/><path d="M7.5 7.5c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4"/>',
  mug: '<path d="M4 8h12v8a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path d="M16 10h2a2 2 0 0 1 0 4h-2"/><path d="M7.5 3.5c0 1.5 1 1.5 1 3M11.5 3.5c0 1.5 1 1.5 1 3"/>',

  /* ---- rules of the road, navigation, buoyage ---- */
  rules: '<path d="M8 21.5V5M4.5 8.5 8 5l3.5 3.5"/><path d="M16.5 21.5v-6a4 4 0 0 0-4-4H8"/>',
  dividers: '<circle cx="12" cy="5" r="2"/><path d="m11 7-5 14M13 7l5 14"/><path d="M8.5 14.5h7"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
  map: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
  buoy: '<path d="M8 17 9.5 7h5L16 17z"/><path d="m10 7 2-4 2 4"/><path d="M9 11h6"/><path d="M3 20c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0"/>',
  lighthouse: '<path d="M9 21 10 9h4l1 12"/><path d="M8 9h8"/><path d="M10 9V5h4v4"/><path d="M12 5V3"/><path d="m3.5 6 3 1.5M20.5 6l-3 1.5"/><path d="M5 21h14"/>',

  /* ---- weather ---- */
  wind: '<path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8a2.5 2.5 0 1 1-2.5 2.5"/>',
  cloud: '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 11.4 3.5 3.5 0 0 0 7 18z"/>',
  barometer: '<circle cx="12" cy="12" r="9"/><path d="m12 12 2.5-4.5"/><circle cx="12" cy="12" r="1"/><path d="M12 5.5V7M6.5 12H8M16 12h1.5M7.5 7.5l1 1"/>',

  /* ---- radio ---- */
  vhf: '<rect x="7" y="6" width="10" height="16" rx="2"/><path d="M10 6V2"/><path d="M10 10h4M10 13h4"/><path d="M12 18h.01" stroke-width="3"/>',
  radio: '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 0 1 0 8.4M7.8 16.2a6 6 0 0 1 0-8.4M19.1 4.9a10 10 0 0 1 0 14.2M4.9 19.1a10 10 0 0 1 0-14.2"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10a7 7 0 0 1-14 0M12 19v3"/>',
  'flag-alpha': '<path d="M5 22V3"/><path d="M5 3h14l-4 4.5L19 12H5"/><path d="M12 3v9"/>',
  mmsi: '<path d="M4 9h16M4 15h16M10 3 8 21M16 3l-2 18"/>',
  megaphone: '<path d="M3 11v2a1 1 0 0 0 1 1h3l8 4V6l-8 4H4a1 1 0 0 0-1 1z"/><path d="M18.5 9.5a3.5 3.5 0 0 1 0 5"/><path d="m7 14 1.5 6"/>',
  beacon: '<rect x="9" y="12" width="6" height="9" rx="1.5"/><path d="M12 12V3"/><path d="M8.5 2.5a4 4 0 0 0 0 5M15.5 2.5a4 4 0 0 1 0 5"/>',
  licence: '<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="8" cy="11" r="2"/><path d="M5.5 15.5c.5-1.3 1.4-2 2.5-2s2 .7 2.5 2M14 10h4M14 14h3"/>',

  /* ---- Yachtmaster Coastal: tides, the passage ---- */
  tide: '<path d="M3 17c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0"/><path d="M3 21c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0"/><path d="M12 13V3M8.5 6.5 12 3l3.5 3.5"/>',
  route: '<circle cx="5" cy="19" r="2"/><circle cx="19" cy="5" r="2"/><path d="M7 19h6a3 3 0 0 0 0-6h-2a3 3 0 0 1 0-6h6"/>',

  /* ---- Yachtmaster Ocean: the sextant, the meridian, the stars ---- */
  sextant: '<path d="M5 4h14"/><path d="M12 4 5.5 18M12 4l6.5 14"/><path d="M4 17.5c5 3 11 3 16 0"/><path d="M12 4v6"/><circle cx="12" cy="12" r="1.5"/>',
  meridian: '<path d="M3 19h18"/><path d="M5 19a7 7 0 0 1 14 0"/><path d="M12 19V6"/><circle cx="12" cy="4.5" r="2"/>',
  star: '<path d="m12 3 2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6-4.5-4.2 6.1-.7z"/>',

  /* ---- the charter check-in: electrics, water and gas, the inventory ---- */
  battery: '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M19 10h1.5a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H19"/><path d="M6 10v4M9.5 10v4M13 10v4"/>',
  drop: '<path d="M12 2.5c3.5 4.5 7 8 7 12a7 7 0 0 1-14 0c0-4 3.5-7.5 7-12z"/><path d="M8.5 14.5a3.5 3.5 0 0 0 3 3.5"/>',
  clipboard: '<rect x="4" y="4" width="16" height="18" rx="2"/><path d="M9 4V2.5h6V4"/><path d="M9 4a1.5 1.5 0 0 0 0 3h6a1.5 1.5 0 0 0 0-3"/><path d="m8 13 2 2 4-4M8 18h8"/>',

  /* ---- old names (banks saved before this set) ---- */
  ring: null, rope: null, light: null, wrench: null, 'board-view': null,
};
TEST_ICONS.ring = TEST_ICONS.lifebuoy;
TEST_ICONS.rope = TEST_ICONS.knot;
TEST_ICONS.light = TEST_ICONS.lighthouse;
TEST_ICONS.wrench = TEST_ICONS.gear;
TEST_ICONS['board-view'] = TEST_ICONS.grid;

// The icon sheet and the viewer list the set by group, in this order.
const TEST_ICON_GROUPS = [
  ['App', ['book', 'timer', 'chart', 'user', 'users', 'play', 'next', 'back', 'check', 'x', 'refresh', 'share', 'flag', 'grid', 'trophy', 'fire', 'target', 'sun', 'moon', 'globe']],
  ['Boat', ['yacht', 'sail', 'wheel', 'propeller', 'gear', 'cleat', 'knot', 'anchor']],
  ['Safety', ['lifebuoy', 'lifejacket', 'medkit', 'flare', 'binoculars', 'captain', 'mug']],
  ['Rules, navigation, buoyage', ['rules', 'dividers', 'compass', 'map', 'buoy', 'lighthouse']],
  ['Weather', ['wind', 'cloud', 'barometer']],
  ['Radio', ['vhf', 'radio', 'mic', 'flag-alpha', 'mmsi', 'megaphone', 'beacon', 'licence']],
  ['Charter check-in', ['battery', 'drop', 'clipboard']],
  ['Yachtmaster Coastal', ['tide', 'route']],
  ['Yachtmaster Ocean', ['sextant', 'meridian', 'star']],
];

const appIcon = (n, s = 24) => rycIcon(n, s);
const svg = (n, s = 22) => TEST_ICONS[n]
  ? `<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${TEST_ICONS[n]}</svg>`
  : appIcon(n, s);
function paintIcons(root = document) {
  root.querySelectorAll('[data-i]').forEach(el => {
    if (el.dataset.done) return;
    el.insertAdjacentHTML('afterbegin', svg(el.dataset.i, +(el.dataset.s || (el.dataset.i === 'status' ? 26 : 22))));
    el.dataset.done = 1;
  });
}
