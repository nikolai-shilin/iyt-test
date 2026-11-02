// @iyt_test_bot's replies, shared by the two ways the bot runs:
//   api/telegram.mjs   Vercel function — Telegram posts each update to it (webhook, always on)
//   bot/bot.mjs        long polling from any machine (local testing; needs the webhook removed)
//
// /start, /exam, /progress, /settings reply with a button into the mini app (WEBAPP_URL, opened at the right
// screen via ?screen=…). /daily sends one text question with A–D buttons; the answer and the one-line note come
// back in the same message (design C3). Questions with a figure are skipped here — figures are drawn in the app.

import { readFile } from 'node:fs/promises';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) throw new Error('TELEGRAM_BOT_TOKEN is not set');
export const webapp = (process.env.WEBAPP_URL || '').replace(/\/$/, '');

// The levels with a bank, in IYT order; `link` is the mini app deep link that opens the level (miniapp/app.js LEVELS).
const LEVELS = [['vhf-radio-operator', 'vhf'], ['international-crew', 'crew'], ['flotilla-skipper', 'flotilla'], ['bareboat-skipper', 'bareboat']];
const read = (name) => readFile(new URL(`../data/questions/${name}.json`, import.meta.url), 'utf8').then(JSON.parse);
// Each bank with its Russian overlay (data/i18n.py): translated questions and topic titles; anything missing stays English.
const banks = await Promise.all(LEVELS.map(async ([id, link]) => ({ id, link, bank: await read(id), ru: await read(`${id}.ru`).catch(() => ({})) })));
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
  if (!data.ok) throw new Error(`${method}: ${data.description}`);
  return data.result;
};
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const open = (text, screen) => (webapp ? [{ text, web_app: { url: screen ? `${webapp}/?screen=${screen}` : `${webapp}/` } }] : null);
const kb = (...rows) => ({ inline_keyboard: rows.filter(Boolean) });
const send = (chat_id, text, reply_markup) => api('sendMessage', { chat_id, text, parse_mode: 'HTML', reply_markup, link_preview_options: { is_disabled: true } });

const RU = (from) => (from?.language_code || '').startsWith('ru');
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
  settingsBtn: (ru) => (ru ? 'Настройки' : 'Settings'),
  practise: (ru) => (ru ? 'Тренироваться' : 'Practise more'),
};

const head = (isRu) => (isRu ? 'Вопрос дня' : 'Question of the day');
function dailyMessage(src, isRu) {
  const q = local(src, isRu);
  const text = `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` + q.options.map((o, i) => `<b>${'ABCD'[i]}</b>  ${esc(o)}`).join('\n');
  return { text, reply_markup: kb(q.options.map((_, i) => ({ text: 'ABCD'[i], callback_data: `d:${q.id}:${i}` }))) };
}

async function onMessage(m) {
  const cmd = (m.text || '').split(/[\s@]/)[0];
  const ru = RU(m.from), chat = m.chat.id;
  if (cmd === '/start') return send(chat, T.start(ru), kb(open(T.open(ru)), open(T.examBtn(ru), 'exam')));
  if (cmd === '/exam') return send(chat, T.exam(ru), kb(open(T.examBtn(ru), 'exam')));
  if (cmd === '/progress') return send(chat, T.progress(ru), kb(open(T.progressBtn(ru), 'progress')));
  if (cmd === '/settings') return send(chat, T.settings(ru), kb(open(T.settingsBtn(ru), 'profile')));
  if (cmd === '/daily') { const d = dailyMessage(daily[Math.floor(Math.random() * daily.length)], ru); return send(chat, d.text, d.reply_markup); }
}

async function onCallback(c) {
  const [kind, id, pick] = (c.data || '').split(':');
  if (kind !== 'd' || !byId[id] || !c.message) return api('answerCallbackQuery', { callback_query_id: c.id });
  const isRu = RU(c.from), q = local(byId[id].q, isRu), ok = +pick === q.answer;
  await api('answerCallbackQuery', { callback_query_id: c.id, text: ok ? (isRu ? 'Верно ✓' : 'Correct ✓') : (isRu ? 'Неверно' : 'Not quite') });
  const text = `<b>${head(isRu)}</b> · ${esc(q.lv)} · ${esc(q.title)}\n\n${esc(q.q)}\n\n` +
    q.options.map((o, i) => `${i === q.answer ? '✅' : i === +pick ? '❌' : '▫️'}  ${esc(o)}`).join('\n') +
    `\n\n<b>${ok ? (isRu ? 'Верно.' : 'Correct.') : (isRu ? 'Неверно.' : 'Not quite.')}</b> ${esc(q.why)}\n<i>${esc(q.ref)}</i>`;
  await api('editMessageText', { chat_id: c.message.chat.id, message_id: c.message.message_id, text, parse_mode: 'HTML', reply_markup: kb(open(T.practise(isRu), q.link)) });
}

// The update types the bot asks Telegram for (getUpdates and setWebhook).
export const ALLOWED_UPDATES = ['message', 'callback_query'];

export async function handleUpdate(u) {
  if (u.message) return onMessage(u.message);
  if (u.callback_query) return onCallback(u.callback_query);
}
