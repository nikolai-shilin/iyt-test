/* IYT Test — Telegram mini app.
   Screens follow docs/design/flows.html (A1–A9 practice, B1–B5 mock exam, C1–C2 progress and profile).
   No backend: the bank is a static JSON file, progress lives in Telegram CloudStorage (per user, per bot) with a
   localStorage copy, so the same code also runs in a plain browser for testing.
   Globals from the design files: rycIcon (icons.js), svg / paintIcons (test-icons.js), figSvg (figures.js). */
'use strict';

const TG = window.Telegram && window.Telegram.WebApp;
const IN_TG = !!(TG && TG.initData);
const tgv = (v) => IN_TG && TG.isVersionAtLeast(v);
const NATIVE_BUTTONS = tgv('7.10'); // MainButton + SecondaryButton; older clients get the in-page bar
const BOT_LINK = 'https://t.me/iyt_test_bot';
const $app = document.getElementById('app');

const LEVELS = [
  { id: 'bareboat-skipper', file: 'data/bareboat-skipper.json' },
  { title: 'International Crew', soon: 'Coming soon' },
  { title: 'Yachtmaster Coastal', soon: 'Coming soon' },
  { title: 'Yachtmaster Offshore', soon: 'Coming in 2027' },
];
const TOPIC_ICON = { terms: 'yacht', ropework: 'rope', safety: 'ring', colregs: 'compass', navigation: 'map', buoyage: 'buoy', weather: 'wind', anchoring: 'anchor', systems: 'wrench', emergency: 'radio' };
const DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

let BANK = null, Q = {}, TOPICS = [], TT = {};

