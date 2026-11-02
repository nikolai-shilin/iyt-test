// @iyt_test_bot's replies, shared by the two ways the bot runs:
//   api/telegram.mjs   Vercel function — Telegram posts each update to it (webhook, always on)
//   bot/bot.mjs        long polling from any machine (local testing; needs the webhook removed)
//
// /start, /exam, /progress, /settings reply with a button into the mini app (WEBAPP_URL, opened at the right
// screen via ?screen=…). /daily sends one text question with A–D buttons; the answer and the one-line note come
// back in the same message (design C3). Questions with a figure are skipped here — figures are drawn in the app.
// Every private message is saved to Supabase users; /settings and the scheduled question (bot/daily.mjs) carry the
// user's on/off switch for the question of the day.

import { readFile } from 'node:fs/promises';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) throw new Error('TELEGRAM_BOT_TOKEN is not set');
export const webapp = (process.env.WEBAPP_URL || '').replace(/\/$/, '');

// The levels with a bank, in IYT order; `link` is the mini app deep link that opens the level (miniapp/app.js LEVELS).
const LEVELS = [['vhf-radio-operator', 'vhf'], ['international-crew', 'crew'], ['flotilla-skipper', 'flotilla'], ['bareboat-skipper', 'bareboat']];
// A bank comes from Supabase — bank() / bank_overlay() return the same shape as the files (docs/data-model.md) —
// or, when the database is not configured or does not answer, from data/questions/<name>.json bundled with the function.
async function read(name) {
  const [level, lang] = name.split('.');
  const url = (process.env.SUPABASE_URL || '').replace(/\/$/, ''), key = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_PUBLISHABLE_KEY || '';
  if (url && key) try {
    const fn = lang ? `bank_overlay?p_level=${level}&p_lang=${lang}` : `bank?p_level=${level}`;
    const res = await fetch(`${url}/rest/v1/rpc/${fn}`, { headers: { apikey: key, ...(key.startsWith('eyJ') && { authorization: `Bearer ${key}` }) }, signal: AbortSignal.timeout(8000) });
    const b = res.ok ? await res.json() : null;
    if (b) return b;
  } catch (e) { console.warn(`bank ${name} from Supabase failed, using the file:`, e.message); }
  return JSON.parse(await readFile(new URL(`../data/questions/${name}.json`, import.meta.url), 'utf8'));
}
// Each bank with its Russian overlay (data/i18n.py): translated questions and topic titles; anything missing stays English.
// A level with no bank in the database or in the files yet is left out.
const banks = (await Promise.all(LEVELS.map(async ([id, link]) => {
  const bank = await read(id).catch(() => null);
  return bank && { id, link, bank, ru: await read(`${id}.ru`).catch(() => ({})) };
}))).filter(Boolean);
const byId = {};
for (const b of banks) for (const q of b.bank.questions) byId[q.id] = { q, b };
const daily = Object.values(byId).filter(({ q }) => !q.figure).map(({ q }) => q);
const N = Object.keys(byId).length;
const names = banks.map((b) => b.bank.title.replace(/^IYT /, ''));
// The question, its topic title and level in the reader's language.
function local(q, isRu) {
  const { b } = byId[q.id], RU_BANK = (isRu && b.ru) || {};
  const title = (RU_BANK.topics && RU_BANK.topics[q.topic]) || b.bank.topics.find((t) => t.id === q.topic).title;
  const tr = RU_BANK.questions && RU_BANK.questions[q.id];
  const lv = b.bank.title.replace(/^IYT /, '');
  return tr && tr.q && tr.options?.length === 4 ? { ...q, ...tr, title, lv, link: b.link } : { ...q, title, lv, link: b.link };
}

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

// The reply language follows the sender's Telegram app language (language_code on every update), with the same rule
// as the mini app (miniapp/app.js pickLang): Russian for ru, uk, be and kk, English for everyone else.
const RU = (from) => /^(ru|uk|be|kk)\b/i.test(from?.language_code || '');
const T = {
  start: (ru) => ru
    ? `⚓️ <b>IYT Test</b> — вопросы для подготовки к экзаменам IYT. Уже доступны: <b>${names.join('</b>, <b>')}</b> — ${N} ситуаций, тренировка по темам и пробный экзамен.\n\nНажмите «Открыть» и выберите уровень.`
    : `⚓️ <b>IYT Test</b> — practice questions for IYT certification levels. Ready now: <b>${names.join('</b>, <b>')}</b> — ${N} situations, practice by topic and a mock exam.\n\nTap Open and pick your level.`,
  open: (ru) => (ru ? 'Открыть' : 'Open'),
  exam: (ru) => (ru ? '⏱ Пробный экзамен по вашему уровню: случайные вопросы из всех тем, таймер, ответы в конце, 70 % для сдачи.' : '⏱ Mock exam for your level: random questions from every topic, a timer, answers at the end, 70 % to pass.'),
  examBtn: (ru) => (ru ? 'Начать экзамен' : 'Start the exam'),
  progress: (ru) => (ru ? '📊 Прогресс по темам, ошибки и серия дней — в приложении.' : '📊 Your mastery by topic, mistakes and streak are in the app.'),
  progressBtn: (ru) => (ru ? 'Мой прогресс' : 'My progress'),
  settings: (ru) => (ru ? '⚙️ Тема, перемешивание вариантов и сброс прогресса — в профиле.' : '⚙️ Theme, option shuffling and progress reset are in your profile.'),
  settingsDaily: (ru) => (ru
    ? '🔔 <b>Вопрос дня</b>: каждое утро один вопрос в этом чате, ответ одной кнопкой. Кнопка ниже включает и выключает его.\n\n'
    : '🔔 <b>Question of the day</b>: one question in this chat every morning, answered with one tap. The button below turns it on or off.\n\n'),
  dailyOn: (ru) => (ru ? '🔔 Вопрос дня: включён' : '🔔 Question of the day: on'),
  dailyOff: (ru) => (ru ? '🔕 Вопрос дня: выключен' : '🔕 Question of the day: off'),
  turnedOn: (ru) => (ru ? 'Вопрос дня включён — до завтра!' : 'Question of the day is on — see you tomorrow!'),
  turnedOff: (ru) => (ru ? 'Вопрос дня выключен. Включить снова — /settings' : 'Question of the day is off. Turn it back on in /settings'),
  settingsBtn: (ru) => (ru ? 'Настройки' : 'Settings'),
  practise: (ru) => (ru ? 'Тренироваться' : 'Practise more'),
};

