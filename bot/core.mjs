// @iyt_test_bot's replies, shared by the two ways the bot runs:
//   api/telegram.mjs   Vercel function — Telegram posts each update to it (webhook, always on)
//   bot/bot.mjs        long polling from any machine (local testing; needs the webhook removed)
//
// /start, /exam, /progress, /settings reply with a button into the mini app (WEBAPP_URL, opened at the right
// screen via ?screen=…). /daily sends one question with A–D buttons; the answer and the one-line note come
// back in the same message (design C3), with a button to the theory article section that explains it. Only questions
// with a photo (the Blender render, miniapp/figs/q/…) are sent: the photo goes with the question, its caption holds
// the text. The language is the user's own choice in the app (EN/RU in the profile), else their Telegram app's.
// Every private message is saved to Supabase users; /settings and the scheduled question (bot/daily.mjs) carry the
// user's on/off switch for the question of the day.

import { readFile } from 'node:fs/promises';
import { SITE, PAUSED } from '../miniapp/site.mjs';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) throw new Error('TELEGRAM_BOT_TOKEN is not set');
export const webapp = (process.env.WEBAPP_URL || '').replace(/\/$/, '');

// The levels with a bank, in IYT order, then the Racing Rules and the Charter Check-in; `link` is the mini app deep link that opens the level (miniapp/app.js LEVELS).
const LEVELS = [['vhf-radio-operator', 'vhf'], ['international-crew', 'crew'], ['flotilla-skipper', 'flotilla'], ['bareboat-skipper', 'bareboat'], ['yachtmaster-coastal', 'coastal'], ['yachtmaster-offshore', 'offshore'], ['yachtmaster-ocean', 'ocean'], ['racing-rules', 'racing'], ['charter-checkin', 'checkin']];
// A bank comes from data/questions/<name>.json, bundled with the function (vercel.json includeFiles): all 18 files
// read and parse in under 0.1 s, where fetching them from Supabase held up a cold start for seconds. Supabase —
// bank() / bank_overlay() return the same shape as the files (docs/data-model.md) — is the fallback for a missing file.
// The Russian texts carry English sailing terms as tags, "створом [[transit]]" (docs/theory.md); the bot leaves them out.
const untag = (text) => JSON.parse(text, (k, v) => (typeof v === 'string' ? v.replace(/ \[\[[^\]]*\]\]/g, '') : v));
async function read(name) {
  try { return untag(await readFile(new URL(`../data/questions/${name}.json`, import.meta.url), 'utf8')); }
  catch (e) { if (e.code !== 'ENOENT') throw e; }
  const [level, lang] = name.split('.');
  const url = (process.env.SUPABASE_URL || '').replace(/\/$/, ''), key = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_PUBLISHABLE_KEY || '';
  if (!url || !key) throw new Error(`no bank ${name}`);
  const fn = lang ? `bank_overlay?p_level=${level}&p_lang=${lang}` : `bank?p_level=${level}`;
  const res = await fetch(`${url}/rest/v1/rpc/${fn}`, { headers: { apikey: key, ...(key.startsWith('eyJ') && { authorization: `Bearer ${key}` }) }, signal: AbortSignal.timeout(8000) });
  const b = res.ok ? untag(await res.text()) : null;
  if (!b) throw new Error(`no bank ${name}`);
  return b;
}
// Each bank with its Russian overlay (data/i18n.py): translated questions and topic titles; anything missing stays English.
// A level with no bank in the database or in the files yet is left out.
const banks = (await Promise.all(LEVELS.filter(([id]) => !PAUSED.includes(id)).map(async ([id, link]) => { // not the paused ones (site.mjs)
  const bank = await read(id).catch(() => null);
  return bank && { id, link, bank, ru: await read(`${id}.ru`).catch(() => ({})) };
}))).filter(Boolean);
const byId = {};
for (const b of banks) for (const q of b.bank.questions) byId[q.id] = { q, b };
let daily = []; // the questions the bot sends: filled below, next to the pools
// The theory article of each topic (data/theory/<level>/<topic>.json, bundled like the banks): only what a link to it
// needs — its sections' ids and kickers, and the rule references each one explains (refs, docs/theory.md).
// A topic without an article gets no link; an article without a Russian translation is linked in English.
const readArt = (p) => readFile(new URL(`../data/theory/${p}.json`, import.meta.url), 'utf8').then(untag, () => null);
const articles = {}; // "<level>/<topic>" → { secs: [{ id, kicker, refs }], ru: { <section id>: kicker } | null }
await Promise.all(banks.flatMap((b) => b.bank.topics.map(async (tp) => {
  const [en, ru] = await Promise.all([readArt(`${b.id}/${tp.id}`), readArt(`${b.id}/${tp.id}.ru`)]);
  if (!en || !Array.isArray(en.sections)) return;
  articles[`${b.id}/${tp.id}`] = { secs: en.sections.map(({ id, kicker, refs }) => ({ id, kicker, refs: refs || [] })),
    ru: ru && Array.isArray(ru.sections) ? Object.fromEntries(ru.sections.map((x) => [x.id, x.kicker])) : null };
})));
const N = Object.keys(byId).length;
const names = banks.map((b) => b.bank.title.replace(/^IYT /, ''));
// The question, its topic title and level in the reader's language.
function local(q, isRu) {
  const { b } = byId[q.id], RU_BANK = (isRu && b.ru) || {};
  const title = (RU_BANK.topics && RU_BANK.topics[q.topic]) || b.bank.topics.find((t) => t.id === q.topic).title;
  const tr = RU_BANK.questions && RU_BANK.questions[q.id];
  const lv = b.bank.title.replace(/^IYT /, '');
  return tr && tr.q && tr.options?.length === 4 ? { ...q, ...tr, title, lv, link: b.link, tr: true } : { ...q, title, lv, link: b.link, tr: false };
}
// The question's photo on the site: the Russian copy (labels in Russian) for a translated question read in Russian.
const photoUrl = (q, isRu) => `${webapp || SITE}/figs/${q.photo}${isRu && q.tr ? '.ru' : ''}.webp`;
const plain = (html) => html.replace(/<[^>]+>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');

export const api = async (method, params = {}) => {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(params) });
  const data = await res.json();
  if (!data.ok) throw Object.assign(new Error(`${method}: ${data.description}`), { code: data.error_code, retryAfter: data.parameters?.retry_after });
  return data.result;
};

