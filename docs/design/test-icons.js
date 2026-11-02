/* IYT Test icons: the base set (icons.js) plus the test's own glyphs (24 grid, 2px line).
   Shared by flows.html, questions.html and the mini app. Load after icons.js. */
const appIcon = (n, s = 24) => rycIcon(n, s);

const TEST_ICONS = {
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  trophy: '<path d="M8 21h8M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/>',
  flag: '<path d="M5 22V4"/><path d="M5 4h12l-2 4 2 4H5"/>',
  timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 1.5M10 2h4M18 5l1.5-1.5"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  play: '<path d="M7 4.5v15l12-7.5z"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
  rope: '<path d="M5 7c0-2 2-3 4-3h6c2 0 4 1 4 3s-2 3-4 3H9c-2 0-4 1-4 3s2 3 4 3h6c2 0 4 1 4 3"/>',
  ring: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="m5.6 5.6 3.6 3.6M14.8 14.8l3.6 3.6M18.4 5.6l-3.6 3.6M9.2 14.8l-3.6 3.6"/>',
  wind: '<path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8a2.5 2.5 0 1 1-2.5 2.5"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
  radio: '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 0 1 0 8.4M7.8 16.2a6 6 0 0 1 0-8.4M19.1 4.9a10 10 0 0 1 0 14.2M4.9 19.1a10 10 0 0 1 0-14.2"/>',
  buoy: '<path d="M9 3h6l1 7H8z"/><path d="M8 10h8v6H8z"/><path d="M4 20c2-2 4 0 6-1s4-1 6 0 3 1 4 1"/>',
  light: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 1 4 12.7V17H8v-2.3A7 7 0 0 1 12 2z"/>',
  share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  fire: '<path d="M12 22c4 0 7-2.7 7-7 0-3-1.5-5-3-6.5 0 2-1 3-2 3.5.5-3-1-6.5-4-8 .3 3-1.7 4.5-3 6.5C5.6 12.4 5 13.3 5 15c0 4.3 3 7 7 7z"/>',
};
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
