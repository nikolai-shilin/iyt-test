// The site around the app: a plain HTML page for every level and every theory article, in English and Russian, for
// search engines and AI assistants (most of them read a page without running its JavaScript) and for the readers
// they send. Everything on them is already served to the app; nothing here is written by hand except the strings.
//
//   /<level>                 the level: its mock exam, its topics with their articles, a way into the app
//   /<level>/<topic>         a topic's article with its drawings, then sample questions with their answers
//   /about                   what IYT Test is and is not
//   /privacy                 what the site, the app, the bot and the MCP server keep about you
//   /mcp                     the MCP server for AI assistants: its address, how to connect it, what it can do
//   /ru, /ru/<level>, …      the same in Russian; /ru lists the levels (in English the app's own / does)
//
// and next to them sitemap.xml (each page with its other language), llms.txt (the map for AI assistants), 404.html
// and pages.json (each address with a hash of its page: indexnow.mjs announces only the pages that changed).
// build.mjs calls buildPages() once the app is in miniapp/dist, with the hashed names of the stylesheets.

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SITE, BOT, PAUSED } from './site.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const readJson = async (p) => {
  try { return JSON.parse(await readFile(join(root, p), 'utf8')); } catch (e) { if (e.code === 'ENOENT') return null; throw new Error(`${p}: ${e.message}`); }
};
const hash = (s) => createHash('sha256').update(s).digest('hex').slice(0, 10);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// **bold** is the only markup of an article's text (docs/theory.md)
const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
// and [text](https://… or /…) links and `code`, in the strings of the privacy and MCP pages
const rich = (s) => inline(s).replace(/\[([^\]]+)\]\((https:\/\/[^)\s]+|\/[^)\s]*)\)/g, '<a href="$2">$1</a>').replace(/`([^`]+)`/g, '<code>$1</code>');
const plain = (s) => String(s ?? '').replace(/\*\*(.+?)\*\*/g, '$1').replace(/\s+/g, ' ').trim();
// a description of at most n characters, cut at a word
const clip = (s, n = 158) => { s = plain(s); if (s.length <= n) return s; const c = s.slice(0, n - 1); return `${c.slice(0, c.lastIndexOf(' ')).replace(/[,;:·—-]$/, '')}…`; };
// the first sentence of a lead (a topic row on a level page), or a cut one when that is long
const first = (s) => { const m = plain(s).match(/^.+?[.!?](?=\s|$)/); return m && m[0].length <= 170 ? m[0] : clip(s, 150); };
const ABCD = 'ABCD';

// The levels in the app's order; `link` is the app's deep link to the level (?screen=, startapp=), as in bot/core.mjs.
const LEVELS = [['vhf-radio-operator', 'vhf'], ['international-crew', 'crew'], ['flotilla-skipper', 'flotilla'], ['bareboat-skipper', 'bareboat'], ['yachtmaster-coastal', 'coastal'], ['yachtmaster-offshore', 'offshore'], ['yachtmaster-ocean', 'ocean'], ['racing-rules', 'racing'], ['charter-checkin', 'checkin']];

// What a level's certificate is, for the words of its title: the skipper and Yachtmaster levels are what people call
// a licence («права на яхту»), VHF and Crew are IYT certificates, the racing rules and the charter check-in neither.
const KIND = { 'flotilla-skipper': 'licence', 'bareboat-skipper': 'licence', 'yachtmaster-coastal': 'licence', 'yachtmaster-offshore': 'licence', 'yachtmaster-ocean': 'licence', 'vhf-radio-operator': 'iyt', 'international-crew': 'iyt' };

// figures.js is a browser script: run it here, as api/mcp.mjs and data/check_theory.mjs do.
const fig = new Function(`${await readFile(join(root, 'docs/design/figures.js'), 'utf8')}\nreturn { figSvg, FIG_TEXT, FIG_DAY };`)();
// Built-in labels of the figures in Russian: the same list as FIG_RU in miniapp/app.js.
const FIG_RU = {
  wind: 'ветер', N: 'N', You: 'Вы', Other: 'Другое судно', 'Night · lights seen ahead': 'Ночь · огни по курсу',
  'Light at night': 'Огонь ночью', 'N (true)': 'N ист.', MN: 'N магн.', Variation: 'Склонение', Deviation: 'Девиация',
  'True course': 'ИК', W: 'W', E: 'E', 'Depths in metres below chart datum': 'Глубины в метрах от нуля глубин',
  Anchoring: 'Якорная стоянка', 'Northern hemisphere': 'Северное полушарие',
  zone: 'зона', pin: 'знак', RC: 'ГК', LW: 'МВ', HW: 'ПВ', A: 'A', B: 'B', C: 'C', D: 'D',
};

const STR = {
  en: {
    levels: 'Levels', about: 'About', other: 'Русский', practise: 'Practise in the app', telegram: 'Open in Telegram',
    kicker: 'IYT theory · free', ruleK: 'Rule', figure: 'Figure',
    homeTitle: 'Pass your IYT exam',
    homeLead: 'Close-to-real questions for every certification level, with an explanation after each answer, and a theory article for every topic. Pick the level you are studying for.',
    levelTitle: (l, kind) => `${l} practice test: ${kind === 'other' ? '' : 'exam '}questions and theory`,
    levelDesc: (l, n, t, q, m, p) => `Free ${l} practice test: ${n} questions in ${t} topics with the reason after every answer, a theory article for each topic, and a timed mock exam of ${q} questions in ${m} minutes, pass at ${p} %.`,
    levelLead: (n, t) => `${n} questions in ${t} topics. Each topic has an article that explains the rules the questions ask about, with drawings; the app asks the questions, explains every answer and brings your mistakes back until you get them right.`,
    questions: 'questions', topics: 'topics', exam: 'exam questions',
    examLine: (q, m, p) => `The mock exam: ${q} questions spread over every topic, ${m} minutes, pass at ${p} %. Size, time and pass mark are the app’s defaults, not an official rule.`,
    topicsK: 'Topics', otherK: 'Other levels', min: (m) => `${m} min read`, nq: (n) => `${n} questions`, noArticle: 'article not written yet',
    articleK: (i, n, m) => `Theory · topic ${i} of ${n} · ${m} min`, contents: 'In this article',
    articleTitle: (t, l) => `${t}: theory and practice questions — ${l}`,
    qsK: 'Practice questions', qsLead: 'Questions from this topic, as the app asks them. Open one to see the answer.',
    answer: 'Show the answer', readSec: (k) => `Explained in: ${k}`,
    ctaK: 'Practise it', ctaTopic: (n) => `All ${n} questions of this topic are in the app: practice by topic with the reason after every answer, your mistakes brought back, and a timed mock exam. Free, no sign-up, in the browser or in Telegram.`,
    ctaLevel: 'Practise by topic with the reason after every answer, take a timed mock exam, and see your progress per topic. Free, no sign-up, in the browser or in Telegram.',
    prev: (i) => `‹ Topic ${i}`, next: (i) => `Topic ${i} ›`,
    foot: 'Written for study, close to the IYT syllabus. Not an IYT or World Sailing publication; the rules themselves are the authority.',
    notFound: 'This page is not here', notFoundLead: 'The address may be mistyped, or the page has moved. The levels are below, and the app is on the home page.',
    aboutTitle: 'About IYT Test',
    aboutLead: 'A free practice app for the theory of IYT sailing certificates, in English and Russian, in any browser and in Telegram.',
    aboutBody: [
      'IYT Test covers the IYT levels from VHF Radio Operator and International Crew to Yachtmaster Ocean, the Racing Rules of Sailing, and a charter check-in course. Every question is a situation you meet on the water, drawn where it can be: the mark ahead, the lights at night, the other boat’s bearing, the engine panel. Four options, and a one-line note naming the rule.',
      'Each topic of each level has a theory article that explains the rules its questions ask about, with drawings. In the app you practise by topic, your mistakes come back until you get them right, and a timed mock exam spreads its questions over every topic.',
      '**Written for study.** The questions and the articles are our own work, close to the syllabus. They are not IYT exam content, and neither IYT nor World Sailing has reviewed them. Facts follow COLREGs, IALA buoyage and standard seamanship; where practice differs by region, the article says so. The exam size, time and pass mark in the app are its own defaults.',
    ],
    aboutWho: (h) => `Made by RYC. Found a mistake? Every question and every article section has a report button in the app, or write to the author on Telegram: <a href="https://t.me/${h}">@${h}</a>.`,
    aboutMcp: (u) => `For AI assistants: the questions and the articles are also a public, read-only MCP server at <code>${u}</code>. Add it as a custom connector and practise in your own assistant.`,
    privacy: 'Privacy', privTitle: 'Privacy policy', privDate: 'Updated 5 November 2026',
    privLead: 'What IYT Test keeps about you, where, who sees it, and how to have it deleted. The short version: in a browser, nothing that says who you are; in Telegram, your Telegram name and your progress, so it follows you between devices.',
    privBody: [
      ['Who we are', 'IYT Test is made by RYC. For anything about your data, write to the author on Telegram: [@fullcrimp](https://t.me/fullcrimp).'],
      ['In a browser', 'The site and the app ask for no account. Your progress stays **on your device**, in the browser’s storage, and is not sent to us. We count page views with Vercel Web Analytics, which uses no cookies and cannot tell who you are: it sees the page, the referring site, and the country and kind of device.'],
      ['In Telegram', 'When you open the app in Telegram, Telegram gives it your **Telegram id, name, username and language**, signed so that nobody else can use them. The app keeps your progress in Telegram’s cloud storage and on our server, so it is the same on every device: the questions you answered, whether you were right, the option you picked and when, your mock exams, the questions you flagged and the notes you wrote about a question or a section of an article.',
        'The admins of IYT Test (the author) can see each student’s name, username, results, flags and notes, to fix the questions people report and see where they get stuck. They also see your Telegram profile photo, fetched from Telegram when they open the list, not stored.'],
      ['The Telegram bot', 'When you write to [@iyt_test_bot](https://t.me/iyt_test_bot), it saves your Telegram id, name, username and language, and whether the question of the day is on. It does not keep what you write to it or how you answer the question of the day. If you block the bot, it marks you as blocked and stops writing.'],
      ['The MCP server', 'The MCP server for AI assistants asks for no sign-in and stores nothing about the people or the assistants that use it. Like every request to the site, a call passes through the hosting’s logs (the IP address, the address called and the time), which Vercel keeps for a limited time to run the service.'],
      ['Who else handles it', 'Vercel hosts the site, the app and the server, and counts the page views. Supabase holds the database, in the EU (Stockholm). Telegram runs the bot, the mini app and its cloud storage. Nobody else gets your data: there are no ads, and nothing is sold.'],
      ['How long, and deleting it', 'Your data is kept while the app runs. To have it deleted, write to [@fullcrimp](https://t.me/fullcrimp) from the same Telegram account: your Telegram name, settings, progress and answers are removed from the server. What is in your browser or in Telegram’s cloud storage you can clear yourself, with Reset progress in the app’s profile.'],
      ['Changes', 'When this policy changes, this page changes, with the date at the top.'],
    ],
    mcpHow: 'How to connect it', mcpBand: 'Practise in Claude or ChatGPT', mcpBandText: 'The questions and the theory are also an MCP server: add it to your AI assistant and it quizzes you, checks your answers and explains the rule.',
    mcp: 'For AI assistants', mcpK: 'MCP server · free', mcpTitle: 'Practise in your AI assistant',
    mcpDesc: 'Connect IYT Test to Claude, ChatGPT or any assistant that speaks MCP: it quizzes you on IYT questions, checks your answers, explains the rule and runs a mock exam. Free, no sign-in.',
    mcpLead: 'The questions and the theory articles of IYT Test are also an MCP server. Add it to Claude, ChatGPT or any other assistant that speaks the Model Context Protocol, and the assistant can quiz you, check your answers, explain the rule behind each one and run a mock exam, in a conversation.',
    mcpUrlK: 'The address', mcpUrlNote: 'Public and read-only: no sign-in, no key, nothing to install.',
    mcpBody: [
      ['Connect it', '**Claude** (web, desktop and mobile): Settings → Connectors → Add custom connector, then paste the address.',
        '**ChatGPT**: turn on developer mode in the settings for apps and connectors, then create a connector with the address. It needs a plan that allows custom connectors.',
        '**Claude Code**, in a terminal:', { code: (u) => `claude mcp add --transport http iyt-test ${u}` },
        '**Cursor, VS Code and other apps** that take a JSON list of servers:', { code: (u) => JSON.stringify({ mcpServers: { 'iyt-test': { type: 'streamable-http', url: u } } }, null, 2) }],
      ['Then ask', { list: ['Quiz me on IALA buoyage for the Bareboat Skipper, five questions, one at a time.', 'Give me a Yachtmaster Coastal mock exam and grade it at the end.', 'I keep mixing up cardinal marks: explain them, then test me.', 'Ask me the question of the day in Russian.'] },
        'The assistant asks each question with its four options and keeps the answer back until you choose. Most questions come with a drawing; where the assistant cannot show it, it gets a link to the image.'],
      ['What it can do', { table: [
        ['list_levels', 'The levels, their topics, the mock-exam settings, and which topics have an article'],
        ['get_questions', 'Random questions of a level, a topic or a difficulty, without the answers'],
        ['check_answer', 'Right or wrong, the right option, the note that names the rule, and the theory section that explains it'],
        ['search_questions', 'Questions by words: “cardinal mark”, “MAYDAY”'],
        ['start_mock_exam · grade_exam', 'An exam-sized set spread over every topic; then the score, pass or fail, the mistakes and what to read'],
        ['question_of_the_day', 'The question the Telegram bot sends today'],
        ['list_theory · get_theory · search_theory', 'The theory articles and their sections, as text with links to the drawings'],
        ['explain_question', 'A question with its answer and the theory section behind it'],
        ['practice_section', 'The questions a theory section covers: read, then practise'],
        ['get_figure', 'A drawing as SVG'],
      ] }, 'Every tool answers in English or Russian. What is not translated yet comes in English.'],
      ['What it keeps', 'Nothing. The server asks for no sign-in and stores nothing about you or your assistant; your progress in the app is not connected to it. The details are in the [privacy policy](/privacy).'],
      ['Where else to find it', 'It is listed in the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.nikolai-shilin/iyt-test) as `io.github.nikolai-shilin/iyt-test`. The questions and the articles are written for study, close to the syllabus; they are not IYT exam content.'],
    ],
  },
  ru: {
    levels: 'Уровни', about: 'О проекте', other: 'English', practise: 'Тренироваться в приложении', telegram: 'Открыть в Telegram',
    kicker: 'Теория IYT · бесплатно', ruleK: 'Правило', figure: 'Рисунок',
    homeTitle: 'Сдайте экзамен IYT',
    homeLead: 'Вопросы, близкие к настоящему экзамену, для каждого уровня — с пояснением после каждого ответа и статьёй по теории для каждой темы. Выберите уровень, к которому готовитесь.',
    levelTitle: (l, kind) => `${l}: тест и теория к ${kind === 'licence' ? 'экзамену на права на яхту' : kind === 'iyt' ? 'экзамену IYT' : 'экзамену'}`,
    levelDesc: (l, n, t, q, m, p, kind) => `${kind === 'licence' ? `Бесплатный тест к экзамену на международные права на яхту ${l}` : `Бесплатный тест ${l}`}: ${n} вопросов по ${t} темам с пояснением к каждому ответу, статья по теории для каждой темы и пробный экзамен на время (${q} вопросов, ${m} минут, проходной балл ${p} %).`,
    levelLead: (n, t) => `${n} вопросов по ${t} темам. У каждой темы есть статья с рисунками, которая объясняет правила из вопросов; приложение задаёт вопросы, объясняет каждый ответ и возвращает ошибки, пока вы не ответите верно.`,
    questions: 'вопросов', topics: 'тем', exam: 'вопросов в экзамене',
    examLine: (q, m, p) => `Пробный экзамен: ${q} вопросов со всех тем, ${m} минут, проходной балл ${p} %. Размер, время и проходной балл — настройки приложения, а не официальное правило.`,
    topicsK: 'Темы', otherK: 'Другие уровни', min: (m) => `${m} мин чтения`, nq: (n) => `${n} вопросов`, noArticle: 'статья ещё не написана',
    articleK: (i, n, m) => `Теория · тема ${i} из ${n} · ${m} мин`, contents: 'В статье',
    articleTitle: (t, l) => `${t}: теория и тест — ${l}`,
    qsK: 'Вопросы для тренировки', qsLead: 'Вопросы по этой теме — так, как их задаёт приложение. Откройте вопрос, чтобы увидеть ответ.',
    answer: 'Показать ответ', readSec: (k) => `Объяснение: ${k}`,
    ctaK: 'Потренируйтесь', ctaTopic: (n) => `Все ${n} вопросов этой темы — в приложении: тренировка по темам с пояснением после каждого ответа, ошибки возвращаются, есть пробный экзамен на время. Бесплатно, без регистрации, в браузере или в Telegram.`,
    ctaLevel: 'Тренируйтесь по темам с пояснением после каждого ответа, сдайте пробный экзамен на время и следите за прогрессом по каждой теме. Бесплатно, без регистрации, в браузере или в Telegram.',
    prev: (i) => `‹ Тема ${i}`, next: (i) => `Тема ${i} ›`,
    foot: 'Написано для подготовки, близко к программе IYT. Не издание IYT или World Sailing; авторитетны сами правила.',
    notFound: 'Такой страницы нет', notFoundLead: 'Возможно, в адресе опечатка или страница переехала. Уровни — ниже, приложение — на главной.',
    aboutTitle: 'Об IYT Test',
    aboutLead: 'Бесплатное приложение для подготовки к теории яхтенных сертификатов IYT — на русском и английском, в браузере и в Telegram.',
    aboutBody: [
      'IYT Test охватывает уровни IYT от VHF Radio Operator и International Crew до Yachtmaster Ocean, Правила парусных гонок и курс приёмки чартерной яхты. Каждый вопрос — ситуация, которая встречается на воде, и где можно, она нарисована: знак по курсу, огни ночью, пеленг на другую яхту, приборы двигателя. Четыре варианта и одна строка с правилом.',
      'У каждой темы каждого уровня есть статья по теории с рисунками, которая объясняет правила из её вопросов. В приложении вы тренируетесь по темам, ошибки возвращаются, пока вы не ответите верно, а пробный экзамен на время собирает вопросы со всех тем.',
      '**Написано для подготовки.** Вопросы и статьи — наша собственная работа, близкая к программе. Это не экзаменационные материалы IYT, ни IYT, ни World Sailing их не проверяли. Факты следуют МППСС, системе IALA и хорошей морской практике; где практика зависит от региона, статья это оговаривает. Размер экзамена, время и проходной балл — настройки самого приложения.',
    ],
    aboutWho: (h) => `Сделано RYC. Нашли ошибку? У каждого вопроса и каждого раздела статьи в приложении есть кнопка «Сообщить», или напишите автору в Telegram: <a href="https://t.me/${h}">@${h}</a>.`,
    aboutMcp: (u) => `Для ИИ-ассистентов: вопросы и статьи доступны как публичный MCP-сервер только для чтения — <code>${u}</code>. Добавьте его как свой коннектор и тренируйтесь в своём ассистенте.`,
    privacy: 'Конфиденциальность', privTitle: 'Политика конфиденциальности', privDate: 'Обновлено 5 ноября 2026 года',
    privLead: 'Что IYT Test хранит о вас, где, кто это видит и как это удалить. Коротко: в браузере — ничего, по чему вас можно узнать; в Telegram — ваше имя в Telegram и ваш прогресс, чтобы он был одинаковым на всех устройствах.',
    privBody: [
      ['Кто мы', 'IYT Test делает RYC. По любым вопросам о ваших данных пишите автору в Telegram: [@fullcrimp](https://t.me/fullcrimp).'],
      ['В браузере', 'Сайт и приложение не просят учётной записи. Ваш прогресс хранится **на вашем устройстве**, в памяти браузера, и нам не отправляется. Просмотры страниц мы считаем через Vercel Web Analytics: без cookie и без возможности узнать, кто вы, — видны только страница, сайт, с которого вы пришли, страна и тип устройства.'],
      ['В Telegram', 'Когда вы открываете приложение в Telegram, Telegram передаёт ему ваши **id, имя, имя пользователя и язык** с подписью, так что никто другой не может ими воспользоваться. Приложение хранит ваш прогресс в облачном хранилище Telegram и на нашем сервере, чтобы он был одинаковым на всех устройствах: на какие вопросы вы отвечали, верно ли, какой вариант выбрали и когда, ваши пробные экзамены, отмеченные вопросы и заметки, которые вы оставили к вопросу или разделу статьи.',
        'Администраторы IYT Test (автор) видят имя, имя пользователя, результаты, отметки и заметки каждого ученика — чтобы исправлять вопросы, о которых сообщают, и видеть, где возникают трудности. Ещё они видят фото вашего профиля в Telegram: оно загружается из Telegram, когда они открывают список, и не хранится.'],
      ['Бот в Telegram', 'Когда вы пишете [@iyt_test_bot](https://t.me/iyt_test_bot), он сохраняет ваши id, имя, имя пользователя и язык в Telegram и то, включён ли вопрос дня. Он не хранит то, что вы ему пишете, и ваши ответы на вопрос дня. Если вы заблокируете бота, он отметит это и перестанет писать.'],
      ['MCP-сервер', 'MCP-сервер для ИИ-ассистентов не просит входа и не хранит ничего о людях и ассистентах, которые к нему обращаются. Как и любой запрос к сайту, обращение проходит через журналы хостинга (IP-адрес, запрошенный адрес и время), которые Vercel хранит ограниченное время для работы сервиса.'],
      ['Кто ещё обрабатывает данные', 'Vercel размещает сайт, приложение и сервер и считает просмотры страниц. Supabase хранит базу данных в ЕС (Стокгольм). Telegram обслуживает бота, мини-приложение и его облачное хранилище. Больше ваши данные никто не получает: рекламы нет, ничего не продаётся.'],
      ['Сколько хранится и как удалить', 'Данные хранятся, пока работает приложение. Чтобы удалить их, напишите [@fullcrimp](https://t.me/fullcrimp) с того же аккаунта Telegram: ваше имя в Telegram, настройки, прогресс и ответы будут удалены с сервера. То, что хранится в браузере или в облачном хранилище Telegram, вы можете стереть сами — кнопкой «Сбросить прогресс» в профиле приложения.'],
      ['Изменения', 'Если политика изменится, изменится эта страница, с новой датой вверху.'],
    ],
    mcpHow: 'Как подключить', mcpBand: 'Тренируйтесь в Claude или ChatGPT', mcpBandText: 'Вопросы и теория доступны и как MCP-сервер: добавьте его в свой ИИ-ассистент, и он будет задавать вопросы, проверять ответы и объяснять правило.',
    mcp: 'Для ИИ-ассистентов', mcpK: 'MCP-сервер · бесплатно', mcpTitle: 'Тренируйтесь в своём ИИ-ассистенте',
    mcpDesc: 'Подключите IYT Test к Claude, ChatGPT или любому ассистенту с поддержкой MCP: он задаёт вопросы IYT, проверяет ответы, объясняет правило и проводит пробный экзамен. Бесплатно, без входа.',
    mcpLead: 'Вопросы и статьи по теории IYT Test доступны и как MCP-сервер. Добавьте его в Claude, ChatGPT или другой ассистент, который поддерживает Model Context Protocol, — и ассистент прямо в разговоре будет задавать вопросы, проверять ответы, объяснять правило за каждым и проводить пробный экзамен.',
    mcpUrlK: 'Адрес', mcpUrlNote: 'Публичный и только для чтения: без входа, без ключа, ничего не нужно устанавливать.',
    mcpBody: [
      ['Как подключить', '**Claude** (веб, компьютер и телефон): Настройки → Коннекторы → Добавить свой коннектор, затем вставьте адрес.',
        '**ChatGPT**: включите режим разработчика в настройках приложений и коннекторов и создайте коннектор с этим адресом. Нужен тариф, в котором доступны свои коннекторы.',
        '**Claude Code**, в терминале:', { code: (u) => `claude mcp add --transport http iyt-test ${u}` },
        '**Cursor, VS Code и другие приложения**, которые принимают список серверов в JSON:', { code: (u) => JSON.stringify({ mcpServers: { 'iyt-test': { type: 'streamable-http', url: u } } }, null, 2) }],
      ['Что спросить', { list: ['Задай мне пять вопросов по системе IALA для Bareboat Skipper, по одному.', 'Проведи пробный экзамен Yachtmaster Coastal и оцени его в конце.', 'Я путаю кардинальные знаки: объясни их, а потом проверь меня.', 'Задай мне вопрос дня на русском.'] },
        'Ассистент задаёт каждый вопрос с четырьмя вариантами и не называет ответ, пока вы не выберете. У большинства вопросов есть рисунок; если ассистент не может его показать, он получает ссылку на изображение.'],
      ['Что он умеет', { table: [
        ['list_levels', 'Уровни, их темы, настройки пробного экзамена и темы, у которых есть статья'],
        ['get_questions', 'Случайные вопросы уровня, темы или сложности, без ответов'],
        ['check_answer', 'Верно или нет, правильный вариант, пояснение с правилом и раздел теории, который его объясняет'],
        ['search_questions', 'Вопросы по словам: «кардинальный знак», «MAYDAY»'],
        ['start_mock_exam · grade_exam', 'Набор вопросов размером с экзамен со всех тем, затем результат, сдано или нет, ошибки и что прочитать'],
        ['question_of_the_day', 'Вопрос, который сегодня присылает бот в Telegram'],
        ['list_theory · get_theory · search_theory', 'Статьи по теории и их разделы — текстом со ссылками на рисунки'],
        ['explain_question', 'Вопрос с ответом и разделом теории, который его объясняет'],
        ['practice_section', 'Вопросы к разделу теории: прочитайте, затем потренируйтесь'],
        ['get_figure', 'Рисунок в формате SVG'],
      ] }, 'Все инструменты отвечают на английском или русском. То, что ещё не переведено, приходит на английском.'],
      ['Что он хранит', 'Ничего. Сервер не просит входа и ничего не хранит о вас и вашем ассистенте; ваш прогресс в приложении с ним не связан. Подробности — в [политике конфиденциальности](/ru/privacy).'],
      ['Где ещё его найти', 'Он опубликован в [официальном реестре MCP](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.nikolai-shilin/iyt-test) под именем `io.github.nikolai-shilin/iyt-test`. Вопросы и статьи написаны для подготовки, близко к программе; это не экзаменационные материалы IYT.'],
    ],
  },
};
const LANGS = ['en', 'ru'];
const FEEDBACK_HANDLE = 'fullcrimp'; // the author on Telegram, as in miniapp/app.js

// An address in a language: English at the root, Russian under /ru.
const at = (lang, path = '') => (lang === 'ru' ? `/ru${path}` : path || '/');
const appLink = (link) => `/?screen=${link}`;
const tgLink = (link) => `https://t.me/${BOT}?startapp=${link}`;