// ---------- users and their daily-question switch: Supabase public.users, written with the secret key ----------
// Without SUPABASE_URL + SUPABASE_SECRET_KEY the bot still answers; it just remembers nobody and shows no switch.
const SB = (process.env.SUPABASE_URL || '').replace(/\/$/, ''), SB_KEY = process.env.SUPABASE_SECRET_KEY || '';
export const hasDb = !!(SB && SB_KEY);
export async function db(path, { method = 'GET', body, prefer } = {}) {
  // New secret keys (sb_secret_…) go in apikey only; a legacy service_role JWT also goes in Authorization.
  const headers = { apikey: SB_KEY, 'content-type': 'application/json', ...(SB_KEY.startsWith('eyJ') && { authorization: `Bearer ${SB_KEY}` }), ...(prefer && { prefer }) };
  const res = await fetch(`${SB}/rest/v1/${path}`, { method, headers, body: body && JSON.stringify(body) });
  if (!res.ok) throw new Error(`db ${method} ${path.split('?')[0]}: ${res.status} ${await res.text()}`);
  return method === 'GET' || prefer?.includes('return=representation') ? res.json() : null;
}
// Saves who wrote to the bot (private chats only: the daily question goes to the user's own chat) and returns their
// row, so callers know whether the daily question is on. A new user gets daily_question = true (the column default).
async function remember(from, chat) {
  if (!hasDb || !from || from.is_bot || chat?.type !== 'private') return null;
  const row = { id: from.id, name: [from.first_name, from.last_name].filter(Boolean).join(' ') || null, username: from.username || null,
    lang: RU(from) ? 'ru' : 'en', blocked_at: null, updated_at: new Date().toISOString() };
  try { return (await db('users?on_conflict=id&select=id,daily_question', { method: 'POST', body: row, prefer: 'resolution=merge-duplicates,return=representation' }))[0]; }
  catch (e) { console.error('remember', from.id, e.message); return null; }
}
const setDaily = (id, on) => db(`users?id=eq.${+id}`, { method: 'PATCH', body: { daily_question: on, updated_at: new Date().toISOString() } });
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const open = (text, screen) => (webapp ? [{ text, web_app: { url: screen ? `${webapp}/?screen=${screen}` : `${webapp}/` } }] : null);
const kb = (...rows) => ({ inline_keyboard: rows.filter(Boolean) });
const send = (chat_id, text, reply_markup) => api('sendMessage', { chat_id, text, parse_mode: 'HTML', reply_markup, link_preview_options: { is_disabled: true } });
// The /start welcome: a photo of a fleet beating upwind (miniapp/intro.jpg, served with the mini app) with the
// introduction as its caption. Without WEBAPP_URL, or if Telegram cannot fetch the photo, the same text goes alone.
// After the first send the photo goes by Telegram's file_id (kept while the function instance lives), so Telegram
// does not download it from the site again for every /start.
let introPhoto = null;
async function welcome(chat_id, ru) {
  const text = T.start(ru), reply_markup = kb(open(T.open(ru)), open(T.examBtn(ru), 'exam'));
  if (webapp) try {
    const sent = await api('sendPhoto', { chat_id, photo: introPhoto || `${webapp}/intro.jpg`, caption: text, parse_mode: 'HTML', reply_markup });
    introPhoto = sent.photo?.at(-1)?.file_id || introPhoto;
    return sent;
  } catch (e) { introPhoto = null; console.warn('welcome photo failed, sending text:', e.message); }
  return send(chat_id, text, reply_markup);
}

