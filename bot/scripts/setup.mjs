// Sets @iyt_test_bot's public profile: name, description, about text and commands (English by default, Russian
// for Russian-language clients), the menu button, and, with --photo, the profile picture.
//
//   node --env-file=.env.local bot/scripts/setup.mjs            # texts, commands, menu button
//   node --env-file=.env.local bot/scripts/setup.mjs --photo    # also upload bot/assets/avatar.png
//   node --env-file=.env.local bot/scripts/setup.mjs --check    # only print what the bot currently has
//
// Needs TELEGRAM_BOT_TOKEN in .env.local (from @BotFather). WEBAPP_URL is optional: when set, the menu button
// opens the mini app; until then the menu shows the commands.
//
// The Main Mini App (the "Open" button on the bot's profile, t.me/<bot>?startapp links, the app catalogue) has no
// Bot API method: it is switched on in @BotFather. The script reports whether it is on and prints the steps if not.
//
// The picture above the description ("What can this bot do?", seen before the first Start) has no Bot API method
// either: it is bot/assets/description.jpg (640×360), set once in @BotFather; the script prints the steps.

import { readFile } from 'node:fs/promises';

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) { console.error('TELEGRAM_BOT_TOKEN is not set (put it in .env.local)'); process.exit(1); }
const webapp = process.env.WEBAPP_URL || '';
const api = (m) => `https://api.telegram.org/bot${token}/${m}`;

async function call(method, params = {}) {
  const res = await fetch(api(method), { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(params) });
  const data = await res.json();
  if (!data.ok) throw new Error(`${method}: ${data.description}`);
  return data.result;
}

const LIMITS = { name: 64, description: 512, short_description: 120 };

const TEXTS = {
  en: {
    name: 'IYT Test — exam practice',
    description: `⚓️ Practice questions for IYT certification levels — VHF Radio Operator, International Crew, Flotilla Skipper, Bareboat Skipper and Yachtmaster Coastal, Offshore and Ocean.

Real situations, drawn: the mark ahead, the lights at night, the other boat's bearing, the engine panel. Four options, a one-line note naming the rule.

📚 Practise by topic · ⏱ Timed mock exam · 🔁 Mistakes come back until you get them right · 🔥 A question a day in this chat

Tap Start to pick your level.`,
    short_description: 'Practice questions for IYT levels: drawn situations, mock exam, daily question. From VHF to Yachtmaster Ocean.',
    commands: [
      { command: 'start', description: 'Pick a level and practise' },
      { command: 'exam', description: 'Start a mock exam' },
      { command: 'daily', description: 'Question of the day' },
      { command: 'progress', description: 'My progress' },
      { command: 'settings', description: 'Language, reminders' },
    ],
  },
  ru: {
    name: 'IYT Test — подготовка к экзамену',
    description: `⚓️ Вопросы для подготовки к экзаменам IYT — VHF Radio Operator, International Crew, Flotilla Skipper, Bareboat Skipper и Yachtmaster Coastal, Offshore и Ocean.

Реальные ситуации, в картинках: знак по курсу, огни ночью, пеленг на другую яхту, приборы двигателя. Четыре варианта и одна строка с правилом.

📚 Тренировка по темам · ⏱ Пробный экзамен на время · 🔁 Ошибки возвращаются, пока не ответите верно · 🔥 Вопрос дня прямо в чате

Нажмите «Старт» и выберите уровень.`,
    short_description: 'Вопросы для подготовки к IYT: ситуации в картинках, пробный экзамен, вопрос дня. От VHF до Yachtmaster Ocean.',
    commands: [
      { command: 'start', description: 'Выбрать уровень и тренироваться' },
      { command: 'exam', description: 'Пробный экзамен' },
      { command: 'daily', description: 'Вопрос дня' },
      { command: 'progress', description: 'Мой прогресс' },
      { command: 'settings', description: 'Язык, напоминания' },
    ],
  },
};
// English is the default for every client; the Russian texts go to the Telegram languages the bot and the mini app
// answer in Russian (bot/core.mjs RU): ru, uk, be, kk.
const LANGS = [['en', undefined], ...['ru', 'uk', 'be', 'kk'].map((code) => ['ru', code])];

const me = await call('getMe');
console.log(`@${me.username} (${me.id})`);
const mainApp = () => {
  if (me.has_main_web_app) return console.log(`main mini app: on — t.me/${me.username}?startapp`);
  console.log(`main mini app: off. To turn it on: @BotFather → /mybots → @${me.username} → Bot Settings →
  Configure Mini App → Enable Mini App, and send ${webapp || 'the app URL (WEBAPP_URL)'}`);
};

if (process.argv.includes('--check')) {
  for (const [l, code] of LANGS) {
    const p = code ? { language_code: code } : {};
    console.log(`\n[${code || l}]`, (await call('getMyName', p)).name);
    console.log((await call('getMyShortDescription', p)).short_description);
    console.log((await call('getMyCommands', p)).map((c) => `/${c.command} — ${c.description}`).join('\n'));
  }
  console.log('\nmenu:', JSON.stringify(await call('getChatMenuButton')));
  mainApp();
  process.exit(0);
}

for (const [l, code] of LANGS) {
  const t = TEXTS[l];
  for (const k of Object.keys(LIMITS)) if (t[k].length > LIMITS[k]) throw new Error(`${l}.${k} is ${t[k].length} chars, limit ${LIMITS[k]}`);
  const p = code ? { language_code: code } : {};
  await call('setMyName', { name: t.name, ...p });
  await call('setMyDescription', { description: t.description, ...p });
  await call('setMyShortDescription', { short_description: t.short_description, ...p });
  await call('setMyCommands', { commands: t.commands, ...p });
  console.log(`[${code || l}] name, descriptions, ${t.commands.length} commands`);
}

if (webapp) {
  await call('setChatMenuButton', { menu_button: { type: 'web_app', text: 'Open', web_app: { url: webapp } } });
  console.log('menu button → mini app', webapp);
} else {
  await call('setChatMenuButton', { menu_button: { type: 'commands' } });
  console.log('menu button → commands (set WEBAPP_URL to point it at the mini app)');
}

if (process.argv.includes('--photo')) {
  const photo = await readFile(new URL('../assets/avatar.png', import.meta.url));
  const form = new FormData();
  form.append('photo', JSON.stringify({ type: 'static', photo: 'attach://avatar' }));
  form.append('avatar', new Blob([photo], { type: 'image/png' }), 'avatar.png');
  const res = await fetch(api('setMyProfilePhoto'), { method: 'POST', body: form });
  const data = await res.json();
  if (!data.ok) throw new Error(`setMyProfilePhoto: ${data.description}`);
  console.log('profile photo uploaded');
}
mainApp();
console.log(`description picture: @BotFather → /mybots → @${me.username} → Edit Bot → Edit Description Picture,
  and send bot/assets/description.jpg (640×360)`);
console.log('done');