/* ---------- small helpers ---------- */
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad = (n) => String(n).padStart(2, '0');
const dkey = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const fmt = (ms) => { const s = Math.max(0, Math.round(ms / 1000)); return `${Math.floor(s / 60)}:${pad(s % 60)}`; };
const short = (t) => TT[t].split(' (')[0].split(' & ')[0];
const lower = (s) => (/^[A-Z][a-z]/.test(s) ? s[0].toLowerCase() + s.slice(1) : s);
const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;
const day = (at) => new Date(at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
const figHtml = (q) => (q.figure ? `<div class="fig">${figSvg(q.figure)}</div>` : '');

function hap(kind) {
  if (!tgv('6.1')) return;
  try { kind === 'sel' ? TG.HapticFeedback.selectionChanged() : TG.HapticFeedback.notificationOccurred(kind); } catch (e) {}
}
const confirmBox = (msg) => new Promise((res) => (tgv('6.2') ? TG.showConfirm(msg, res) : res(window.confirm(msg))));
function toast(text) {
  $app.querySelector('.toast')?.remove();
  $app.insertAdjacentHTML('beforeend', `<div class="toast">${esc(text)}</div>`);
  setTimeout(() => $app.querySelector('.toast')?.remove(), 1400);
}

/* ---------- state: mastery per question, activity per day, exams; saved locally and to CloudStorage ---------- */
// q[id] = [last two results as '0'/'1', wrong count]. Mastered = right twice in a row (docs/data-model.md).
const KEY = 'iyt-test-state-v1';
const fresh = () => ({ v: 1, ts: 0, q: {}, days: {}, total: 0, flags: [], exams: [], exam: null, last: null, set: { theme: 'auto', shuffle: true, feedback: true } });
let S = fresh();
const merge = (o) => { const f = fresh(); return { ...f, ...o, set: { ...f.set, ...(o && o.set) } }; };

const CLOUD = tgv('6.9') ? TG.CloudStorage : null;
const CHUNK = 3800; // CloudStorage values are capped at 4096 chars
let cloudTimer = null;
function save(cloud = true) {
  S.ts = Date.now();
  const s = JSON.stringify(S);
  try { localStorage.setItem(KEY, s); } catch (e) {}
  if (cloud && CLOUD) { clearTimeout(cloudTimer); cloudTimer = setTimeout(() => cloudSave(s), 500); }
}
function cloudSave(s = JSON.stringify(S)) {
  if (!CLOUD) return;
  clearTimeout(cloudTimer);
  const n = Math.ceil(s.length / CHUNK);
  try {
    for (let i = 0; i < n; i++) CLOUD.setItem('st' + i, s.slice(i * CHUNK, (i + 1) * CHUNK));
    CLOUD.setItem('stn', String(n));
  } catch (e) {}
}
function cloudLoad() {
  return new Promise((res) => {
    if (!CLOUD) return res(null);
    try {
      CLOUD.getItem('stn', (err, n) => {
        n = +n;
        if (err || !n) return res(null);
        const keys = Array.from({ length: n }, (_, i) => 'st' + i);
        CLOUD.getItems(keys, (err2, vals) => {
          if (err2) return res(null);
          try { res(JSON.parse(keys.map((k) => vals[k] || '').join(''))); } catch (e) { res(null); }
        });
      });
    } catch (e) { res(null); }
  });
}
function loadLocal() { try { const s = localStorage.getItem(KEY); if (s) S = merge(JSON.parse(s)); } catch (e) {} }

const rec = (id) => S.q[id] || ['', 0];
const mastered = (id) => rec(id)[0] === '11';
const isMistake = (id) => rec(id)[1] > 0 && !mastered(id);
const touched = (id) => !!S.q[id];
function record(id, ok) {
  const [h, w] = rec(id);
  S.q[id] = [(h + (ok ? '1' : '0')).slice(-2), w + (ok ? 0 : 1)];
  const d = dkey();
  S.days[d] = (S.days[d] || 0) + 1;
  S.total++;
}
const topicIds = (t) => BANK.questions.filter((q) => q.topic === t).map((q) => q.id);
const topicPct = (t) => { const ids = topicIds(t); return Math.round((ids.filter(mastered).length / ids.length) * 100); };
const levelPct = () => Math.round((BANK.questions.filter((q) => mastered(q.id)).length / BANK.questions.length) * 100);
const allMistakes = () => BANK.questions.filter((q) => isMistake(q.id)).map((q) => q.id);
const weakTopics = () => TOPICS.filter((t) => topicPct(t.id) < 50 && topicIds(t.id).some(touched)).map((t) => t.id);
function streak() {
  const d = new Date();
  if (!S.days[dkey(d)]) d.setDate(d.getDate() - 1); // today not practised yet: the streak is still alive
  let n = 0;
  while (S.days[dkey(d)]) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function prune() { const c = new Date(); c.setDate(c.getDate() - 90); const k = dkey(c); for (const d in S.days) if (d < k) delete S.days[d]; }

/* ---------- navigation: a stack of views, one optional sheet on top ---------- */
let stack = [{ v: 'home' }];
let sheet = null;
let P = null; // the running practice session (memory only)
let mainCb = null, secCb = null;
const cur = () => stack[stack.length - 1];

function go(v, p = {}) { stack.push({ v, ...p }); sheet = null; render(true); }
function replace(v, p = {}) { stack[stack.length - 1] = { v, ...p }; sheet = null; render(true); }
function tab(v) { stack = [{ v }]; sheet = null; P = null; render(true); }
async function back() {
  if (sheet) { sheet = null; return render(); }
  const c = cur();
  if (c.v === 'question' && P && !P.done) {
    if (!(await confirmBox('Quit this session? Your answers so far are kept.'))) return;
    P = null;
  }
  if (c.v === 'exam') { stopTimer(); save(); }
  if (stack.length > 1) { stack.pop(); render(true); }
}

/* ---------- theme: day / night / auto (follows Telegram, or the system outside it) ---------- */
function isNight() {
  const t = S.set.theme;
  if (t !== 'auto') return t === 'night';
  return IN_TG ? TG.colorScheme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
}
function applyTheme() {
  const n = isNight();
  $app.classList.toggle('theme-night', n);
  document.documentElement.dataset.theme = n ? 'dark' : 'light';
  if (tgv('6.9')) {
    const bg = n ? '#000000' : '#ffffff';
    try { TG.setHeaderColor(bg); TG.setBackgroundColor(bg); if (tgv('7.10')) TG.setBottomBarColor(bg); } catch (e) {}
  }
}
const tok = (name) => getComputedStyle($app).getPropertyValue(name).trim();

/* ---------- rendering ---------- */
const NAV = [['home', 'book', 'Learn'], ['examIntro', 'timer', 'Exam'], ['progress', 'chart', 'Progress'], ['profile', 'user', 'Profile']];

function render(toTop) {
  if (cur().v === 'exam' && !S.exam) stack[stack.length - 1] = { v: 'examIntro' };
  const c = cur();
  const V = VIEWS[c.v](c);
  const old = $app.querySelector('.scroll');
  const keep = !toTop && old ? old.scrollTop : 0;
  let h = '';
  if (!IN_TG) h += `<div class="tgh"><span>${stack.length > 1 || sheet ? '<button data-act="back">‹ Back</button>' : ''}</span><b>${esc(V.title)}</b><span></span></div>`;
  h += `<div class="scroll wrap">${V.body}</div>`;
  if (V.nav && stack.length === 1) h += `<div class="nav">${NAV.map(([v, i, t]) => `<a class="${v === V.nav ? 'on' : ''}" data-act="tab" data-v="${v}"><span data-i="${i}"></span>${t}</a>`).join('')}</div>`;
  const B = sheet ? {} : V;
  mainCb = B.main ? B.main.act : null;
  secCb = B.second ? B.second.act : null;
  if (!NATIVE_BUTTONS && (B.main || B.second)) {
    const b = (x, k, cls) => `<button class="b ${cls}${x.off ? ' off' : ''}" data-act="${k}">${x.icon ? `<span data-i="${x.icon}" data-s="18"></span>` : ''}<span class="t">${esc(x.text)}</span></button>`;
    const both = B.main && B.second;
    h += '<div class="tgmain wrap">' +
      (both && B.second.pos !== 'bottom' ? `<div class="row2">${b(B.second, 'second', 'b2')}${b(B.main, 'main', '')}</div>` :
        (B.main ? b(B.main, 'main', '') : '') + (B.second ? b(B.second, 'second', 'b2') : '')) + '</div>';
  }
  if (sheet) h += `<div class="scrim" data-act="back"></div><div class="sheet"><div class="grip"></div><div class="wrap stack g16">${SHEETS[sheet.v](sheet)}</div></div>`;
  $app.innerHTML = h;
  paintIcons($app);
  const sc = $app.querySelector('.scroll');
  if (keep) sc.scrollTop = keep;
  if (NATIVE_BUTTONS) nativeButtons(B);
  if (tgv('6.1')) (stack.length > 1 || sheet ? TG.BackButton.show() : TG.BackButton.hide());
  if (c.v === 'exam' && S.exam) { startTimer(); if (tgv('6.2')) TG.enableClosingConfirmation(); }
  else { stopTimer(); if (tgv('6.2')) TG.disableClosingConfirmation(); }
}

function nativeButtons(B) {
  const MB = TG.MainButton, SB = TG.SecondaryButton;
  if (B.main) {
    const off = !!B.main.off;
    MB.setParams({ text: B.main.text, color: off ? tok('--band') : tok('--accent'), text_color: off ? tok('--faint') : tok('--on-accent'), is_active: !off, is_visible: true });
  } else MB.hide();
  if (B.second) SB.setParams({ text: B.second.text, color: tok('--band'), text_color: tok('--accent'), is_active: true, is_visible: true, position: B.second.pos || 'left' });
  else SB.hide();
}

/* ---------- pieces shared by several screens ---------- */
function topicRows() {
  return `<div class="topics">${TOPICS.map((t) => {
    const ids = topicIds(t.id), m = ids.filter(mastered).length, p = Math.round((m / ids.length) * 100);
    const cls = p >= 100 ? ' done' : p < 50 && ids.some(touched) ? ' weak' : '';
    return `<div class="topic${cls}" data-act="setup" data-t="${t.id}"><span class="ico">${p >= 100 ? svg('check', 18) : svg(TOPIC_ICON[t.id] || 'book', 18)}</span>` +
      `<span class="card-title">${esc(t.title)}</span><span class="n"><b>${m}/${ids.length}</b>mastered</span><span class="bar"><i style="width:${p}%"></i></span></div>`;
  }).join('')}</div>`;
}
function tbars(per, limit = 60) {
  return `<div class="tbars">${TOPICS.filter((t) => per[t.id]).map((t) => {
    const [a, b] = per[t.id], p = Math.round((a / b) * 100);
    return `<div class="tbar${p < limit ? ' weak' : ''}"><span class="card-title">${esc(t.title)}</span><span class="n">${a}/${b}</span><span class="bar"><i style="width:${p}%"></i></span></div>`;
  }).join('')}</div>`;
}
function perTopic(ids, isOk) {
  const per = {};
  ids.forEach((id) => { const t = Q[id].topic; per[t] = per[t] || [0, 0]; per[t][1]++; if (isOk(id)) per[t][0]++; });
  return per;
}
function examLine() {
  const E = S.exam;
  const a = E.ids.filter((id) => E.ans[id] != null).length;
  return `${a} of ${E.ids.length} answered · ${fmt(remaining())} left`;
}

/* ---------- views ---------- */
const VIEWS = {
  /* A1 Home */
  home() {
    const st = streak(), lp = levelPct(), ex = S.exams.length;
    const lv = LEVELS.map((l) => l.soon
      ? `<div class="lvl soon"><span class="ring" style="--v:0"><b>—</b></span><div><div class="card-title">${l.title}</div><div class="card-meta">${l.soon}</div></div></div>`
      : `<div class="lvl on" data-act="level"><span class="ring" style="--v:${lp}"><b>${lp}%</b></span><div><div class="card-title">Bareboat Skipper</div>` +
        `<div class="card-meta">${TOPICS.length} topics · ${BANK.questions.length} questions${ex ? ' · ' + plural(ex, 'exam') + ' taken' : ''}</div></div><span class="chev" data-i="next" data-s="20"></span></div>`).join('');
    return {
      title: 'IYT Test', nav: 'home',
      body: `<div class="row sb-between" style="min-height:40px"><img class="logo" src="design/logo-black.svg" alt="RYC">${st ? `<span class="streak"><span class="fire" data-i="fire" data-s="14"></span>${st}-day streak</span>` : ''}</div>
        <div class="stack g12"><span class="meta">IYT theory · free</span><h1 class="display">Pass your IYT&nbsp;exam</h1>
        <p class="body-muted">Close-to-real questions for every certification level, with an explanation after each answer. Pick a level to continue.</p></div>
        ${S.exam ? `<div class="continue" data-act="examIntro"><div><span class="meta">Mock exam in progress</span><div class="card-title" style="margin-top:4px">${examLine()}</div></div><span class="mini mini-accent">Continue</span></div>` : ''}
        <div class="stack" style="gap:10px">${lv}</div>`,
    };
  },

  /* A2 Level */
  level() {
    const lp = levelPct(), m = BANK.questions.filter((q) => mastered(q.id)).length;
    const any = BANK.questions.some((q) => touched(q.id));
    const weakest = TOPICS.filter((t) => topicIds(t.id).some(touched) && topicPct(t.id) < 100).sort((a, b) => topicPct(a.id) - topicPct(b.id)).slice(0, 2).map((t) => short(t.id));
    const text = any ? `${m} of ${BANK.questions.length} questions answered right twice in a row.${weakest.length ? ` Weakest: ${weakest.join(', ')}.` : ''}`
      : 'A question counts as mastered once you answer it right twice in a row. Start with any topic.';
    const mis = allMistakes().length;
    return {
      title: 'Bareboat Skipper',
      body: `<div class="row" style="gap:18px;align-items:center"><span class="ring l" style="--v:${lp}"><b>${lp}%</b><small>mastered</small></span>
          <div class="stack g8"><span class="meta">${esc(BANK.title)}</span><p class="body-s">${text}</p></div></div>
        <div class="row" style="gap:10px"><button class="pill pill-primary" style="flex:1;padding:0 14px;font-size:18px" data-act="setup"><span data-i="play" data-s="20"></span>Practice</button>
          <button class="pill" style="flex:1;padding:0 14px;font-size:18px" data-act="examIntro"><span data-i="timer" data-s="20"></span>Mock exam</button></div>
        ${mis ? `<div class="row sb-between"><div><div class="card-title">Mistakes to clear</div><div class="card-meta">${plural(mis, 'question')} to answer right twice</div></div><button class="mini mini-accent" data-act="allMistakes">Review</button></div>` : ''}
        <div class="stack g8"><div class="row sb-between"><span class="kicker">Topics</span><span class="meta">mastered / total</span></div>${topicRows()}</div>`,
    };
  },

  /* A4–A7 Practice question (feedback on) or silent question (feedback off) */
  question() {
    const id = P.ids[P.i], q = Q[id], ord = P.orders[id], n = P.ids.length, last = P.i === n - 1;
    const segs = P.ids.map((x, k) => {
      const r = P.res[x];
      return `<span class="${r ? (P.fb ? r : 'on') : k === P.i ? 'now' : ''}"></span>`;
    }).join('');
    const opts = ord.map((oi, k) => {
      let cls = '', l = 'ABCD'[k];
      if (P.checked) {
        if (oi === q.answer) { cls = 'ok'; l = svg('check', 16); }
        else if (k === P.sel) { cls = 'bad'; l = svg('x', 16); }
        else cls = 'dim';
        cls += ' locked';
      } else if (k === P.sel) cls = 'sel';
      return `<div class="opt ${cls}" data-act="opt" data-n="${k}" role="button"><span class="l">${l}</span><span>${esc(q.options[oi])}</span></div>`;
    }).join('');
    let after = '';
    if (P.checked) {
      const ok = P.res[id] === 'ok';
      after = `<div class="verdict ${ok ? 'ok' : 'bad'}"><span class="ico">${svg(ok ? 'check' : 'x', 16)}</span>${ok ? 'Correct' : 'Not quite'}</div>
        <div class="band why" id="why"><span class="kicker">Why</span><p class="body-s">${esc(q.why)}</p><span class="chip ref">${svg('book', 12)}${esc(q.ref)}</span></div>`;
    }
    const flagged = S.flags.includes(id);
    const tools = `<div class="qtools"><button class="mini${flagged ? ' on' : ''}" data-act="flag"><span data-i="flag" data-s="14"></span>${flagged ? 'Flagged' : 'Flag'}</button>` +
      (!P.checked && !last ? '<button class="mini" data-act="skip"><span data-i="next" data-s="14"></span>Skip</button>' : '') + '</div>';
    let main;
    if (!P.checked && P.fb) main = { text: 'Check', off: P.sel == null, act: check };
    else if (!P.checked) main = { text: last ? 'Finish' : 'Next', off: P.sel == null, act: silentNext };
    else main = { text: last ? 'See results' : 'Next', act: nextQ };
    return {
      title: 'Practice', main,
      body: `<div class="progress">${segs}</div>
        <div class="qhead"><span class="meta meta-ink">Question ${P.i + 1} of ${n}</span><span class="chip">${esc(short(q.topic))}</span></div>
        ${figHtml(q)}<p class="q">${esc(q.q)}</p><div class="opts">${opts}</div>${after}${tools}`,
    };
  },

  /* A8 Results */
  results() {
    const done = P.ids.filter((id) => P.res[id]);
    const ok = done.filter((id) => P.res[id] === 'ok').length;
    const pct = done.length ? Math.round((ok / done.length) * 100) : 0;
    const wrong = done.filter((id) => P.res[id] === 'bad');
    const plus = P.ids.filter((id) => mastered(id) && !P.before[id]).length;
    const per = perTopic(done, (id) => P.res[id] === 'ok');
    const worst = Object.entries(per).filter(([, [a, b]]) => a < b).sort((x, y) => (x[1][0] - x[1][1]) - (y[1][0] - y[1][1]))[0];
    const head = pct >= 90 ? 'Excellent' : pct >= 70 ? 'Good session' : pct >= 50 ? 'Getting there' : 'Keep going';
    let copy = wrong.length
      ? `${short(worst[0])} needs the most work — ${worst[1][1] - worst[1][0]} of ${plural(wrong.length, 'mistake')} ${worst[1][1] - worst[1][0] === 1 ? 'was' : 'were'} there.`
      : 'No mistakes this time.';
    copy += plus ? ` ${plural(plus, 'question')} moved to mastered.` : '';
    const after = levelPct();
    return {
      title: 'Results',
      main: wrong.length ? { text: `Practise ${lower(short(worst[0]))}`, act: () => startPractice(pickFor(topicIds(worst[0]), 10)) } : { text: 'Practise more', act: () => openSetup() },
      second: wrong.length ? { text: `Mistakes · ${wrong.length}`, icon: 'refresh', act: () => go('review', { items: wrong.map((id) => ({ id, pick: P.picks[id] })), label: 'This session', from: 'session' }) } : null,
      body: `<div class="score"><span class="ring l" style="--v:${pct}"><b>${ok}/${done.length}</b><small>correct</small></span>
          <h2 class="display" style="font-size:34px">${head}</h2><p class="body-muted">${copy}</p></div>
        <div class="stats"><div class="stat"><b>${pct}%</b><span class="meta">score</span></div><div class="stat"><b>${fmt(P.secs * 1000)}</b><span class="meta">time</span></div><div class="stat"><b>+${plus}</b><span class="meta">mastered</span></div></div>
        <div class="stack g8"><span class="kicker">By topic</span>${tbars(per)}</div>
        <p class="hint hint-line">Mastery: ${P.lvlBefore}% → ${after}%</p>`,
    };
  },

  /* A9 Review mistakes (a session's, an exam's, or the running list) */
  review(c) {
    const items = c.items.filter((x) => Q[x.id]);
    const cards = items.map(({ id, pick }) => {
      const q = Q[id];
      const yours = c.from === 'all' ? '' : pick == null
        ? `<div class="ans bad"><span class="l">${svg('x', 12)}</span><span>Not answered</span></div>`
        : pick !== q.answer ? `<div class="ans bad"><span class="l">${svg('x', 12)}</span><span>${esc(q.options[pick])}</span></div>` : '';
      return `<div class="rev"><span class="chip" style="align-self:flex-start">${esc(TT[q.topic])}</span>${figHtml(q)}<p class="q">${esc(q.q)}</p>${yours}
        <div class="ans ok"><span class="l">${svg('check', 12)}</span><span>${esc(q.options[q.answer])}</span></div>
        <p class="body-muted" style="font-size:14px">${esc(q.why)}</p></div>`;
    }).join('');
    const total = allMistakes().length;
    return {
      title: 'Mistakes',
      main: items.length ? { text: 'Practise these again', act: () => startPractice(shuffle(items.map((x) => x.id)), true) } : null,
      body: `<div class="stack g4"><span class="meta">${esc(c.label)} · ${items.length}</span><h2 class="display-s">Review mistakes</h2></div>
        ${cards || '<p class="body-muted empty">Nothing to review — no mistakes here.</p>'}
        ${c.from !== 'all' && total ? `<div class="row sb-between" style="padding-top:4px"><span class="kicker">All mistakes</span><button class="meta acc" data-act="allMistakes">${plural(total, 'question')} ›</button></div>` : ''}`,
    };
  },

  /* B1 Exam intro (also the Exam tab) */
  examIntro() {
    const atts = S.exams.slice(0, 5).map((e) => `<div class="att"><span class="card-meta">${day(e.at)}</span><span class="card-meta">${e.pct}% · <span class="${e.passed ? 'acc' : 'bad-t'}">${e.passed ? 'passed' : 'not passed'}</span></span></div>`).join('');
    return {
      title: 'Mock exam', nav: 'examIntro',
      main: { text: S.exam ? 'Continue the exam' : 'Start the exam', act: startExam },
      second: S.exam ? { text: 'Start over', act: restartExam, pos: 'bottom' } : null,
      body: `<div class="stack g8"><span class="meta">Bareboat Skipper</span><h2 class="display">Mock exam</h2>
          <p class="body-muted">Like the real one: random questions from all ${TOPICS.length} topics, a timer, and the answers only at the end.</p></div>
        <div class="stats"><div class="stat"><b>${BANK.examQuestions}</b><span class="meta">questions</span></div><div class="stat"><b>${BANK.examMinutes}</b><span class="meta">minutes</span></div><div class="stat"><b>${BANK.passMark}%</b><span class="meta">to pass</span></div></div>
        ${S.exam ? `<div class="continue" data-act="main"><div><span class="meta">In progress</span><div class="card-title" style="margin-top:4px">${examLine()}</div></div><span class="mini mini-accent">Continue</span></div>` : ''}
        <div class="steps steps-plain">
          <div class="step step-num"><span class="step-ico">1</span><div><div class="card-title">Answer in any order</div><div class="card-meta">Flag a question and come back to it from the overview grid.</div></div></div>
          <div class="step step-num"><span class="step-ico">2</span><div><div class="card-title">No explanations until you submit</div><div class="card-meta">Afterwards every mistake shows the right answer and why.</div></div></div>
          <div class="step step-num"><span class="step-ico">3</span><div><div class="card-title">Leaving pauses the timer</div><div class="card-meta">Close the app and the exam waits for you, up to 24 hours.</div></div></div>
        </div>
        ${atts ? `<div class="band" style="padding:16px 18px"><div class="card-title" style="margin-bottom:4px">Last attempts</div>${atts}</div>` : ''}
        <p class="hint">Exam size, time and pass mark are app defaults, not confirmed IYT figures.</p>`,
    };
  },

  /* B2 Exam question */
  exam() {
    const E = S.exam, n = E.ids.length, id = E.ids[E.i], q = Q[id], ord = E.ord[id];
    const sel = E.ans[id] == null ? -1 : ord.indexOf(E.ans[id]);
    const left = remaining();
    const opts = ord.map((oi, k) => `<div class="opt${k === sel ? ' sel' : ''}" data-act="eopt" data-n="${k}" role="button"><span class="l">${'ABCD'[k]}</span><span>${esc(q.options[oi])}</span></div>`).join('');
    const fl = E.flags.includes(E.i);
    return {
      title: 'Mock exam',
      main: E.i < n - 1 ? { text: 'Next ›', act: () => examMove(1) } : { text: 'Finish…', act: () => { sheet = { v: 'grid' }; render(); } },
      second: E.i > 0 ? { text: '‹ Previous', act: () => examMove(-1) } : null,
      body: `<div class="bar ink"><i style="width:${((E.i + 1) / n) * 100}%"></i></div>
        <div class="qhead"><span class="meta meta-ink">${E.i + 1} of ${n}</span><span class="timer${left < 300000 ? ' low' : ''}"><span data-i="timer" data-s="16"></span><b>${fmt(left)}</b></span></div>
        ${figHtml(q)}<p class="q">${esc(q.q)}</p><div class="opts">${opts}</div>
        <div class="qtools"><button class="mini${fl ? ' on' : ''}" data-act="eflag"><span data-i="flag" data-s="14"></span>${fl ? 'Flagged' : 'Flag'}</button>
          <button class="mini" data-act="grid"><span data-i="board-view" data-s="14"></span>All questions</button></div>`,
    };
  },

  /* B4 Passed / B5 Not passed */
  examResult() {
    const R = S.last;
    if (!R) return { title: 'Result', body: '<p class="body-muted empty">No exam result yet.</p>' };
    const per = perTopic(R.ids, (id) => R.ans[id] === Q[id].answer);
    const weak = TOPICS.filter((t) => per[t.id] && per[t.id][0] / per[t.id][1] < BANK.passMark / 100).map((t) => t.id);
    const wrong = R.ids.filter((id) => R.ans[id] !== Q[id].answer);
    const names = weak.slice().sort((a, b) => (per[a][0] - per[a][1]) - (per[b][0] - per[b][1])).slice(0, 3).map(short);
    const reviewAct = () => go('review', { items: wrong.map((id) => ({ id, pick: R.ans[id] })), label: 'Mock exam', from: 'exam' });
    let head, copy, bars;
    if (R.passed) {
      head = R.pct >= 85 ? 'Ready for the&nbsp;exam' : 'Passed';
      copy = `Time used ${fmt(R.secs * 1000)} of ${BANK.examMinutes}:00. ` + (weak.length ? `${plural(weak.length, 'topic')} under ${BANK.passMark}% — worth one more look.` : `Every topic at ${BANK.passMark}% or more.`);
      bars = `<div class="stack g8"><span class="kicker">By topic</span>${tbars(per, BANK.passMark)}</div>`;
    } else {
      head = R.pct >= BANK.passMark - 10 && weak.length ? `Close — ${plural(weak.length, 'topic')} short` : 'Not passed this time';
      copy = (R.left ? `${plural(R.left, 'question')} ${R.left === 1 ? 'was' : 'were'} left unanswered${R.auto ? ' when the time ran out' : ''}. ` : '') +
        (names.length ? `${names.join(', ')} cost you the most points.` : '');
      const fine = {}, bad = {};
      for (const t in per) (weak.includes(t) ? bad : fine)[t] = per[t];
      bars = (weak.length ? `<div class="stack g8"><span class="kicker">Work on these first</span>${tbars(bad, BANK.passMark)}</div>` : '') +
        (Object.keys(fine).length ? `<div class="stack g8"><span class="kicker">Fine</span>${tbars(fine, BANK.passMark)}</div>` : '');
    }
    return {
      title: 'Result',
      main: R.passed
        ? (wrong.length ? { text: `Mistakes · ${wrong.length}`, icon: 'refresh', act: reviewAct } : { text: 'Back to the level', act: () => { stack = [{ v: 'home' }, { v: 'level' }]; render(true); } })
        : { text: weak.length ? `Practise the ${plural(weak.length, 'weak topic')}` : 'Practise', icon: 'play', act: () => startPractice(pickFor(weak.flatMap(topicIds), 20)) },
      second: R.passed ? { text: 'Share', icon: 'share', act: () => share(R) } : (wrong.length ? { text: `Review ${plural(wrong.length, 'mistake')}`, act: reviewAct, pos: 'bottom' } : null),
      body: `<div class="score">${R.passed ? `<span class="pass">${svg('trophy', 16)}Passed</span>` : `<span class="pass no">${svg('x', 16)}Not yet · ${BANK.passMark}% to pass</span>`}
          <span class="ring l${R.passed ? '' : ' bad'}" style="--v:${R.pct}"><b>${R.pct}%</b><small>${R.ok} of ${R.n}</small></span>
          <h2 class="display" style="font-size:34px">${head}</h2><p class="body-muted">${esc(copy)}</p></div>${bars}`,
    };
  },

  /* C1 Progress */
  progress() {
    const lp = levelPct(), st = streak();
    const week = Array.from({ length: 7 }, (_, k) => { const d = new Date(); d.setDate(d.getDate() - 6 + k); return { d, n: S.days[dkey(d)] || 0 }; });
    const max = Math.max(1, ...week.map((w) => w.n)), sum = week.reduce((a, w) => a + w.n, 0);
    const days = week.map((w, k) => `<div class="${k === 6 ? 'today' : ''}"><i class="${w.n ? '' : 'z'}" style="height:${w.n ? Math.max(8, (w.n / max) * 100) : 4}%"></i><span>${DAYS[w.d.getDay()]}</span></div>`).join('');
    const mis = allMistakes().length, fl = S.flags.filter((id) => Q[id]).length;
    return {
      title: 'IYT Test', nav: 'progress',
      body: `<div class="stack g4"><span class="meta">Bareboat Skipper</span><h2 class="display-s">Progress</h2></div>
        <div class="stats"><div class="stat"><b>${lp}%</b><span class="meta">mastered</span></div><div class="stat"><b>${S.total}</b><span class="meta">answered</span></div><div class="stat"><b>${st}</b><span class="meta">day streak</span></div></div>
        <div class="band" style="padding:16px 18px"><div class="row sb-between" style="margin-bottom:12px"><span class="kicker">This week</span><span class="meta">${plural(sum, 'question')}</span></div><div class="days">${days}</div></div>
        <div class="stack g8"><div class="row sb-between"><span class="kicker">Mastery by topic</span><button class="meta acc" data-act="setup">Practise weakest ›</button></div>${topicRows()}</div>
        <div class="row sb-between"><div><div class="card-title">Mistakes to clear</div><div class="card-meta">${mis ? `${plural(mis, 'question')} answered wrong and not yet mastered` : 'None right now'}</div></div><button class="mini mini-accent${mis ? '' : ' off'}" data-act="allMistakes">Review</button></div>
        <div class="row sb-between"><div><div class="card-title">Flagged questions</div><div class="card-meta">${fl ? plural(fl, 'question') : 'Flag a question to keep it here'}</div></div><button class="mini mini-accent${fl ? '' : ' off'}" data-act="flagged">Practise</button></div>`,
    };
  },

  /* C2 Profile */
  profile() {
    const u = (IN_TG && TG.initDataUnsafe && TG.initDataUnsafe.user) || null;
    const name = u ? [u.first_name, u.last_name].filter(Boolean).join(' ') : 'Guest';
    const ini = name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();
    const ava = u && u.photo_url ? `<img src="${esc(u.photo_url)}" alt="">` : esc(ini);
    const th = S.set.theme;
    const seg = (v, inner) => `<button class="lang${th === v ? ' lang-on' : ''}" data-act="theme" data-t="${v}">${inner}</button>`;
    const tog = (k) => `<button class="toggle${S.set[k] ? ' on' : ''}" data-act="set" data-k="${k}" aria-pressed="${S.set[k]}"></button>`;
    return {
      title: 'IYT Test', nav: 'profile',
      body: `<div class="row" style="gap:14px"><span class="tg-ava" style="width:52px;height:52px;font-size:16px">${ava}</span><div><div class="card-title" style="font-size:18px">${esc(name)}</div>
          <div class="card-meta">${u ? (u.username ? '@' + esc(u.username) + ' · ' : '') + 'progress synced with Telegram' : 'Progress is saved in this browser'}</div></div></div>
        <div class="stack">
          <div class="set"><div class="card-title">Current level</div><span class="chip chip-on">Bareboat Skipper</span></div>
          <div class="set"><div class="card-title">Theme</div><div class="langs">${seg('day', svg('sun', 14))}${seg('night', svg('moon', 14))}${seg('auto', 'Auto')}</div></div>
          <div class="set"><div><div class="card-title">Shuffle options</div><div class="card-meta">Different order each time</div></div>${tog('shuffle')}</div>
          <div class="set"><div><div class="card-title">Explain after each answer</div><div class="card-meta">Off = exam style, results at the end</div></div>${tog('feedback')}</div>
          <div class="set"><div><div class="card-title">Reset progress</div><div class="card-meta">Mastery, mistakes, streak and exams</div></div><button class="danger-link" data-act="reset">Reset</button></div>
        </div>
        <p class="hint">Questions are written for study and are not official IYT exam content. Bank version ${esc(BANK.version)}.</p>`,
    };
  },
};

/* A3 Set up a session · B3 Exam grid */
const SHEETS = {
  setup(s) {
    const pool = setupPool(s), N = pool.length, size = s.size === 'all' ? N : Math.min(s.size, N);
    const misAll = allMistakes();
    const chips = TOPICS.map((t) => {
      const c = s.mis ? topicIds(t.id).filter(isMistake).length : topicIds(t.id).length;
      return `<button class="tag${s.on.has(t.id) ? ' tag-on' : ''}${s.mis && !c ? ' off' : ''}" style="min-height:40px;font-size:15px;padding:0 14px" data-act="chip" data-t="${t.id}">${esc(short(t.id))}<span class="tag-count">${c}</span></button>`;
    }).join('');
    const sz = (v, label) => `<button class="tag${s.size === v ? ' tag-on' : ''}" style="min-height:40px;font-size:15px" data-act="size" data-s="${v}">${label}</button>`;
    return `<div class="stack g4"><span class="meta">Practice</span><h2 class="display-s">What to practise?</h2></div>
      <div class="stack g8"><div class="row sb-between"><span class="kicker">Topics</span><button class="meta acc" data-act="chipsAll">${s.on.size === TOPICS.length ? 'None' : 'All'}</button></div>
        <div class="tags">${chips}</div><span class="hint">${weakTopics().length ? 'Weak topics are preselected. ' : ''}Tap to add or remove.</span></div>
      <div class="stack g8"><span class="kicker">Questions</span><div class="tags">${N > 10 ? sz(10, '10') : ''}${N > 20 ? sz(20, '20') : ''}${sz('all', `All ${N}`)}
        <button class="tag${s.mis ? ' tag-on' : ''}${misAll.length ? '' : ' off'}" style="min-height:40px;font-size:15px" data-act="mis"><span data-i="refresh" data-s="16"></span>Mistakes only</button></div></div>
      <div class="set" style="border:0;padding:6px 0 0"><div><div class="card-title">Show the answer after each question</div><div class="card-meta">Off = exam style, results at the end</div></div><button class="toggle${s.fb ? ' on' : ''}" data-act="fb"></button></div>
      <button class="pill pill-primary pill-wide${size ? '' : ' off'}" data-act="start">${size ? `Start · ${plural(size, 'question')}` : 'Pick a topic'}</button>`;
  },
  grid() {
    const E = S.exam, a = E.ids.filter((id) => E.ans[id] != null).length, left = E.ids.length - a;
    const cells = E.ids.map((id, k) => `<span class="${E.ans[id] != null ? 'a' : ''}${E.flags.includes(k) ? ' f' : ''}${k === E.i ? ' now' : ''}" data-act="jump" data-n="${k}">${k + 1}</span>`).join('');
    return `<div class="row sb-between"><div class="stack g4"><span class="meta">Overview</span><h2 class="display-s" style="font-size:26px">${a} answered · ${left} left</h2></div>
        <span class="timer"><span data-i="timer" data-s="16"></span><b>${fmt(remaining())}</b></span></div>
      <div class="grid40">${cells}</div>
      <div class="legend-row"><span><i class="a"></i>Answered</span><span><i></i>Not yet</span><span><i class="f"></i>Flagged</span></div>
      <button class="pill ${left ? 'pill-quiet' : 'pill-primary'} pill-wide" data-act="submit">Submit exam</button>
      <span class="hint" style="text-align:center">${left ? `Submitting with ${left} unanswered counts them as wrong.` : 'All answered — submit when you are ready.'}</span>`;
  },
};

/* ---------- practice ---------- */
function defaultTopics() {
  const w = weakTopics();
  return w.length ? w : TOPICS.map((t) => t.id);
}
function openSetup(topics) {
  sheet = { v: 'setup', on: new Set(topics || defaultTopics()), size: 10, mis: false, fb: S.set.feedback };
  render();
}
function setupPool(s) {
  const ids = TOPICS.filter((t) => s.on.has(t.id)).flatMap((t) => topicIds(t.id));
  return s.mis ? ids.filter(isMistake) : ids;
}
// Mistakes first, then questions not yet mastered, then the rest; the chosen ones come in random order.
function pickFor(pool, n) {
  const groups = [pool.filter(isMistake), pool.filter((id) => !isMistake(id) && !mastered(id)), pool.filter(mastered)];
  return shuffle(groups.flatMap(shuffle).slice(0, n));
}
function startPractice(ids, fb = S.set.feedback) {
  if (!ids.length) return toast('No questions to practise');
  P = {
    ids, i: 0, res: {}, picks: {}, sel: null, checked: false, fb, t0: Date.now(), done: false,
    orders: Object.fromEntries(ids.map((id) => [id, S.set.shuffle ? shuffle([0, 1, 2, 3]) : [0, 1, 2, 3]])),
    before: Object.fromEntries(ids.map((id) => [id, mastered(id)])), lvlBefore: levelPct(),
  };
  if (['results', 'review', 'examResult'].includes(cur().v)) replace('question'); else go('question');
}
function check() {
  if (P.sel == null || P.checked) return;
  const id = P.ids[P.i], oi = P.orders[id][P.sel], ok = oi === Q[id].answer;
  record(id, ok);
  P.res[id] = ok ? 'ok' : 'bad';
  P.picks[id] = oi;
  P.checked = true;
  hap(ok ? 'success' : 'error');
  save();
  render();
  $app.querySelector('#why')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}
function silentNext() {
  if (P.sel == null) return;
  const id = P.ids[P.i], oi = P.orders[id][P.sel], ok = oi === Q[id].answer;
  record(id, ok);
  P.res[id] = ok ? 'ok' : 'bad';
  P.picks[id] = oi;
  save();
  nextQ();
}
function nextQ() {
  P.i++; P.sel = null; P.checked = false;
  if (P.i >= P.ids.length) { P.done = true; P.secs = Math.round((Date.now() - P.t0) / 1000); replace('results'); }
  else render(true);
}

/* ---------- mock exam ---------- */
let timerInt = null, lastTick = 0, ticks = 0;
const remaining = () => (S.exam ? Math.max(0, BANK.examMinutes * 60000 - S.exam.el) : 0);
function startTimer() { if (timerInt) return; lastTick = Date.now(); timerInt = setInterval(tick, 1000); }
function stopTimer() { clearInterval(timerInt); timerInt = null; }
function tick() {
  if (!S.exam) return stopTimer();
  const now = Date.now();
  if (document.visibilityState === 'visible') S.exam.el += now - lastTick;
  lastTick = now;
  S.exam.last = now;
  const left = remaining();
  $app.querySelectorAll('.timer b').forEach((b) => { b.textContent = fmt(left); });
  $app.querySelectorAll('.timer').forEach((t) => t.classList.toggle('low', left < 300000));
  if (left <= 0) return submitExam(true);
  if (++ticks % 5 === 0) save(false);
}
function buildExam() {
  const n = Math.min(BANK.examQuestions, BANK.questions.length);
  const groups = shuffle(TOPICS.map((t) => shuffle(topicIds(t.id)))); // round-robin over topics: an even spread
  const ids = [];
  while (ids.length < n && groups.some((g) => g.length)) for (const g of groups) if (g.length && ids.length < n) ids.push(g.pop());
  const order = shuffle(ids);
  S.exam = { ids: order, ord: Object.fromEntries(order.map((id) => [id, S.set.shuffle ? shuffle([0, 1, 2, 3]) : [0, 1, 2, 3]])), ans: {}, flags: [], el: 0, i: 0, at: Date.now(), last: Date.now() };
  save();
}
function startExam() {
  if (!S.exam) buildExam();
  go('exam');
}
async function restartExam() {
  if (!(await confirmBox('Start a new exam? The one in progress will be dropped.'))) return;
  S.exam = null;
  buildExam();
  go('exam');
}
function examMove(d) {
  const E = S.exam;
  E.i = Math.max(0, Math.min(E.ids.length - 1, E.i + d));
  save(false);
  render(true);
}
async function submitExam(auto) {
  const E = S.exam;
  if (!E) return;
  const left = E.ids.filter((id) => E.ans[id] == null).length;
  if (!auto && left && !(await confirmBox(`${plural(left, 'question')} unanswered will count as wrong. Submit the exam?`))) return;
  stopTimer();
  let ok = 0;
  E.ids.forEach((id) => {
    const a = E.ans[id], c = a === Q[id].answer;
    if (c) ok++;
    if (a != null) record(id, c); // unanswered questions do not touch mastery
  });
  const n = E.ids.length, pct = Math.round((ok / n) * 100), passed = pct >= BANK.passMark;
  const R = { at: Date.now(), ok, n, pct, passed, secs: Math.round(E.el / 1000), left, auto: !!auto, ids: E.ids, ans: E.ans };
  S.exams = [{ at: R.at, ok, n, pct, passed, secs: R.secs }, ...S.exams].slice(0, 20);
  S.last = R;
  S.exam = null;
  save();
  cloudSave();
  hap(passed ? 'success' : 'error');
  if (cur().v === 'exam') { sheet = null; replace('examResult'); }
}
function share(R) {
  const text = `I scored ${R.pct}% on the IYT Bareboat Skipper mock exam — practice questions for IYT levels:`;
  if (IN_TG) TG.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(BOT_LINK)}&text=${encodeURIComponent(text)}`);
  else if (navigator.share) navigator.share({ text, url: BOT_LINK }).catch(() => {});
  else { navigator.clipboard?.writeText(`${text} ${BOT_LINK}`); toast('Copied to the clipboard'); }
}

/* ---------- taps ---------- */
const ACT = {
  back,
  main: () => mainCb && mainCb(),
  second: () => secCb && secCb(),
  tab: (d) => tab(d.v),
  level: () => go('level'),
  examIntro: () => (cur().v === 'examIntro' ? null : go('examIntro')),
  setup: (d) => openSetup(d.t ? [d.t] : undefined),
  allMistakes: () => go('review', { items: allMistakes().map((id) => ({ id })), label: 'All mistakes', from: 'all' }),
  flagged: () => startPractice(pickFor(S.flags.filter((id) => Q[id]), 20)),
  // set-up sheet
  chip: (d) => { const s = sheet; s.on.has(d.t) ? s.on.delete(d.t) : s.on.add(d.t); hap('sel'); render(); },
  chipsAll: () => { sheet.on = new Set(sheet.on.size === TOPICS.length ? [] : TOPICS.map((t) => t.id)); render(); },
  size: (d) => { sheet.size = d.s === 'all' ? 'all' : +d.s; hap('sel'); render(); },
  mis: () => { sheet.mis = !sheet.mis; if (sheet.mis) sheet.size = 'all'; render(); },
  fb: () => { sheet.fb = !sheet.fb; S.set.feedback = sheet.fb; save(); render(); },
  start: () => { const s = sheet, pool = setupPool(s); startPractice(pickFor(pool, s.size === 'all' ? pool.length : s.size), s.fb); },
  // practice question
  opt: (d) => { if (P.checked) return; P.sel = +d.n; hap('sel'); render(); },
  flag: () => {
    const id = P.ids[P.i], k = S.flags.indexOf(id);
    k >= 0 ? S.flags.splice(k, 1) : S.flags.push(id);
    save(); render(); toast(k >= 0 ? 'Removed from flagged' : 'Flagged — find it in Progress');
  },
  skip: () => { const [id] = P.ids.splice(P.i, 1); P.ids.push(id); P.sel = null; render(true); },
  // exam
  eopt: (d) => { const E = S.exam, id = E.ids[E.i]; E.ans[id] = E.ord[id][+d.n]; hap('sel'); save(false); render(); },
  eflag: () => { const E = S.exam, k = E.flags.indexOf(E.i); k >= 0 ? E.flags.splice(k, 1) : E.flags.push(E.i); save(false); render(); },
  grid: () => { sheet = { v: 'grid' }; render(); },
  jump: (d) => { S.exam.i = +d.n; sheet = null; save(false); render(true); },
  submit: () => submitExam(false),
  // profile
  theme: (d) => { S.set.theme = d.t; save(); applyTheme(); render(); },
  set: (d) => { S.set[d.k] = !S.set[d.k]; save(); render(); },
  reset: async () => {
    if (!(await confirmBox('Reset all progress? Mastery, mistakes, streak and exam history will be cleared.'))) return;
    const set = S.set;
    S = fresh(); S.set = set;
    save(); cloudSave(); toast('Progress reset'); render();
  },
};
$app.addEventListener('click', (e) => {
  const el = e.target.closest('[data-act]');
  if (!el || !$app.contains(el)) return;
  const fn = ACT[el.dataset.act];
  if (fn) fn(el.dataset, el);
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') back();
  const c = cur();
  if (sheet || (c.v !== 'question' && c.v !== 'exam')) return;
  const k = 'abcd'.indexOf(e.key.toLowerCase()), num = '1234'.indexOf(e.key);
  const n = k >= 0 ? k : num;
  if (n >= 0) ACT[c.v === 'exam' ? 'eopt' : 'opt']({ n });
  if (e.key === 'Enter' && mainCb) { e.preventDefault(); ACT.main(); }
});
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') { if (timerInt) tick(); save(false); cloudSave(); }
  else lastTick = Date.now(); // time spent away does not count
});

/* ---------- start ---------- */
function deepLink() {
  const p = (IN_TG && TG.initDataUnsafe && TG.initDataUnsafe.start_param) || new URLSearchParams(location.search).get('screen') || '';
  if (p === 'exam') stack = [{ v: 'examIntro' }];
  else if (p === 'progress') stack = [{ v: 'progress' }];
  else if (p === 'profile' || p === 'settings') stack = [{ v: 'profile' }];
  else if (p === 'bareboat' || p === 'level') stack = [{ v: 'home' }, { v: 'level' }];
  else if (p === 'practice') { stack = [{ v: 'home' }, { v: 'level' }]; return 'setup'; }
  return null;
}
function expireExam() {
  // an exam left for more than 24 hours is graded as it stands
  if (S.exam && Date.now() - S.exam.last > 24 * 3600 * 1000) submitExam(true);
}

async function init() {
  if (TG) {
    try { TG.ready(); TG.expand(); } catch (e) {}
    if (tgv('7.7')) try { TG.disableVerticalSwipes(); } catch (e) {}
    if (tgv('6.1')) TG.BackButton.onClick(back);
    if (NATIVE_BUTTONS) { TG.MainButton.onClick(() => ACT.main()); TG.SecondaryButton.onClick(() => ACT.second()); }
    if (IN_TG) TG.onEvent('themeChanged', () => { applyTheme(); render(); });
  }
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => { applyTheme(); render(); });
  loadLocal();
  applyTheme();
  const res = await fetch(LEVELS[0].file, { cache: 'no-cache' });
  if (!res.ok) throw new Error('Could not load the question bank (' + res.status + ')');
  BANK = await res.json();
  BANK.questions.forEach((q) => { Q[q.id] = q; });
  TOPICS = BANK.topics;
  TT = Object.fromEntries(TOPICS.map((t) => [t.id, t.title]));
  const remote = await cloudLoad();
  if (remote && remote.ts > S.ts) { S = merge(remote); applyTheme(); try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  prune();
  expireExam();
  const then = deepLink();
  render(true);
  if (then === 'setup') openSetup();
}
init().catch((e) => {
  $app.innerHTML = `<div class="boot"><div class="stack g8" style="padding:24px;text-align:center"><span class="meta">Something went wrong</span><p class="body-muted">${esc(e.message)}</p></div></div>`;
  console.error(e);
});