// The reply language follows the sender's Telegram app language (language_code on every update), with the same rule
// as the mini app (miniapp/app.js pickLang): Russian for ru, uk, be and kk, English for everyone else.
const RU = (from) => /^(ru|uk|be|kk)\b/i.test(from?.language_code || '');
// The language the user picked in the app (progress.state.set.lang, synced by api/progress.mjs), for each of `ids`:
// { <id>: 'ru' | 'en' }, with no entry for those who never picked one. Never fails ({} on any error).
export async function chosenLangs(ids) {
  if (!hasDb || !ids.length) return {};
  try {
    const rows = await db(`progress?select=user_id,lang:state->set->>lang&user_id=in.(${ids.map(Number).join(',')})`);
    return Object.fromEntries(rows.filter((r) => r.lang === 'ru' || r.lang === 'en').map((r) => [r.user_id, r.lang]));
  } catch (e) { console.error('chosenLangs', e.message); return {}; }
}
const prefersRu = async (from) => { const l = (await chosenLangs([from.id]))[from.id]; return l ? l === 'ru' : RU(from); };
// The language a question message was sent in rides in its buttons' callback data (…:r / …:e), so the answer comes
// back in the same language; buttons from before carry none and follow the Telegram app's language.
const tag = (ru) => (ru ? 'r' : 'e');
const tagRu = (t, from) => (t === 'r' ? true : t === 'e' ? false : RU(from));
const T = {
  start: (ru) => ru
    ? `⚓️ <b>Sailing Certification Test</b> — вопросы для подготовки к экзаменам на яхтенные сертификаты, по Правилам парусных гонок и по приёмке чартерной яхты. Уже доступны: <b>${names.join('</b>, <b>')}</b> — ${N} ситуаций, тренировка по темам и пробный экзамен.\n\nНажмите «Открыть» и выберите уровень.`
    : `⚓️ <b>Sailing Certification Test</b> — practice questions for sailing certification levels, the Racing Rules of Sailing and the charter check-in. Ready now: <b>${names.join('</b>, <b>')}</b> — ${N} situations, practice by topic and a mock exam.\n\nTap Open and pick your level.`,
  open: (ru) => (ru ? 'Открыть' : 'Open'),
  exam: (ru) => (ru ? '⏱ Пробный экзамен по вашему уровню: случайные вопросы из всех тем, таймер, ответы в конце, 70 % для сдачи.' : '⏱ Mock exam for your level: random questions from every topic, a timer, answers at the end, 70 % to pass.'),
  examBtn: (ru) => (ru ? 'Начать экзамен' : 'Start the exam'),
  progress: (ru) => (ru ? '📊 Прогресс по темам, ошибки и серия дней — в приложении.' : '📊 Your mastery by topic, mistakes and streak are in the app.'),
  progressBtn: (ru) => (ru ? 'Мой прогресс' : 'My progress'),
  settings: (ru) => (ru ? '⚙️ Тема, перемешивание вариантов и сброс прогресса — в профиле.' : '⚙️ Theme, option shuffling and progress reset are in your profile.'),
  settingsDaily: (ru) => (ru
    ? '🔔 <b>Вопрос дня</b>: каждый день в обед один вопрос в этом чате, ответ одной кнопкой. Кнопка ниже включает и выключает его.\n\n'
    : '🔔 <b>Question of the day</b>: one question in this chat every day at lunchtime, answered with one tap. The button below turns it on or off.\n\n'),
  dailyOn: (ru) => (ru ? '🔔 Вопрос дня: включён' : '🔔 Question of the day: on'),
  dailyOff: (ru) => (ru ? '🔕 Вопрос дня: выключен' : '🔕 Question of the day: off'),
  turnedOn: (ru) => (ru ? 'Вопрос дня включён — до завтра!' : 'Question of the day is on — see you tomorrow!'),
  turnedOff: (ru) => (ru ? 'Вопрос дня выключен. Включить снова — /settings' : 'Question of the day is off. Turn it back on in /settings'),
  settingsBtn: (ru) => (ru ? 'Настройки' : 'Settings'),
  practise: (ru) => (ru ? 'Тренироваться' : 'Practise more'),
  theory: (ru, what) => (ru ? `📖 Теория: ${what}` : `📖 Theory: ${what}`),
};

