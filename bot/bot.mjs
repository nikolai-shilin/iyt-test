// @iyt_test_bot — answers the commands registered by bot/scripts/setup.mjs and opens the mini app.
// Long polling, no dependencies, no database: run it on any machine that stays on.
//
//   npm run bot        # = node --env-file=.env.local bot/bot.mjs
//
// /start, /exam, /progress, /settings reply with a button into the mini app (WEBAPP_URL, opened at the right
// screen via ?screen=…). /daily sends one text question with A–D buttons; the answer and the one-line note come
// back in the same message (design C3). Questions with a figure are skipped here — figures are drawn in the app.

import { readFile } from 'node:fs/promises';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) { console.error('TELEGRAM_BOT_TOKEN is not set (put it in .env.local)'); process.exit(1); }
const webapp = (process.env.WEBAPP_URL || '').replace(/\/$/, '');
if (!webapp) console.warn('WEBAPP_URL is not set: replies will have no "Open" buttons');

const bank = JSON.parse(await readFile(new URL('../data/questions/bareboat-skipper.json', import.meta.url), 'utf8'));
const byId = Object.fromEntries(bank.questions.map((q) => [q.id, q]));
const topic = Object.fromEntries(bank.topics.map((t) => [t.id, t.title]));
const daily = bank.questions.filter((q) => !q.figure);

const api = async (method, params = {}) => {
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
    ? '⚓️ <b>IYT Test</b> — вопросы для подготовки к экзаменам IYT. Сейчас доступен <b>Bareboat Skipper</b>: 100 ситуаций в 10 темах, пробный экзамен на 40 вопросов.\n\nНажмите «Открыть», чтобы начать.'
    : '⚓️ <b>IYT Test</b> — practice questions for IYT certification levels. <b>Bareboat Skipper</b> is ready: 100 situations over 10 topics and a 40-question mock exam.\n\nTap Open to start.',
  open: (ru) => (ru ? 'Открыть' : 'Open'),
  exam: (ru) => (ru ? '⏱ Пробный экзамен: 40 вопросов, 60 минут, 70 % для сдачи.' : '⏱ Mock exam: 40 questions, 60 minutes, 70 % to pass.'),
  examBtn: (ru) => (ru ? 'Начать экзамен' : 'Start the exam'),
  progress: (ru) => (ru ? '📊 Прогресс по темам, ошибки и серия дней — в приложении.' : '📊 Your mastery by topic, mistakes and streak are in the app.'),
  progressBtn: (ru) => (ru ? 'Мой прогресс' : 'My progress'),
  settings: (ru) => (ru ? '⚙️ Тема, перемешивание вариантов и сброс прогресса — в профиле.' : '⚙️ Theme, option shuffling and progress reset are in your profile.'),
  settingsBtn: (ru) => (ru ? 'Настройки' : 'Settings'),
  practise: (ru) => (ru ? 'Тренироваться' : 'Practise more'),
};

function dailyMessage(q) {
  const text = `<b>Question of the day</b> · ${esc(topic[q.topic])}\n\n${esc(q.q)}\n\n` + q.options.map((o, i) => `<b>${'ABCD'[i]}</b>  ${esc(o)}`).join('\n');
  return { text, reply_markup: kb(q.options.map((_, i) => ({ text: 'ABCD'[i], callback_data: `d:${q.id}:${i}` }))) };
}

async function onMessage(m) {
  const cmd = (m.text || '').split(/[\s@]/)[0];
  const ru = RU(m.from), chat = m.chat.id;
  if (cmd === '/start') return send(chat, T.start(ru), kb(open(T.open(ru)), open(T.examBtn(ru), 'exam')));
  if (cmd === '/exam') return send(chat, T.exam(ru), kb(open(T.examBtn(ru), 'exam')));
  if (cmd === '/progress') return send(chat, T.progress(ru), kb(open(T.progressBtn(ru), 'progress')));
  if (cmd === '/settings') return send(chat, T.settings(ru), kb(open(T.settingsBtn(ru), 'profile')));
  if (cmd === '/daily') { const d = dailyMessage(daily[Math.floor(Math.random() * daily.length)]); return send(chat, d.text, d.reply_markup); }
}

async function onCallback(c) {
  const [kind, id, pick] = (c.data || '').split(':');
  const q = byId[id];
  if (kind !== 'd' || !q || !c.message) return api('answerCallbackQuery', { callback_query_id: c.id });
  const ok = +pick === q.answer, ru = RU(c.from);
  await api('answerCallbackQuery', { callback_query_id: c.id, text: ok ? 'Correct ✓' : 'Not quite' });
  const text = `<b>Question of the day</b> · ${esc(topic[q.topic])}\n\n${esc(q.q)}\n\n` +
    q.options.map((o, i) => `${i === q.answer ? '✅' : i === +pick ? '❌' : '▫️'}  ${esc(o)}`).join('\n') +
    `\n\n<b>${ok ? 'Correct.' : 'Not quite.'}</b> ${esc(q.why)}\n<i>${esc(q.ref)}</i>`;
  await api('editMessageText', { chat_id: c.message.chat.id, message_id: c.message.message_id, text, parse_mode: 'HTML', reply_markup: kb(open(T.practise(ru), 'practice')) });
}

const me = await api('getMe');
const hook = await api('getWebhookInfo');
if (hook.url) { console.error(`A webhook is set (${hook.url}); long polling will not receive updates. Remove it with deleteWebhook first.`); process.exit(1); }
console.log(`@${me.username} polling…`);

let offset = 0;
for (;;) {
  try {
    const updates = await api('getUpdates', { offset, timeout: 30, allowed_updates: ['message', 'callback_query'] });
    for (const u of updates) {
      offset = u.update_id + 1;
      try {
        if (u.message) await onMessage(u.message);
        else if (u.callback_query) await onCallback(u.callback_query);
      } catch (e) { console.error('update', u.update_id, e.message); }
    }
  } catch (e) {
    console.error(e.message);
    await new Promise((r) => setTimeout(r, 3000));
  }
}
