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

const bank = JSON.parse(await readFile(new URL('../data/questions/bareboat-skipper.json', import.meta.url), 'utf8'));
// Russian overlay (data/i18n.py): translated questions and topic titles; anything missing stays English.
const RU_BANK = await readFile(new URL('../data/questions/bareboat-skipper.ru.json', import.meta.url), 'utf8').then(JSON.parse).catch(() => ({}));
const byId = Object.fromEntries(bank.questions.map((q) => [q.id, q]));
const daily = bank.questions.filter((q) => !q.figure);
const N = bank.questions.length, NT = bank.topics.length;
// The question and its topic title in the reader's language.
function local(q, isRu) {
  const tr = isRu && RU_BANK.questions && RU_BANK.questions[q.id];
  const title = (isRu && RU_BANK.topics && RU_BANK.topics[q.topic]) || bank.topics.find((t) => t.id === q.topic).title;
  return tr && tr.q && tr.options?.length === 4 ? { ...q, ...tr, title } : { ...q, title };
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
    ? `⚓️ <b>IYT Test</b> — вопросы для подготовки к экзаменам IYT. Сейчас доступен <b>Bareboat Skipper</b>: ${N} ситуаций в ${NT} темах, пробный экзамен на ${bank.examQuestions} вопросов.\n\nНажмите «Открыть», чтобы начать.`
    : `⚓️ <b>IYT Test</b> — practice questions for IYT certification levels. <b>Bareboat Skipper</b> is ready: ${N} situations over ${NT} topics and a ${bank.examQuestions}-question mock exam.\n\nTap Open to start.`,
  open: (ru) => (ru ? 'Открыть' : 'Open'),
  exam: (ru) => (ru ? '⏱ Пробный экзамен: 40 вопросов, 60 минут, 70 % для сдачи.' : '⏱ Mock exam: 40 questions, 60 minutes, 70 % to pass.'),
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
  const text = `<b>${head(isRu)}</b> · ${esc(q.title)}\n\n${esc(q.q)}\n\n` + q.options.map((o, i) => `<b>${'ABCD'[i]}</b>  ${esc(o)}`).join('\n');
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
  const isRu = RU(c.from), q = local(byId[id], isRu), ok = +pick === q.answer;
  await api('answerCallbackQuery', { callback_query_id: c.id, text: ok ? (isRu ? 'Верно ✓' : 'Correct ✓') : (isRu ? 'Неверно' : 'Not quite') });
  const text = `<b>${head(isRu)}</b> · ${esc(q.title)}\n\n${esc(q.q)}\n\n` +
    q.options.map((o, i) => `${i === q.answer ? '✅' : i === +pick ? '❌' : '▫️'}  ${esc(o)}`).join('\n') +
    `\n\n<b>${ok ? (isRu ? 'Верно.' : 'Correct.') : (isRu ? 'Неверно.' : 'Not quite.')}</b> ${esc(q.why)}\n<i>${esc(q.ref)}</i>`;
  await api('editMessageText', { chat_id: c.message.chat.id, message_id: c.message.message_id, text, parse_mode: 'HTML', reply_markup: kb(open(T.practise(isRu), 'practice')) });
}

// The update types the bot asks Telegram for (getUpdates and setWebhook).
export const ALLOWED_UPDATES = ['message', 'callback_query'];

export async function handleUpdate(u) {
  if (u.message) return onMessage(u.message);
  if (u.callback_query) return onCallback(u.callback_query);
}