const head = (isRu) => (isRu ? 'Вопрос дня' : 'Question of the day');
// The on/off switch: one button whose label says the current state; tapping it flips it (callback dq:1 / dq:0).
const dailySwitch = (on, ru) => [{ text: on ? T.dailyOn(ru) : T.dailyOff(ru), callback_data: `dq:${on ? 0 : 1}:${tag(ru)}` }];
// One question with A–D buttons. `switchOn` (true/false) adds the on/off switch under them — the scheduled send does.
export function dailyMessage(src, isRu, switchOn) {
  const q = local(src, isRu);
  const text = `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` + q.options.map((o, i) => `<b>${'ABCD'[i]}</b>  ${esc(o)}`).join('\n');
  return { text, photo: q.photo ? photoUrl(q, isRu) : null,
    reply_markup: kb(q.options.map((_, i) => ({ text: 'ABCD'[i], callback_data: `d:${q.id}:${i}:${tag(isRu)}` })), switchOn != null && dailySwitch(switchOn, isRu)) };
}
// The same message after the answer: ✅ on the right option, ❌ on a wrong pick, then the note and the reference.
function answered(q, isRu, pick) {
  const ok = pick === q.answer;
  return `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` +
    q.options.map((o, i) => `${i === q.answer ? '✅' : i === pick ? '❌' : '▫️'}  ${esc(o)}`).join('\n') +
    `\n\n<b>${ok ? (isRu ? 'Верно.' : 'Correct.') : (isRu ? 'Неверно.' : 'Not quite.')}</b> ${esc(q.why)}\n<i>${esc(q.ref)}</i>`;
}
// Sends a question: its photo with the text as the caption. After the first send a photo goes by Telegram's file_id
// (kept while the function instance lives), so the daily send fetches each photo from the site once. If Telegram
// cannot take the photo, the question goes as text; a blocked chat or the flood limit is thrown to the caller.
const photoIds = new Map(); // photo URL → file_id
export async function sendQuestion(chat_id, src, isRu, switchOn) {
  const d = dailyMessage(src, isRu, switchOn);
  if (d.photo) try {
    const sent = await api('sendPhoto', { chat_id, photo: photoIds.get(d.photo) || d.photo, caption: d.text, parse_mode: 'HTML', reply_markup: d.reply_markup });
    const id = sent.photo?.at(-1)?.file_id;
    if (id) photoIds.set(d.photo, id);
    return sent;
  } catch (e) {
    if (e.code !== 400 || /chat not found/i.test(e.message)) throw e;
    photoIds.delete(d.photo);
    console.warn('question photo failed, sending text:', d.photo, e.message);
  }
  return send(chat_id, d.text, d.reply_markup);
}

