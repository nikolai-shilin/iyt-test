/* IYT Test hi-fi flows: icons, topic data, the page-by-page viewer (page-by-page viewer with an index and an overview). */

/* ---------- topics of the Bareboat Skipper bank (data/questions/bareboat-skipper.json) with sample mastery ---------- */
const TOPICS = [
  { id: 'terms', t: 'Nautical terms & parts of the boat', i: 'yacht', m: 100, n: 10 },
  { id: 'ropework', t: 'Ropework & knots', i: 'rope', m: 90, n: 10 },
  { id: 'safety', t: 'Safety equipment & procedures', i: 'ring', m: 80, n: 10 },
  { id: 'colregs', t: 'Rules of the road (COLREGs)', i: 'compass', m: 50, n: 10 },
  { id: 'navigation', t: 'Charts, compass & position', i: 'map', m: 60, n: 10 },
  { id: 'buoyage', t: 'Buoyage & lights', i: 'buoy', m: 30, n: 10 },
  { id: 'weather', t: 'Weather', i: 'wind', m: 70, n: 10 },
  { id: 'anchoring', t: 'Anchoring & mooring', i: 'anchor', m: 60, n: 10 },
  { id: 'systems', t: 'Engine, electrics & boat systems', i: 'wrench', m: 40, n: 10 },
  { id: 'emergency', t: 'VHF, distress & emergencies', i: 'radio', m: 40, n: 10 },
];
function fillTopics() {
  // [data-fill=topics]: level page rows (icon, title, mastered/total, bar). data-weak marks the under-50 ones in red.
  document.querySelectorAll('[data-fill=topics]').forEach(el => {
    const lim = +(el.dataset.limit || 99), link = el.dataset.link !== undefined;
    el.innerHTML = TOPICS.slice(0, lim).map(t => `<${link ? 'a' : 'div'} class="topic${t.m >= 100 ? ' done' : t.m < 50 ? ' weak' : ''}">` +
      `<span class="ico">${t.m >= 100 ? svg('check', 18) : svg(t.i, 18)}</span><span class="card-title">${t.t}</span>` +
      `<span class="n"><b>${Math.round(t.m / 10)}/${t.n}</b>mastered</span><span class="bar"><i style="width:${t.m}%"></i></span></${link ? 'a' : 'div'}>`).join('');
  });
  // [data-fill=tbars]: result bars per topic; data-scores="terms:2/2,colregs:1/3,…" gives the session's numbers.
  document.querySelectorAll('[data-fill=tbars]').forEach(el => {
    const sc = Object.fromEntries((el.dataset.scores || '').split(',').filter(Boolean).map(s => { const [k, v] = s.split(':'); const [a, b] = v.split('/').map(Number); return [k, [a, b]]; }));
    el.innerHTML = TOPICS.filter(t => sc[t.id]).map(t => { const [a, b] = sc[t.id], p = Math.round(a / b * 100);
      return `<div class="tbar${p < 60 ? ' weak' : ''}"><span class="card-title">${t.t}</span><span class="n">${a}/${b}</span><span class="bar"><i style="width:${p}%"></i></span></div>`; }).join('');
  });
  // [data-fill=chips]: topic chips for the practice set-up sheet; data-on lists the selected ids.
  document.querySelectorAll('[data-fill=chips]').forEach(el => {
    const on = (el.dataset.on || '').split(',');
    el.innerHTML = TOPICS.map(t => `<span class="tag${on.includes(t.id) ? ' tag-on' : ''}" style="min-height:40px;font-size:15px;padding:0 14px">${t.t.split(' (')[0].split(' & ')[0]}<span class="tag-count">${t.n}</span></span>`).join('');
  });
  // [data-fill=grid40]: exam overview, data-a answered count, data-f flagged list, data-now current.
  document.querySelectorAll('[data-fill=grid40]').forEach(el => {
    const a = +el.dataset.a, f = (el.dataset.f || '').split(',').map(Number), now = +el.dataset.now;
    el.innerHTML = Array.from({ length: 40 }, (_, i) => `<span class="${i < a ? 'a' : ''}${f.includes(i + 1) ? ' f' : ''}${i + 1 === now ? ' now' : ''}">${i + 1}</span>`).join('');
  });
}

/* ---------- theme ---------- */
let night = false;
function setTheme(t) {
  night = t === 'night';
  document.querySelectorAll('.screen, .desk').forEach(s => s.classList.toggle('theme-night', night));
  document.documentElement.dataset.theme = night ? 'dark' : 'light';
  document.querySelectorAll('[data-theme-btn]').forEach(b => b.classList.toggle('on', b.dataset.themeBtn === t));
  document.querySelectorAll('img.logo').forEach(img => img.style.filter = night ? 'invert(1)' : '');
  save('theme', t);
}
function save(k, v) { try { localStorage.setItem('iyt-test-' + k, v); } catch (e) {} }
function load(k, d) { try { return localStorage.getItem('iyt-test-' + k) || d; } catch (e) { return d; } }