function setPath(obj, path, val) {
  const k = path.split('.');
  let o = obj;
  for (let i = 0; i < k.length - 1; i++) { o = o?.[k[i]]; if (o == null) return; }
  if (o != null) o[k[k.length - 1]] = val;
}
// The question in the reader's language, by the app's rule (localise in miniapp/app.js): translated only when the
// overlay has the question and all four options; the option order never changes.
function local(q, ov, lang) {
  const tr = lang === 'ru' && ov && ov.questions && ov.questions[q.id];
  if (!tr || !tr.q || (tr.options || []).length !== 4) return { ...q, _tr: lang === 'en' };
  const figure = q.figure ? structuredClone(q.figure) : null;
  if (figure) for (const [p, v] of Object.entries(tr.figure || {})) setPath(figure, p, v);
  return { ...q, q: tr.q, options: tr.options, why: tr.why || q.why, ref: tr.ref || q.ref, figure, _tr: true };
}

// A card figure (a script, a checklist): a line that carries on the one before stays under its bullet (as in app.js).
function cardItems(lines) {
  const out = [];
  lines.forEach((l, i) => {
    const prev = lines[i - 1];
    const cont = i > 0 && (/[:,]\s*$/.test(prev) || /^[\s(«"'“‘a-zа-яё]/u.test(l));
    if (cont) out[out.length - 1].push(l.trim()); else out.push([l]);
  });
  return out;
}
// A drawing as the app shows it (figHtml in app.js): the SVG in the page, coloured by the page's tokens.
function figure(f, { ru = false, view, label } = {}) {
  if (!f) return '';
  if (f.type === 'card') return `<div class="figcard">${f.tag ? `<span class="figtag">${esc(f.tag)}</span>` : ''}<span class="kicker">${esc(f.title || '')}</span>` +
    `<ul>${cardItems(f.lines || []).map((l) => `<li>${l.map(esc).join('<br>')}</li>`).join('')}</ul></div>`;
  for (const k in fig.FIG_TEXT) delete fig.FIG_TEXT[k];
  if (ru) Object.assign(fig.FIG_TEXT, FIG_RU);
  let svg = fig.figSvg(f).replace('<svg ', '<svg aria-hidden="true" focusable="false" ');
  if (view) svg = svg.replace(/viewBox="[^"]*"/, `viewBox="${esc(view)}"`);
  return `<div class="fig${f.type === 'lights' ? ' night' : fig.FIG_DAY.has(f.type) ? ' day' : ''}" role="img" aria-label="${esc(label || f.note || f.title || STR[ru ? 'ru' : 'en'].figure)}">${svg}</div>`;
}
// A figure with a photo (as thPhoto in app.js): the Blender render and its plan under it; a text card stays, under them.
function photo(o, { ru, label }) {
  const s = `/figs/${o.photo}`, l = ru ? '.ru' : '', img = (src, w, h, alt) => `<img src="${src}" width="${w}" height="${h}" loading="lazy" decoding="async" alt="${esc(alt)}">`;
  return `<figure class="th-photo">${img(`${s}${l}.webp`, 1280, 800, label || '')}${o.plan ? img(`${s}-plan${l}.webp`, 1200, Math.round(1200 / o.plan), '') : ''}</figure>` +
    (o.fig.type === 'card' ? figure(o.fig, { ru, view: o.view, label }) : '');
}
const pic = (o, opt) => (o.photo ? photo(o, opt) : figure(o.fig, { ...opt, view: o.view }));
function block(b, s, ru) {
  if (b.p) return `<p class="th-p">${inline(b.p)}</p>`;
  if (b.list) return `<ul class="th-list">${b.list.map((x) => `<li>${inline(x)}</li>`).join('')}</ul>`;
  if (b.fig) return pic(b, { ru, label: b.cap && plain(b.cap) }) + (b.cap ? `<p class="th-cap">${inline(b.cap)}</p>` : '');
  if (b.tiles) return `<div class="th-tiles c${[2, 3, 4].includes(b.cols) ? b.cols : Math.min(b.tiles.length, 4)}">${b.tiles.map((x) => `<div class="th-tile">${pic(x, { ru, label: x.name })}<b>${esc(x.name)}</b>${x.note ? `<span>${esc(x.note)}</span>` : ''}</div>`).join('')}</div>`;
  if (b.rule) return `<div class="band th-rule"><span class="kicker">${esc(b.label || s.ruleK)}</span><p class="body-s">${inline(b.rule)}</p></div>`;
  if (b.table && b.table.head && b.table.rows) return `<table class="th-table"><thead><tr>${b.table.head.map((x) => `<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${b.table.rows.map((r) => `<tr>${r.map((x) => `<td>${inline(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  return '';
}
// Reading time, as the app counts it (articleMeta in app.js).
function minutes(a) {
  let w = 0, p = 0;
  const add = (x) => { w += String(x || '').split(/\s+/).length; };
  add(a.lead);
  a.sections.forEach((sec) => {
    add(sec.title);
    sec.blocks.forEach((b) => { add(b.p); add(b.rule); (b.list || []).forEach(add); if (b.table) (b.table.rows || []).forEach((r) => r.forEach(add)); if (b.fig) p++; if (b.tiles) p += b.tiles.length; });
  });
  return Math.max(2, Math.round(w / 130 + p * 0.15));
}
// The questions shown under an article: one per section, a drawn one where the section has it (so the samples
// cover the article and each links to the section that explains it), topped up from the rest of the topic.
function samples(qs, art, n = 6) {
  const picked = [];
  for (const sec of art.sections) {
    const mine = qs.filter((q) => !picked.includes(q) && (sec.refs || []).includes(q.ref));
    const q = mine.find((x) => x.figure) || mine[0];
    if (q) picked.push(q);
    if (picked.length >= n) break;
  }
  for (const q of qs) { if (picked.length >= n) break; if (!picked.includes(q)) picked.push(q); }
  return picked;
}

// One page: the head search engines read (title, description, canonical, the other language, link previews,
// structured data) and the app's look; dark when the reader's system is.
function shell({ lang, path, alt = {}, title, desc, body, ld, css, type = 'website', noindex = false }) {
  const s = STR[lang], url = SITE + path;
  const alts = Object.entries(alt).map(([l, p]) => `<link rel="alternate" hreflang="${l}" href="${SITE}${p}">`);
  if (alt.en) alts.push(`<link rel="alternate" hreflang="x-default" href="${SITE}${alt.en}">`);
  const other = LANGS.find((l) => l !== lang);
  return `<!doctype html>
<html lang="${lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ffffff">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/icon.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/apple-icon.png">
${noindex ? '<meta name="robots" content="noindex">' : `<link rel="canonical" href="${url}">\n${alts.join('\n')}`}
<meta property="og:type" content="${type}">
<meta property="og:site_name" content="IYT Test">
<meta property="og:url" content="${url}">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${SITE}/intro.jpg">
<meta property="og:locale" content="${lang === 'ru' ? 'ru_RU' : 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
${css.map((h) => `<link rel="stylesheet" href="/${h}">`).join('\n')}
${ld ? `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, '\\u003c')}</script>` : ''}
</head>
<body>
<div class="screen app page" id="page">
<script>try { if (matchMedia('(prefers-color-scheme: dark)').matches) { document.getElementById('page').classList.add('theme-night'); document.documentElement.dataset.theme = 'dark'; document.querySelector('meta[name=theme-color]').content = '#000000'; } } catch (e) {}</script>
<header class="wrap pg-top"><a href="${at(lang)}" aria-label="IYT Test"><img class="logo" src="/design/logo-black.svg" alt="RYC" width="50" height="25"></a>
<nav><a href="${at(lang, '/about')}">${s.about}</a>${alt[other] ? `<a href="${alt[other]}" hreflang="${other}" lang="${other}">${STR[lang].other}</a>` : ''}</nav></header>
<main class="wrap">
${body}
</main>
<footer class="wrap pg-foot"><p style="margin:0">${s.foot}</p>
<nav><a href="${at(lang)}">${s.levels}</a><a href="${at(lang, '/about')}">${s.about}</a><a href="/">${s.practise}</a><a href="https://t.me/${BOT}">Telegram</a><a href="${at(lang, '/mcp')}">${s.mcp}</a><a href="${at(lang, '/privacy')}">${s.privacy}</a></nav></footer>
</div>
<script defer src="/_vercel/insights/script.js"></script>
</body>
</html>
`;
}
const crumbs = (items) => `<nav class="crumbs meta" aria-label="Breadcrumbs">${items.map(([name, href], i) => (i < items.length - 1 ? `<a href="${href}">${esc(name)}</a>` : `<span aria-current="page">${esc(name)}</span>`)).join('')}</nav>`;
const crumbLd = (items) => ({ '@type': 'BreadcrumbList', itemListElement: items.map(([name, href], i) => ({ '@type': 'ListItem', position: i + 1, name, item: SITE + href })) });
const cta = (s, text, link) => `<div class="band pg-cta"><span class="kicker">${s.ctaK}</span><p class="body-muted" style="margin:0">${text}</p>` +
  `<div class="row"><a class="pill pill-primary" href="${appLink(link)}">${s.practise}</a><a class="pill pill-quiet" href="${tgLink(link)}">${s.telegram}</a></div></div>`;
const ORG = { '@type': 'Organization', name: 'IYT Test', url: `${SITE}/`, logo: `${SITE}/design/logo-black.svg` };

export async function buildPages(out, { css }) {
  const sheet = await readFile(join(root, 'miniapp/site.css'), 'utf8');
  const sheetName = `h/site.${hash(sheet)}.css`;
  await writeFile(join(out, sheetName), sheet);
  css = [...css, sheetName];

  // every level with its Russian overlay and its articles in both languages
  const levels = [];
  for (const [id, link] of LEVELS.filter(([x]) => !PAUSED.includes(x))) { // a paused level has no pages (site.mjs)
    const bank = await readJson(`data/questions/${id}.json`);
    if (!bank) continue;
    const ov = await readJson(`data/questions/${id}.ru.json`);
    const art = {};
    for (const tp of bank.topics) {
      const en = await readJson(`data/theory/${id}/${tp.id}.json`);
      if (!en || !Array.isArray(en.sections)) continue;
      art[tp.id] = { en, ru: await readJson(`data/theory/${id}/${tp.id}.ru.json`) };
    }
    levels.push({ id, link, bank, ov, art, title: bank.title, kind: KIND[id] || 'other' });
  }
  const topicTitle = (L, tp, lang) => (lang === 'ru' && L.ov && L.ov.topics && L.ov.topics[tp.id]) || tp.title;

  const pages = []; // { path, lang, alt, html }
  const add = (p) => pages.push(p);

  for (const lang of LANGS) {
    const s = STR[lang];
    const home = at(lang);
    for (const L of levels) {
      const b = L.bank, lp = at(lang, `/${L.id}`);
      const has = (tp) => L.art[tp.id] && (lang === 'en' || L.art[tp.id].ru);
      // the level
      const rows = b.topics.map((tp, i) => {
        const a = has(tp) && L.art[tp.id][lang];
        const inner = `<span class="card-title">${i + 1}. ${esc(topicTitle(L, tp, lang))}</span><span class="card-meta">${a ? `${esc(first(a.lead))} · ${s.min(minutes(a))} · ` : ''}${s.nq(tp.count || b.questions.filter((q) => q.topic === tp.id).length)}${a ? '' : ` · ${s.noArticle}`}</span>`;
        return `<li>${a ? `<a class="band pg-row" href="${lp}/${tp.id}">${inner}</a>` : `<div class="band pg-row">${inner}</div>`}</li>`;
      }).join('');
      const others = levels.filter((x) => x !== L).map((x) => `<li><a class="band pg-row" href="${at(lang, `/${x.id}`)}"><span class="card-title">${esc(x.title)}</span><span class="card-meta">${s.nq(x.bank.questions.length)} · ${x.bank.topics.length} ${s.topics}</span></a></li>`).join('');
      const trail = [[s.levels, home], [L.title, lp]];
      const official = !['racing-rules', 'charter-checkin'].includes(L.id);
      add({
        path: lp, lang, alt: { en: `/${L.id}`, ru: `/ru/${L.id}` },
        html: shell({
          lang, path: lp, alt: { en: `/${L.id}`, ru: `/ru/${L.id}` }, css,
          title: `${s.levelTitle(L.title, L.kind)} · IYT Test`,
          desc: clip(s.levelDesc(L.title, b.questions.length, b.topics.length, b.examQuestions, b.examMinutes, b.passMark, L.kind), 300),
          ld: { '@context': 'https://schema.org', '@graph': [
            { '@type': 'CollectionPage', name: s.levelTitle(L.title, L.kind), url: SITE + lp, inLanguage: lang, isAccessibleForFree: true, publisher: ORG,
              about: { '@type': 'EducationalOccupationalCredential', name: L.title, ...(official ? { recognizedBy: { '@type': 'Organization', name: 'International Yacht Training Worldwide' } } : {}) },
              mainEntity: { '@type': 'ItemList', itemListElement: b.topics.filter(has).map((tp, i) => ({ '@type': 'ListItem', position: i + 1, name: topicTitle(L, tp, lang), url: `${SITE}${lp}/${tp.id}` })) } },
            crumbLd(trail)] },
          body: `${crumbs(trail)}
<div class="pg-head"><span class="meta">${s.kicker}</span><h1 class="display">${esc(s.levelTitle(L.title, L.kind))}</h1><p class="body-muted">${esc(s.levelLead(b.questions.length, b.topics.length))}</p></div>
<div class="band pg-facts"><div><b>${b.questions.length}</b><span class="meta">${s.questions}</span></div><div><b>${b.topics.length}</b><span class="meta">${s.topics}</span></div><div><b>${b.examQuestions}</b><span class="meta">${s.exam}</span></div></div>
<p class="card-meta" style="margin:-12px 0 0">${s.examLine(b.examQuestions, b.examMinutes, b.passMark)}</p>
<section class="stack g12"><h2 class="kicker">${s.topicsK}</h2><ol class="pg-list">${rows}</ol></section>
${cta(s, s.ctaLevel, L.link)}
<section class="stack g12"><h2 class="kicker">${s.otherK}</h2><ul class="pg-list">${others}</ul></section>`,
        }),
      });

      // its articles
      const arts = b.topics.filter(has);
      arts.forEach((tp) => {
        const a = L.art[tp.id][lang], en = L.art[tp.id].en, ru = lang === 'ru';
        const path = at(lang, `/${L.id}/${tp.id}`), alt = { en: `/${L.id}/${tp.id}` };
        if (L.art[tp.id].ru) alt.ru = `/ru/${L.id}/${tp.id}`;
        const tt = topicTitle(L, tp, lang), k = b.topics.indexOf(tp), m = minutes(a);
        const qs = b.questions.filter((q) => q.topic === tp.id);
        // the section of this article that explains a question: the one whose refs hold its English reference
        const secOf = (q) => { const e = en.sections.find((x) => (x.refs || []).includes(q.ref)); return e && (a.sections.find((x) => x.id === e.id) || e); };
        const sample = samples(qs, en).map((q) => ({ q: local(q, L.ov, lang), sec: secOf(q) }));
        const qHtml = sample.map(({ q, sec }) => {
          const own = q._tr ? '' : ' lang="en"'; // a question not translated yet is read in English
          // a question with a photo (as figHtml and qPlan in app.js): the render in the figure's place, its plan in the answer
          const ql = ru && q._tr ? '.ru' : '', qimg = (src, h, cls, alt) => `<img${cls} src="/figs/${esc(q.photo)}${src}${ql}.webp" width="960" height="${h}" loading="lazy" decoding="async" alt="${esc(alt)}">`;
          const fig = q.photo ? `<div class="qphoto">${qimg('', 600, '', (q.figure && q.figure.note) || '')}</div>` : figure(q.figure, { ru: ru && q._tr });
          const plan = q.photo && q.plan ? qimg('-plan', Math.round(960 / q.plan), ' class="qplan"', '') : '';
          return `<article class="pg-q" id="${esc(q.id)}"${own}>${fig}<p class="pg-qt">${esc(q.q)}</p>
<ol class="pg-opts" type="A">${q.options.map((o) => `<li>${esc(o)}</li>`).join('')}</ol>
<details><summary>${s.answer}</summary><p class="th-p"><b>${ABCD[q.answer]}. ${esc(q.options[q.answer])}</b></p><p class="th-p">${esc(q.why)}</p>${plan}` +
            `<p class="card-meta">${esc(q.ref)}${sec ? ` · <a href="#sec-${esc(sec.id)}">${esc(s.readSec(sec.kicker))}</a>` : ''}</p></details></article>`;
        }).join('\n');
        const near = (x, key) => (x ? `<a class="band th-near" href="${at(lang, `/${L.id}/${x.id}`)}"><span class="meta">${s[key](b.topics.indexOf(x) + 1)}</span><span class="card-title">${esc(topicTitle(L, x, lang))}</span></a>` : '<span></span>');
        const ai = arts.indexOf(tp);
        const trail = [[s.levels, home], [L.title, lp], [tt, path]];
        add({
          path, lang, alt,
          html: shell({
            lang, path, alt, css, type: 'article',
            title: `${s.articleTitle(tt, L.title)} · IYT Test`,
            desc: clip(a.lead),
            ld: { '@context': 'https://schema.org', '@graph': [
              { '@type': 'Article', headline: tt, description: plain(a.lead), inLanguage: lang, url: SITE + path, mainEntityOfPage: SITE + path, image: `${SITE}/intro.jpg`,
                author: ORG, publisher: ORG, isAccessibleForFree: true, timeRequired: `PT${m}M`, educationalLevel: L.title,
                isPartOf: { '@type': 'CollectionPage', name: s.levelTitle(L.title, L.kind), url: SITE + lp },
                articleSection: a.sections.map((x) => x.kicker) },
              { '@type': 'Quiz', name: `${tt}: ${s.qsK}`, inLanguage: lang, educationalLevel: L.title, url: `${SITE}${path}#questions`,
                hasPart: sample.map(({ q }) => ({ '@type': 'Question', eduQuestionType: 'Multiple choice', text: q.q,
                  acceptedAnswer: { '@type': 'Answer', text: q.options[q.answer], answerExplanation: { '@type': 'Comment', text: q.why } },
                  suggestedAnswer: q.options.filter((o, i) => i !== q.answer).map((o) => ({ '@type': 'Answer', text: o })) })) },
              ...(a.sections.some((x) => x.qa) ? [{ '@type': 'FAQPage', inLanguage: lang, url: SITE + path,
                mainEntity: a.sections.filter((x) => x.qa && x.qa.q && x.qa.a).map((x) => ({ '@type': 'Question', name: x.qa.q, url: `${SITE}${path}#sec-${x.id}`,
                  acceptedAnswer: { '@type': 'Answer', text: plain(x.qa.a) } })) }] : []),
              crumbLd(trail)] },
            body: `${crumbs(trail)}
<div class="pg-head"><span class="meta">${esc(s.articleK(k + 1, b.topics.length, m))}</span><h1 class="display-s">${esc(tt)}</h1></div>
<p class="th-p th-lead">${inline(a.lead)}</p>
<nav class="th-toc" aria-label="${s.contents}">${a.sections.map((x) => `<a class="chip" href="#sec-${esc(x.id)}">${esc(x.kicker)}</a>`).join('')}<a class="chip" href="#questions">${s.qsK}</a></nav>
${a.sections.map((x, n) => `<section class="th-sec" id="sec-${esc(x.id)}"><span class="kicker">${n + 1} · ${esc(x.kicker)}</span><h2 class="th-h">${esc(x.title)}</h2>${x.qa && x.qa.q && x.qa.a ? `<div class="th-qa"><p class="th-q">${esc(x.qa.q)}</p><p class="th-p">${inline(x.qa.a)}</p></div>` : ''}${x.blocks.map((bl) => block(bl, s, ru)).join('')}</section>`).join('\n')}
<section class="stack g12" id="questions"><h2 class="th-h">${s.qsK}</h2><p class="body-muted">${s.qsLead}</p>
${qHtml}</section>
${cta(s, s.ctaTopic(qs.length), L.link)}
<div class="th-nextprev">${near(arts[ai - 1], 'prev')}${near(arts[ai + 1], 'next')}</div>`,
          }),
        });
      });
    }

    // about
    const ap = at(lang, '/about');
    add({
      path: ap, lang, alt: { en: '/about', ru: '/ru/about' },
      html: shell({
        lang, path: ap, alt: { en: '/about', ru: '/ru/about' }, css, title: `${s.aboutTitle} · IYT Test`, desc: clip(s.aboutLead),
        ld: { '@context': 'https://schema.org', '@graph': [{ '@type': 'AboutPage', name: s.aboutTitle, url: SITE + ap, inLanguage: lang, publisher: ORG }, crumbLd([[s.levels, home], [s.aboutTitle, ap]])] },
        body: `${crumbs([[s.levels, home], [s.aboutTitle, ap]])}
<div class="pg-head"><h1 class="display">${s.aboutTitle}</h1><p class="body-muted">${esc(s.aboutLead)}</p></div>
${s.aboutBody.map((p) => `<p class="th-p">${inline(p)}</p>`).join('\n')}
<p class="th-p">${s.aboutWho(FEEDBACK_HANDLE)}</p>
<p class="th-p">${s.aboutMcp(`${SITE}/api/mcp`)} <a href="${at(lang, '/mcp')}">${s.mcpHow}</a>.</p>
${cta(s, s.ctaLevel, 'level')}`,
      }),
    });

    // privacy
    const pp = at(lang, '/privacy');
    add({
      path: pp, lang, alt: { en: '/privacy', ru: '/ru/privacy' },
      html: shell({
        lang, path: pp, alt: { en: '/privacy', ru: '/ru/privacy' }, css, title: `${s.privTitle} · IYT Test`, desc: clip(s.privLead),
        ld: { '@context': 'https://schema.org', '@graph': [{ '@type': 'WebPage', name: s.privTitle, url: SITE + pp, inLanguage: lang, publisher: ORG, dateModified: '2026-11-05' }, crumbLd([[s.levels, home], [s.privTitle, pp]])] },
        body: `${crumbs([[s.levels, home], [s.privTitle, pp]])}
<div class="pg-head"><span class="meta">${s.privDate}</span><h1 class="display">${s.privTitle}</h1><p class="body-muted">${esc(s.privLead)}</p></div>
${s.privBody.map(([h, ...ps]) => `<section class="th-sec"><h2 class="th-h">${esc(h)}</h2>${ps.map((p) => `<p class="th-p">${rich(p)}</p>`).join('')}</section>`).join('\n')}`,
      }),
    });

    // the MCP server
    const mp = at(lang, '/mcp'), mcpUrl = `${SITE}/api/mcp`;
    const mcpBlock = (bl) => (typeof bl === 'string' ? `<p class="th-p">${rich(bl)}</p>`
      : bl.code ? `<pre class="pg-code"><code>${esc(bl.code(mcpUrl))}</code></pre>`
      : bl.list ? `<ul class="th-list">${bl.list.map((x) => `<li>${rich(x)}</li>`).join('')}</ul>`
      : `<table class="th-table pg-tools"><tbody>${bl.table.map(([k, v]) => `<tr><td><code>${esc(k).replace(/ · /g, '<br>')}</code></td><td>${esc(v)}</td></tr>`).join('')}</tbody></table>`);
    add({
      path: mp, lang, alt: { en: '/mcp', ru: '/ru/mcp' },
      html: shell({
        lang, path: mp, alt: { en: '/mcp', ru: '/ru/mcp' }, css, title: `${s.mcpTitle} · IYT Test`, desc: clip(s.mcpDesc),
        ld: { '@context': 'https://schema.org', '@graph': [{ '@type': 'WebPage', name: s.mcpTitle, url: SITE + mp, inLanguage: lang, publisher: ORG,
          about: { '@type': 'WebAPI', name: 'IYT Test MCP server', url: mcpUrl, documentation: SITE + mp, isAccessibleForFree: true, provider: ORG } }, crumbLd([[s.levels, home], [s.mcp, mp]])] },
        body: `${crumbs([[s.levels, home], [s.mcp, mp]])}
<div class="pg-head"><span class="meta">${s.mcpK}</span><h1 class="display">${s.mcpTitle}</h1><p class="body-muted">${esc(s.mcpLead)}</p></div>
<div class="band pg-cta"><span class="kicker">${s.mcpUrlK}</span><pre class="pg-code pg-url"><code>${esc(mcpUrl).replace('.com/', '.com/<wbr>')}</code></pre><p class="body-muted" style="margin:0">${s.mcpUrlNote}</p></div>
${s.mcpBody.map(([h, ...bs]) => `<section class="th-sec"><h2 class="th-h">${esc(h)}</h2>${bs.map(mcpBlock).join('')}</section>`).join('\n')}`,
      }),
    });
  }

  // Russian home: the levels (in English the app at / is the home page, with the same list for crawlers)
  {
    const s = STR.ru;
    add({
      path: '/ru', lang: 'ru', alt: { en: '/', ru: '/ru' },
      html: shell({
        lang: 'ru', path: '/ru', alt: { en: '/', ru: '/ru' }, css,
        title: 'Права на яхту IYT: тест и теория к экзамену, от VHF до Yachtmaster Ocean · IYT Test',
        desc: 'Бесплатный тест к экзамену на международные права на яхту IYT: вопросы в картинках с пояснением к каждому ответу, теория по МППСС, навигации и безопасности, пробный экзамен. От VHF до Yachtmaster Ocean.',
        ld: { '@context': 'https://schema.org', '@type': 'WebPage', name: s.homeTitle, url: `${SITE}/ru`, inLanguage: 'ru', publisher: ORG,
          mainEntity: { '@type': 'ItemList', itemListElement: levels.map((L, i) => ({ '@type': 'ListItem', position: i + 1, name: L.title, url: `${SITE}/ru/${L.id}` })) } },
        body: `<div class="pg-head"><span class="meta">${s.kicker}</span><h1 class="display">${s.homeTitle}</h1><p class="body-muted">${s.homeLead}</p></div>
<section class="stack g12"><h2 class="kicker">${s.levels}</h2><ul class="pg-list">${levels.map((L) => `<li><a class="band pg-row" href="/ru/${L.id}"><span class="card-title">${esc(L.title)}</span><span class="card-meta">${s.nq(L.bank.questions.length)} · ${L.bank.topics.length} ${s.topics}</span></a></li>`).join('')}</ul></section>
${cta(s, s.ctaLevel, 'level')}
<div class="band pg-cta pg-mcp"><span class="kicker">${s.mcp}</span><div class="card-title">${s.mcpBand}</div><p class="body-muted" style="margin:0">${s.mcpBandText}</p><a class="pill pill-quiet" href="/ru/mcp">${s.mcpHow}</a></div>`,
      }),
    });
  }

  // the page for an address that is not here (Vercel serves 404.html), not indexed
  await writeFile(join(out, '404.html'), shell({
    lang: 'en', path: '/404', css, noindex: true, title: `${STR.en.notFound} · IYT Test`, desc: STR.en.notFoundLead,
    body: `<div class="pg-head"><h1 class="display">${STR.en.notFound}</h1><p class="body-muted">${STR.en.notFoundLead}</p></div>
<ul class="pg-list">${levels.map((L) => `<li><a class="band pg-row" href="/${L.id}"><span class="card-title">${esc(L.title)}</span><span class="card-meta">${STR.en.nq(L.bank.questions.length)}</span></a></li>`).join('')}</ul>`,
  }));

  for (const p of pages) {
    const file = join(out, `${p.path.slice(1)}.html`);
    await mkdir(dirname(file), { recursive: true });
    await writeFile(file, p.html);
  }

  // the app's own home page goes in the sitemap and pages.json too (built by build.mjs)
  const index = await readFile(join(out, 'index.html'), 'utf8');
  const all = [{ path: '/', lang: 'en', alt: { en: '/', ru: '/ru' }, html: index }, ...pages];
  const link = (l, p) => `<xhtml:link rel="alternate" hreflang="${l}" href="${SITE}${p}"/>`;
  await writeFile(join(out, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${all.map((p) => `  <url><loc>${SITE}${p.path}</loc>${Object.keys(p.alt).length > 1 ? Object.entries(p.alt).map(([l, x]) => link(l, x)).join('') + link('x-default', p.alt.en) : ''}</url>`).join('\n')}
</urlset>
`);
  // a hash of each page without what changes on every build (the app's hashed file names): a page whose words,
  // drawings or links changed gets a new one
  const steady = (h) => h.replace(/\/?h\/[\w.-]+\.[0-9a-f]{10}\.(css|js|json)/g, '');
  await writeFile(join(out, 'pages.json'), JSON.stringify(Object.fromEntries(all.map((p) => [p.path, hash(steady(p.html))])), null, 1));

  // llms.txt (llmstxt.org): what the site is and where its content is, for AI assistants
  await writeFile(join(out, 'llms.txt'), `# IYT Test

> Free practice questions and theory articles for IYT sailing certification levels (VHF Radio Operator, International Crew, Flotilla Skipper, Bareboat Skipper, Yachtmaster Coastal, Offshore and Ocean), the Racing Rules of Sailing and a charter check-in course, in English and Russian. Written for study, close to the syllabus; not an IYT or World Sailing publication.

Each level page lists its topics; each topic page is a theory article with drawings, followed by sample questions with their answers and the rule behind each. The full question banks are practised in the app at ${SITE}/ (also in Telegram: https://t.me/${BOT}). Russian pages are the same addresses under ${SITE}/ru.

## Levels

${levels.map((L) => `- [${L.title}](${SITE}/${L.id}): ${L.bank.questions.length} questions in ${L.bank.topics.length} topics; mock exam of ${L.bank.examQuestions} questions in ${L.bank.examMinutes} minutes`).join('\n')}

${levels.map((L) => `## ${L.title}: theory\n\n${L.bank.topics.filter((tp) => L.art[tp.id]).map((tp) => `- [${tp.title}](${SITE}/${L.id}/${tp.id}): ${clip(L.art[tp.id].en.lead, 200)}`).join('\n')}`).join('\n\n')}

## For AI assistants

- [MCP server](${SITE}/api/mcp) (how to connect it: ${SITE}/mcp): public, read-only, no sign-in. Tools to list levels and topics, draw questions (without answers), check an answer, run and grade a mock exam, read and search the theory articles, and get a drawing as SVG. Every tool takes lang (en or ru).

## Optional

- [About](${SITE}/about): what IYT Test is, who makes it, and what it is not
- [Privacy](${SITE}/privacy): what the site, the app, the bot and the MCP server keep about you
`);
  return all.length;
}