// The article that explains a question, as a button to its page on the site (miniapp/pages.mjs: /<level>/<topic>,
// /ru/… when translated), opened at the section whose refs hold the question's reference, else at the top.
function theoryButton(src, isRu) {
  const { b } = byId[src.id], art = articles[`${b.id}/${src.topic}`];
  if (!art) return null;
  const ru = isRu && !!art.ru, sec = art.secs.find((x) => x.refs.includes(src.ref));
  const what = sec ? (ru && art.ru[sec.id]) || sec.kicker : local(src, isRu).title;
  return [{ text: T.theory(isRu, what), url: `${SITE}${ru ? '/ru' : ''}/${b.id}/${src.topic}${sec ? `#sec-${sec.id}` : ''}` }];
}

// Question of the day: the same question for everyone on a UTC day (per level once users have one), with its photo.
// The pool for /daily and the question of the day: questions with a photo whose answered caption fits Telegram's
// 1024-character limit in both languages. Their articles are linked in the reader's language when translated.
daily = Object.values(byId).map(({ q }) => q).filter((q) => q.photo && q.figure &&
  [false, true].every((ru) => plain(answered(local(q, ru), ru, (q.answer + 1) % 4)).length <= 1000));
const pools = Object.fromEntries(banks.map((b) => [b.id, daily.filter((q) => byId[q.id].b === b)]));
export function questionOfTheDay(day, levelId) {
  const pool = pools[levelId]?.length ? pools[levelId] : daily;
  let h = 2166136261; // FNV-1a over "day|level": stable for the day, spread across the pool
  for (const ch of `${day}|${levelId || ''}`) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return pool[h % pool.length];
}

async function onMessage(m) {
  const cmd = (m.text || '').split(/[\s@]/)[0];
  const ru = RU(m.from), chat = m.chat.id;
  const user = await remember(m.from, m.chat);
  if (cmd === '/start') return welcome(chat, ru);
  if (cmd === '/exam') return send(chat, T.exam(ru), kb(open(T.examBtn(ru), 'exam')));
  if (cmd === '/progress') return send(chat, T.progress(ru), kb(open(T.progressBtn(ru), 'progress')));
  if (cmd === '/settings') return user
    ? send(chat, T.settingsDaily(ru) + T.settings(ru), kb(dailySwitch(user.daily_question, ru), open(T.settingsBtn(ru), 'profile')))
    : send(chat, T.settings(ru), kb(open(T.settingsBtn(ru), 'profile')));
  if (cmd === '/daily') return sendQuestion(chat, daily[Math.floor(Math.random() * daily.length)], await prefersRu(m.from));
}

// Flips the user's switch and redraws the button in place, leaving the message's other buttons as they are.
async function onSwitch(c, on, ru) {
  if (!hasDb || !(await remember(c.from, c.message.chat))) return api('answerCallbackQuery', { callback_query_id: c.id });
  await setDaily(c.from.id, on);
  await api('answerCallbackQuery', { callback_query_id: c.id, text: on ? T.turnedOn(ru) : T.turnedOff(ru) });
  const rows = (c.message.reply_markup?.inline_keyboard || []).map((r) => (r.some((b) => b.callback_data?.startsWith('dq:')) ? dailySwitch(on, ru) : r));
  await api('editMessageReplyMarkup', { chat_id: c.message.chat.id, message_id: c.message.message_id, reply_markup: { inline_keyboard: rows } });
}

async function onCallback(c) {
  const [kind, id, pick, lang] = (c.data || '').split(':');
  if (kind === 'dq' && c.message) return onSwitch(c, id === '1', tagRu(pick, c.from));
  if (kind !== 'd' || !byId[id] || !c.message) return api('answerCallbackQuery', { callback_query_id: c.id });
  const isRu = tagRu(lang, c.from), q = local(byId[id].q, isRu), ok = +pick === q.answer;
  // The scheduled question carries the switch; keep it (with the current state) after the answer.
  const hadSwitch = (c.message.reply_markup?.inline_keyboard || []).some((r) => r.some((b) => b.callback_data?.startsWith('dq:')));
  const [, user] = await Promise.all([
    api('answerCallbackQuery', { callback_query_id: c.id, text: ok ? (isRu ? 'Верно ✓' : 'Correct ✓') : (isRu ? 'Неверно' : 'Not quite') }),
    remember(c.from, c.message.chat),
  ]);
  const text = answered(q, isRu, +pick);
  const reply_markup = kb(theoryButton(byId[id].q, isRu), open(T.practise(isRu), q.link), hadSwitch && user && dailySwitch(user.daily_question, isRu));
  const where = { chat_id: c.message.chat.id, message_id: c.message.message_id, parse_mode: 'HTML', reply_markup };
  // a question sent with its photo keeps it; the text goes in the caption (older text-only questions: the text)
  await (c.message.photo ? api('editMessageCaption', { ...where, caption: text }) : api('editMessageText', { ...where, text }));
}

// The update types the bot asks Telegram for (getUpdates and setWebhook).
export const ALLOWED_UPDATES = ['message', 'callback_query'];

export async function handleUpdate(u) {
  if (u.message) return onMessage(u.message);
  if (u.callback_query) return onCallback(u.callback_query);
}