/* ---------- viewer: one screen per page, or the overview of all lanes ---------- */
const arts = [...document.querySelectorAll('.art')];
const stageBox = document.querySelector('.stage-box');
const scaler = document.querySelector('.scaler');
const notes = document.querySelector('.notes-body');
let cur = -1, home = null;
const WHO = { app: 'Mini app', web: 'Website', bot: 'Telegram' };

function buildIndex() {
  const idx = document.querySelector('.index');
  let html = '';
  document.querySelectorAll('section.flow').forEach(sec => {
    html += `<h4>${WHO[sec.dataset.who]} · ${sec.querySelector('h2').textContent}</h4>`;
    sec.querySelectorAll('.art').forEach(a => {
      const i = arts.indexOf(a);
      html += `<a data-go="${i}"><span>${a.dataset.id}</span>${a.querySelector('.cap b').textContent.replace(/^\S+\s/, '')}</a>`;
    });
  });
  idx.innerHTML = html;
  idx.addEventListener('click', e => { const a = e.target.closest('[data-go]'); if (a) { go(+a.dataset.go); document.body.classList.remove('index-open'); } });
}

function restore() {
  if (cur < 0 || !home) return;
  const scr = scaler.firstElementChild;
  if (scr) home.parent.insertBefore(scr, home.next);
  home = null;
}

function fitStage() {
  const scr = scaler.firstElementChild;
  if (!scr) return;
  const stage = document.querySelector('.stage');
  const w = scr.offsetWidth, h = scr.offsetHeight;
  const narrow = window.innerWidth <= 760;
  const availW = stage.clientWidth - (narrow ? 32 : 48);
  const availH = narrow ? Math.max(window.innerHeight * 0.82, 480) : stage.clientHeight - 48;
  const ref = scr.classList.contains('long') || scr.classList.contains('desk') ? Math.min(h, 844) : h;
  const sc = Math.min(1, availW / w, availH / ref);
  scaler.style.transform = `scale(${sc})`;
  stageBox.style.width = w * sc + 'px';
  stageBox.style.height = h * sc + 'px';
  stage.style.alignItems = h * sc > stage.clientHeight - 40 ? 'flex-start' : 'center';
  stage.style.overflowY = h * sc > stage.clientHeight - 40 ? 'auto' : 'hidden';
}

function go(i) {
  i = Math.max(0, Math.min(arts.length - 1, i));
  restore();
  cur = i;
  const a = arts[i], scr = a.querySelector('.screen, .desk'), sec = a.closest('section.flow');
  home = { parent: scr.parentNode, next: scr.nextSibling };
  scaler.appendChild(scr);
  const cap = a.querySelector('.cap');
  const title = cap.querySelector('b').textContent;
  const body = cap.innerHTML.replace(/<b>.*?<\/b>/, '');
  const web = sec.dataset.who === 'web';
  notes.innerHTML = `<span class="who${web ? ' web' : ''}">${WHO[sec.dataset.who]} · ${sec.querySelector('h2').textContent}</span>` +
    `<h2>${title.replace(/^\S+\s/, '')}</h2><span class="counter">${a.dataset.id} · page ${i + 1} of ${arts.length}</span><p>${body}</p>`;
  document.querySelector('[data-prev]').disabled = i === 0;
  document.querySelector('[data-next]').disabled = i === arts.length - 1;
  document.querySelectorAll('.index a').forEach(x => x.classList.toggle('on', +x.dataset.go === i));
  document.querySelector('.index a.on')?.scrollIntoView({ block: 'nearest' });
  if (location.hash !== '#' + a.dataset.id) history.replaceState(null, '', '#' + a.dataset.id);
  fitStage();
}

function setMode(mode) {
  document.body.classList.toggle('mode-overview', mode === 'overview');
  document.querySelectorAll('[data-mode-btn]').forEach(b => b.classList.toggle('on', b.dataset.modeBtn === mode));
  if (mode === 'overview') { restore(); cur = -1; }
  else { const id = location.hash.slice(1); const i = arts.findIndex(a => a.dataset.id === id); go(i >= 0 ? i : 0); }
  save('mode', mode);
}

document.querySelectorAll('[data-theme-btn]').forEach(b => b.addEventListener('click', () => setTheme(b.dataset.themeBtn)));
document.querySelectorAll('[data-mode-btn]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.modeBtn)));
document.querySelector('[data-prev]').addEventListener('click', () => go(cur - 1));
document.querySelector('[data-next]').addEventListener('click', () => go(cur + 1));
document.querySelector('.menu-btn').addEventListener('click', () => document.body.classList.toggle('index-open'));
document.addEventListener('keydown', e => {
  if (cur < 0 || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'ArrowRight' || e.key === 'PageDown') { go(cur + 1); e.preventDefault(); }
  if (e.key === 'ArrowLeft' || e.key === 'PageUp') { go(cur - 1); e.preventDefault(); }
});
window.addEventListener('hashchange', () => { const i = arts.findIndex(a => '#' + a.dataset.id === location.hash); if (i >= 0 && i !== cur) { if (cur < 0) setMode('pages'); else go(i); } });
window.addEventListener('resize', () => { if (cur >= 0) fitStage(); });

fillTopics();
paintIcons();
paintFigures();
buildIndex();
setTheme(load('theme', 'day'));
setMode(location.hash ? 'pages' : load('mode', 'pages'));