const head = (isRu) => (isRu ? 'Вопрос дня' : 'Question of the day');
// The on/off switch: one button whose label says the current state; tapping it flips it (callback dq:1 / dq:0).
const dailySwitch = (on, ru) => [{ text: on ? T.dailyOn(ru) : T.dailyOff(ru), callback_data: `dq:${on ? 0 : 1}` }];
// One question with A–D buttons. `switchOn` (true/false) adds the on/off switch under them — the scheduled send does.
export function dailyMessage(src, isRu, switchOn) {
  const q = local(src, isRu);
  const text = `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` + q.options.map((o, i) => `<b>${'ABCD'[i]}</b>  ${esc(o)}`).join('\n');
  return { text, reply_markup: kb(q.options.map((_, i) => ({ text: 'ABCD'[i], callback_data: `d:${q.id}:${i}` })), switchOn != null && dailySwitch(switchOn, isRu)) };
}

// Question of the day: the same question for everyone on a UTC day (per level once users have one), text-only.
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
  if (cmd === '/start') return send(chat, T.start(ru), kb(open(T.open(ru)), open(T.examBtn(ru), 'exam')));
  if (cmd === '/exam') return send(chat, T.exam(ru), kb(open(T.examBtn(ru), 'exam')));
  if (cmd === '/progress') return send(chat, T.progress(ru), kb(open(T.progressBtn(ru), 'progress')));
  if (cmd === '/settings') return user
    ? send(chat, T.settingsDaily(ru) + T.settings(ru), kb(dailySwitch(user.daily_question, ru), open(T.settingsBtn(ru), 'profile')))
    : send(chat, T.settings(ru), kb(open(T.settingsBtn(ru), 'profile')));
  if (cmd === '/daily') { const d = dailyMessage(daily[Math.floor(Math.random() * daily.length)], ru); return send(chat, d.text, d.reply_markup); }
}

// Flips the user's switch and redraws the button in place, leaving the message's other buttons as they are.
async function onSwitch(c, on) {
  const ru = RU(c.from);
  if (!hasDb || !(await remember(c.from, c.message.chat))) return api('answerCallbackQuery', { callback_query_id: c.id });
  await setDaily(c.from.id, on);
  await api('answerCallbackQuery', { callback_query_id: c.id, text: on ? T.turnedOn(ru) : T.turnedOff(ru) });
  const rows = (c.message.reply_markup?.inline_keyboard || []).map((r) => (r.some((b) => b.callback_data?.startsWith('dq:')) ? dailySwitch(on, ru) : r));
  await api('editMessageReplyMarkup', { chat_id: c.message.chat.id, message_id: c.message.message_id, reply_markup: { inline_keyboard: rows } });
}

async function onCallback(c) {
  const [kind, id, pick] = (c.data || '').split(':');
  if (kind === 'dq' && c.message) return onSwitch(c, id === '1');
  if (kind !== 'd' || !byId[id] || !c.message) return api('answerCallbackQuery', { callback_query_id: c.id });
  const isRu = RU(c.from), q = local(byId[id].q, isRu), ok = +pick === q.answer;
  // The scheduled question carries the switch; keep it (with the current state) after the answer.
  const hadSwitch = (c.message.reply_markup?.inline_keyboard || []).some((r) => r.some((b) => b.callback_data?.startsWith('dq:')));
  const [, user] = await Promise.all([
    api('answerCallbackQuery', { callback_query_id: c.id, text: ok ? (isRu ? 'Верно ✓' : 'Correct ✓') : (isRu ? 'Неверно' : 'Not quite') }),
    remember(c.from, c.message.chat),
  ]);
  const text = `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` +
    q.options.map((o, i) => `${i === q.answer ? '✅' : i === +pick ? '❌' : '▫️'}  ${esc(o)}`).join('\n') +
    `\n\n<b>${ok ? (isRu ? 'Верно.' : 'Correct.') : (isRu ? 'Неверно.' : 'Not quite.')}</b> ${esc(q.why)}\n<i>${esc(q.ref)}</i>`;
  await api('editMessageText', { chat_id: c.message.chat.id, message_id: c.message.message_id, text, parse_mode: 'HTML',
    reply_markup: kb(open(T.practise(isRu), q.link), hadSwitch && user && dailySwitch(user.daily_question, isRu)) });
}

// The update types the bot asks Telegram for (getUpdates and setWebhook).
export const ALLOWED_UPDATES = ['message', 'callback_query'];

export async function handleUpdate(u) {
  if (u.message) return onMessage(u.message);
  if (u.callback_query) return onCallback(u.callback_query);
}
