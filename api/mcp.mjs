// The MCP server of IYT Test: the question banks and the theory articles as tools for AI assistants (Claude, ChatGPT
// and anything else that speaks the Model Context Protocol). Public and read-only: everything it returns is already
// served to the mini app, there is no sign-in and nothing is saved.
//
//   POST /api/mcp                                            JSON-RPC 2.0 over Streamable HTTP, stateless: initialize,
//                                                            ping, tools/list, tools/call; notifications get 202
//   GET  /api/mcp?figure=bs-001[&lang=ru]                    a question's drawing (SVG image)
//   GET  /api/mcp?figure=bareboat-skipper/buoyage/lateral/1  the nth drawing of a theory section (SVG image)
//   GET  /api/mcp                                            405: the server opens no stream of its own
//
// Tools (TOOLS below): list_levels, get_questions, check_answer, search_questions, start_mock_exam, grade_exam,
// question_of_the_day, list_theory, get_theory, search_theory, explain_question, practice_section, get_figure.
// A question goes out without its answer; check_answer, grade_exam and explain_question give the answer, the note and
// the theory section that explains the rule (the section whose refs hold the question's reference, as in the app).
//
// No dependencies: the protocol is a few JSON-RPC methods, written out here. The banks (data/questions), the articles
// (data/theory) and the figure generator (docs/design/figures.js) are bundled with the function (vercel.json
// includeFiles) and read once per instance; a level without a bank file and a topic without an article are left out,
// so articles appear here as they are written. Add the server to an assistant as a remote MCP server (custom
// connector) with the URL SITE/api/mcp (miniapp/site.mjs): https://iyt.rycrentals.com/api/mcp.

import { readFile } from 'node:fs/promises';
import { SITE, PAUSED } from '../miniapp/site.mjs';

const root = new URL('../', import.meta.url);
// The Russian texts carry English sailing terms as tags, "створом [[transit]]" (docs/theory.md): here they read as
// "створом (transit)", which helps an assistant explain the term.
const readJson = async (path) => { try { return JSON.parse(await readFile(new URL(path, root), 'utf8'), (k, v) => (typeof v === 'string' ? v.replace(/ \[\[([^\]]*)\]\]/g, ' ($1)') : v)); } catch { return null; } };

// The levels in the app's order; `link` is the mini app deep link that opens the level (as in bot/core.mjs).
const LEVELS = [['vhf-radio-operator', 'vhf'], ['international-crew', 'crew'], ['flotilla-skipper', 'flotilla'], ['bareboat-skipper', 'bareboat'], ['yachtmaster-coastal', 'coastal'], ['yachtmaster-offshore', 'offshore'], ['yachtmaster-ocean', 'ocean'], ['racing-rules', 'racing'], ['charter-checkin', 'checkin']];
// An article the tools can walk; one that is not shaped like this is left out (data/check_theory.mjs says why).
const isArticle = (a) => !!a && Array.isArray(a.sections) && a.sections.length > 0 && a.sections.every((s) => s && typeof s.id === 'string' && Array.isArray(s.blocks));
// Each bank with its Russian overlay (anything missing stays English) and its articles: topic → { en, ru | null }.
const banks = (await Promise.all(LEVELS.filter(([id]) => !PAUSED.includes(id)).map(async ([id, link]) => { // not the paused ones (site.mjs)
  const bank = await readJson(`data/questions/${id}.json`);
  if (!bank || !Array.isArray(bank.questions) || !Array.isArray(bank.topics)) return null;
  const ru = (await readJson(`data/questions/${id}.ru.json`)) || {}, theory = {};
  await Promise.all(bank.topics.map(async (tp) => {
    const en = await readJson(`data/theory/${id}/${tp.id}.json`);
    if (!isArticle(en)) return;
    const tr = await readJson(`data/theory/${id}/${tp.id}.ru.json`);
    theory[tp.id] = { en, ru: isArticle(tr) ? tr : null };
  }));
  return { id, link, bank, ru, theory };
}))).filter(Boolean);
const byLevel = Object.fromEntries(banks.flatMap((b) => [[b.id, b], [b.link, b]]));
const byId = {};
for (const b of banks) for (const q of b.bank.questions) byId[q.id] = { q, b };

// figures.js is a browser script: run it here, as data/check_theory.mjs does. Without it no drawing is offered.
const figLib = await readFile(new URL('docs/design/figures.js', root), 'utf8')
  .then((src) => new Function(`${src}\nreturn { figSvg, FIG_TEXT };`)()).catch(() => null);
// Built-in labels of the figures in Russian: the same list as FIG_RU in miniapp/app.js.
const FIG_RU = {
  wind: 'ветер', N: 'N', You: 'Вы', Other: 'Другое судно', 'Night · lights seen ahead': 'Ночь · огни по курсу',
  'Light at night': 'Огонь ночью', 'N (true)': 'N ист.', MN: 'N магн.', Variation: 'Склонение', Deviation: 'Девиация',
  'True course': 'ИК', W: 'W', E: 'E', 'Depths in metres below chart datum': 'Глубины в метрах от нуля глубин',
  Anchoring: 'Якорная стоянка', 'Northern hemisphere': 'Северное полушарие',
  zone: 'зона', pin: 'знак', RC: 'ГК', LW: 'МВ', HW: 'ПВ', A: 'A', B: 'B', C: 'C', D: 'D',
};
// The day tokens of docs/design/app.css: an image on its own has no page to take them from.
const TOKENS = { bg: '#ffffff', ink: '#000000', muted: '#6d7a7e', faint: '#b8c2c6', band: '#f2f7f9', line: '#eef2f4', 'tag-line': '#dfe5e8', accent: '#0290d7', danger: '#d40000' };
const NIGHT = { ...TOKENS, bg: '#07101a', ink: '#ffffff', muted: '#a8b9c9', faint: '#5c6f80', band: '#07101a' }; // lights are seen at night
const MARGIN = 12;
// One figure as an image file: colours written in, a background, a size. `view` crops it (theory tiles, "x y w h").
function drawing(spec, { ru = false, view } = {}) {
  if (!figLib || !spec || spec.type === 'card') return null;
  for (const k in figLib.FIG_TEXT) delete figLib.FIG_TEXT[k];
  if (ru) Object.assign(figLib.FIG_TEXT, FIG_RU);
  let svg;
  try { svg = figLib.figSvg(spec); } catch { return null; }
  const tok = spec.type === 'lights' ? NIGHT : TOKENS;
  const [x, y, w, h] = (/^\s*-?[\d.]+(\s+-?[\d.]+){3}\s*$/.test(view || '') ? view : (svg.match(/viewBox="([^"]*)"/) || [])[1] || '0 0 320 200').trim().split(/\s+/).map(Number);
  const box = [x - MARGIN, y - MARGIN, w + 2 * MARGIN, h + 2 * MARGIN];
  const style = `<style>.sea{fill:none;stroke:${tok.faint};stroke-width:2;stroke-linecap:round}.glow{filter:drop-shadow(0 0 6px currentColor)}</style>`;
  return svg
    .replace(/<svg [^>]*>/, (tag) => tag.replace(/viewBox="[^"]*"/, `viewBox="${box.join(' ')}"`).replace('width="100%"', `xmlns="http://www.w3.org/2000/svg" width="${box[2] * 2}" height="${box[3] * 2}"`) +
      `${style}<rect x="${box[0]}" y="${box[1]}" width="${box[2]}" height="${box[3]}" fill="${tok.band}"/>`)
    .replace(/var\(--([a-z-]+)\)/g, (m, k) => tok[k] || m);
}

const ABCD = 'ABCD';
const LANGS = ['en', 'ru'];
const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const norm = (s) => String(s ?? '').toLowerCase().replace(/ё/g, 'е');
function setPath(obj, path, val) {
  const k = path.split('.');
  let o = obj;
  for (let i = 0; i < k.length - 1; i++) { o = o?.[k[i]]; if (o == null) return; }
  if (o != null) o[k[k.length - 1]] = val;
}
// The question in the reader's language, by the app's rule (localise in miniapp/app.js): translated only when the
// overlay has the question and all four options; the option order never changes.
function local(q, b, lang) {
  const tr = lang === 'ru' && b.ru.questions && b.ru.questions[q.id];
  if (!tr || !tr.q || (tr.options || []).length !== 4) return q;
  const figure = q.figure ? structuredClone(q.figure) : null;
  if (figure) for (const [p, v] of Object.entries(tr.figure || {})) setPath(figure, p, v);
  return { ...q, q: tr.q, options: tr.options, why: tr.why || q.why, ref: tr.ref || q.ref, figure, _tr: true };
}
const topicTitle = (b, id, lang) => (lang === 'ru' && b.ru.topics && b.ru.topics[id]) || b.bank.topics.find((t) => t.id === id)?.title || id;
// A topic's article in the language asked for, or in English while the translation is not written.
function article(b, topic, lang) {
  const t = b.theory[topic];
  if (!t) return null;
  return lang === 'ru' && t.ru ? { a: t.ru, lang: 'ru' } : { a: t.en, lang: 'en' };
}
// The section that explains a question: the one of its topic's article whose refs hold the question's reference as
// the English bank spells it (sectionOf in miniapp/app.js). null when there is no article or no section lists it.
function sectionOf(q, b, lang) {
  const t = b.theory[q.topic], en = t && t.en.sections.find((s) => (s.refs || []).includes(q.ref));
  if (!en) return null;
  const s = article(b, q.topic, lang).a.sections.find((x) => x.id === en.id) || en;
  return { level: b.id, topic: q.topic, section: s.id, kicker: s.kicker, title: s.title };
}
// The figures of a section in reading order (full-width ones and tiles): the number in a theory figure's address.
const figuresOf = (s) => s.blocks.flatMap((bl) => (bl.fig ? [bl] : (bl.tiles || []).filter((t) => t && t.fig)));
const figureUrl = (ctx, id) => `${ctx.origin}/api/mcp?figure=${id}${ctx.lang === 'ru' ? '&lang=ru' : ''}`;

// A question as the tools give it: no answer unless asked for. A card figure is text; any other is a drawing with
// its address and the spec it is drawn from.
function show(id, ctx, answer = false) {
  const { q: src, b } = byId[id], q = local(src, b, ctx.lang);
  const out = { id: q.id, level: b.id, topic: q.topic, topic_title: topicTitle(b, q.topic, ctx.lang), difficulty: q.difficulty,
    question: q.q, options: Object.fromEntries(q.options.map((o, i) => [ABCD[i], o])) };
  if (q.figure) out.figure = q.figure.type === 'card' || !figLib ? q.figure : { type: q.figure.type, url: figureUrl(ctx, q.id), spec: q.figure };
  if (answer) Object.assign(out, { answer: ABCD[q.answer], answer_text: q.options[q.answer], why: q.why, reference: q.ref, theory: sectionOf(src, b, ctx.lang) });
  return out;
}

// ---------- theory as text ----------
const cell = (s) => String(s ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
function sectionText(b, topic, s, got, ctx) {
  const out = [`## ${s.kicker}: ${s.title}`, `Section id: \`${s.id}\``];
  if (s.qa && s.qa.q && s.qa.a) out.push(`**${s.qa.q}** ${s.qa.a}`); // the opener: the question and its short answer
  const figs = figuresOf(s);
  const link = (f, label) => (f.fig.type === 'card' || !figLib ? '' : `[${label}](${figureUrl({ ...ctx, lang: got }, `${b.id}/${topic}/${s.id}/${figs.indexOf(f) + 1}`)})`);
  const card = (f) => [f.title && `**${f.title}**`, ...(f.lines || []).map((l) => `- ${l}`)].filter(Boolean).join('\n');
  for (const bl of s.blocks) {
    if (bl.p) out.push(bl.p);
    else if (bl.list) out.push(bl.list.map((l) => `- ${l}`).join('\n'));
    else if (bl.rule) out.push(`> **${bl.label || (got === 'ru' ? 'Правило' : 'Rule')}:** ${bl.rule}`);
    else if (bl.table) out.push([bl.table.head, bl.table.head.map(() => '---'), ...(bl.table.rows || [])].map((r) => `| ${r.map(cell).join(' | ')} |`).join('\n'));
    else if (bl.fig) out.push(bl.fig.type === 'card' ? card(bl.fig) : link(bl, `${got === 'ru' ? 'Рисунок' : 'Drawing'}: ${bl.cap || bl.fig.note || bl.fig.type}`));
    else if (bl.tiles) out.push(bl.tiles.map((t) => `- **${t.name || ''}**${t.note ? `: ${t.note}` : ''}${t.fig ? ` ${link(t, got === 'ru' ? 'рисунок' : 'drawing')}` : ''}`).join('\n'));
  }
  return out.filter(Boolean).join('\n\n');
}
function articleText(b, topic, lang, only, ctx) {
  const { a, lang: got } = article(b, topic, lang);
  const sections = only ? a.sections.filter((s) => s.id === only) : a.sections;
  return [
    `# ${topicTitle(b, topic, got)} (${b.bank.title})`,
    lang !== got && 'This article is not translated into Russian yet: the English text follows.',
    !only && a.lead,
    ...sections.map((s) => sectionText(b, topic, s, got, ctx)),
  ].filter(Boolean).join('\n\n');
}
const blockWords = (bl) => [bl.p, bl.rule, bl.cap, ...(bl.list || []), ...(bl.tiles || []).flatMap((t) => [t.name, t.note]), ...(bl.table ? [bl.table.head, ...(bl.table.rows || [])].flat() : [])].filter(Boolean).join(' ');

// ---------- the tools ----------
class Bad extends Error {} // the caller's mistake: goes back as the tool's answer, so the assistant can correct itself
const need = (ok, msg) => { if (!ok) throw new Bad(msg); };
const levelOf = (v) => { need(byLevel[v], `Unknown level "${v ?? ''}". Levels: ${banks.map((b) => b.id).join(', ')}.`); return byLevel[v]; };
const topicOf = (b, v) => { need(b.bank.topics.some((t) => t.id === v), `Unknown topic "${v ?? ''}" in ${b.id}. Topics: ${b.bank.topics.map((t) => t.id).join(', ')}.`); return v; };
const questionOf = (v) => { need(typeof v === 'string' && byId[v], `Unknown question "${v ?? ''}". Ids look like ${banks[0]?.bank.questions[0]?.id}.`); return v; };
const optionOf = (v) => { const i = typeof v === 'string' ? ABCD.indexOf(v.trim().toUpperCase()) : -1; need(i >= 0 && v.trim().length === 1, 'option is one letter: A, B, C or D.'); return i; };
const countOf = (v, def, max) => (v == null ? def : (need(Number.isInteger(v) && v >= 1 && v <= max, `count is a whole number from 1 to ${max}.`), v));
const termsOf = (v) => { const t = norm(v).split(/[^\p{L}\p{N}]+/u).filter(Boolean); need(t.length, 'query is empty.'); return t.slice(0, 8); };
const withArticle = (b, v) => { topicOf(b, v); need(b.theory[v], `No article for "${v}" in ${b.id} yet. Topics with one: ${Object.keys(b.theory).join(', ') || 'none'}.`); return v; };
// Up to n questions out of ids, at random, leaving out the ones the student has already had.
const pick = (ids, n, exclude) => { const skip = new Set(Array.isArray(exclude) ? exclude : []); return shuffle(ids.filter((id) => !skip.has(id))).slice(0, n); };
// What to read after wrong answers: their topics that have an article, most mistakes first, with the sections that
// explain them — the results screen of the app.
function reading(wrong, ctx) {
  const by = {};
  for (const id of wrong) {
    const { q, b } = byId[id];
    if (!b.theory[q.topic]) continue;
    const r = (by[`${b.id}/${q.topic}`] ||= { level: b.id, topic: q.topic, title: topicTitle(b, q.topic, ctx.lang), mistakes: 0, sections: [] });
    r.mistakes++;
    const s = sectionOf(q, b, ctx.lang);
    if (s && !r.sections.some((x) => x.section === s.section)) r.sections.push({ section: s.section, kicker: s.kicker, title: s.title });
  }
  return Object.values(by).sort((a, z) => z.mistakes - a.mistakes);
}
// The text the searches look in, built once per language.
const hay = {};
const questionHay = (lang) => (hay[`q${lang}`] ||= Object.values(byId).map(({ q, b }) => {
  const l = local(q, b, lang);
  return { id: q.id, level: b.id, head: norm(l.q), text: norm([l.q, ...l.options, l.ref, q.ref, topicTitle(b, q.topic, lang)].join(' ')) };
}));
const theoryHay = (lang) => (hay[`t${lang}`] ||= banks.flatMap((b) => Object.keys(b.theory).flatMap((topic) => {
  const { a } = article(b, topic, lang);
  return a.sections.map((s) => {
    const body = s.blocks.map(blockWords).join(' ');
    return { level: b.id, topic, section: s.id, kicker: s.kicker, title: s.title, body, head: norm(`${s.kicker} ${s.title} ${(s.refs || []).join(' ')}`), text: norm(`${s.kicker} ${s.title} ${(s.refs || []).join(' ')} ${body}`) };
  });
})));
// The best matches: every word of the query is there; the ones with more of them in the heading come first.
const find = (rows, terms, level, limit) => rows.filter((r) => (!level || r.level === level) && terms.every((t) => r.text.includes(t)))
  .map((r) => [r, terms.filter((t) => r.head.includes(t)).length]).sort((a, z) => z[1] - a[1]).slice(0, limit).map(([r]) => r);

// Question of the day: the same pick as the bot's (questionOfTheDay in bot/core.mjs) — text questions only, one per UTC
// day, per level when one is given.
const daily = Object.values(byId).filter(({ q }) => !q.figure);
function questionOfTheDay(day, levelId) {
  const own = daily.filter(({ b }) => b.id === levelId), pool = own.length ? own : daily;
  let h = 2166136261; // FNV-1a over "day|level"
  for (const ch of `${day}|${levelId || ''}`) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return pool[h % pool.length].q;
}

const LANG = { type: 'string', enum: LANGS, description: 'Language of the text: en (default) or ru. What is not translated yet comes in English.' };
const LEVEL = { type: 'string', description: 'Level id, e.g. bareboat-skipper.' };
const QID = { type: 'string', description: 'Question id, e.g. bs-001.' };
const EXCLUDE = { type: 'array', items: { type: 'string' }, description: 'Question ids the student has already had in this conversation, so they are not repeated.' };
const tool = (name, title, description, properties, required, run) => ({ name, title, description, inputSchema: { type: 'object', properties, required, additionalProperties: false }, annotations: { title, readOnlyHint: true, openWorldHint: false }, run });
const TOOLS = [
  tool('list_levels', 'List levels', 'The levels with a question bank (sailing certification courses, the Racing Rules of Sailing, the charter check-in): topics, number of questions, mock-exam settings and which topics have a theory article.',
    { lang: LANG }, [], (a, ctx) => banks.map((b) => ({
      id: b.id, title: b.bank.title, questions: b.bank.questions.length, russian: !!(b.ru.questions && Object.keys(b.ru.questions).length),
      exam: { questions: Math.min(b.bank.examQuestions, b.bank.questions.length), minutes: b.bank.examMinutes, pass_mark: b.bank.passMark },
      topics: b.bank.topics.map((t) => ({ id: t.id, title: topicTitle(b, t.id, ctx.lang), questions: b.bank.questions.filter((q) => q.topic === t.id).length, theory: !!b.theory[t.id] })),
      app: `${ctx.origin}/?screen=${b.link}`,
    }))),
  tool('get_questions', 'Get practice questions', 'Random practice questions of a level, of one topic or difficulty when given, without the answers.',
    { level: LEVEL, topic: { type: 'string', description: 'Topic id, to practise one topic.' }, difficulty: { type: 'integer', enum: [1, 2, 3], description: '1 easy, 2 medium, 3 hard.' },
      count: { type: 'integer', minimum: 1, maximum: 20, description: 'How many (default 5).' }, text_only: { type: 'boolean', description: 'Only questions without a drawing, for when images cannot be shown.' }, exclude: EXCLUDE, lang: LANG },
    ['level'], (a, ctx) => {
      const b = levelOf(a.level), topic = a.topic == null ? null : topicOf(b, a.topic);
      need(a.difficulty == null || [1, 2, 3].includes(a.difficulty), 'difficulty is 1, 2 or 3.');
      const ids = b.bank.questions.filter((q) => (!topic || q.topic === topic) && (!a.difficulty || q.difficulty === a.difficulty) && !(a.text_only && q.figure && q.figure.type !== 'card')).map((q) => q.id);
      return { level: b.id, matching: ids.length, questions: pick(ids, countOf(a.count, 5, 20), a.exclude).map((id) => show(id, ctx)) };
    }),
  tool('check_answer', 'Check an answer', 'Whether an option of a question is right: the right option, the one-line note that names the rule, and the theory section that explains it.',
    { question_id: QID, option: { type: 'string', enum: [...ABCD], description: 'The option chosen: A, B, C or D.' }, lang: LANG },
    ['question_id', 'option'], (a, ctx) => {
      const q = show(questionOf(a.question_id), ctx, true), i = optionOf(a.option);
      return { question_id: q.id, correct: ABCD[i] === q.answer, chosen: ABCD[i], answer: q.answer, answer_text: q.answer_text, why: q.why, reference: q.reference, theory: q.theory };
    }),
  tool('search_questions', 'Search questions', 'Questions whose text, options, rule reference or topic have the words (e.g. "cardinal mark", "MAYDAY"), without the answers.',
    { query: { type: 'string', description: 'Words to look for; all of them must be there.' }, level: LEVEL, count: { type: 'integer', minimum: 1, maximum: 20, description: 'How many (default 10).' }, lang: LANG },
    ['query'], (a, ctx) => {
      const level = a.level == null ? null : levelOf(a.level).id;
      return { questions: find(questionHay(ctx.lang), termsOf(a.query), level, countOf(a.count, 10, 20)).map((r) => show(r.id, ctx)) };
    }),
  tool('start_mock_exam', 'Start a mock exam', 'A mock exam of a level: the exam\'s number of questions spread evenly over all topics, with the time allowed and the pass mark, without the answers.',
    { level: LEVEL, lang: LANG }, ['level'], (a, ctx) => {
      const b = levelOf(a.level), n = Math.min(b.bank.examQuestions, b.bank.questions.length);
      // round-robin over the topics: an even spread (buildExam in miniapp/app.js)
      const groups = shuffle(b.bank.topics.map((t) => shuffle(b.bank.questions.filter((q) => q.topic === t.id).map((q) => q.id)))), ids = [];
      while (ids.length < n && groups.some((g) => g.length)) for (const g of groups) if (g.length && ids.length < n) ids.push(g.pop());
      return { level: b.id, title: b.bank.title, minutes: b.bank.examMinutes, pass_mark: b.bank.passMark, questions: shuffle(ids).map((id) => show(id, ctx)) };
    }),
  tool('grade_exam', 'Grade a mock exam', 'The marks of a finished mock exam: the score, pass or fail, the result per topic, every mistake with the right answer and its note, and the theory sections to read. A question with option null was not answered and counts as wrong.',
    { answers: { type: 'array', minItems: 1, maxItems: 100, description: 'One item per question of the exam.', items: { type: 'object', properties: { question_id: QID, option: { type: ['string', 'null'], enum: [...ABCD, null], description: 'A, B, C, D, or null when not answered.' } }, required: ['question_id'], additionalProperties: false } }, lang: LANG },
    ['answers'], (a, ctx) => {
      need(Array.isArray(a.answers) && a.answers.length >= 1 && a.answers.length <= 100, 'answers is a list of 1 to 100 items: { question_id, option }.');
      const seen = new Set(), marked = a.answers.map((x) => {
        const id = questionOf(x && x.question_id);
        need(!seen.has(id), `Question ${id} is in the answers twice.`);
        seen.add(id);
        return { id, pick: x.option == null ? null : optionOf(x.option) };
      });
      const b = byId[marked[0].id].b;
      need(marked.every((m) => byId[m.id].b === b), 'The answers are from more than one level; grade one exam at a time.');
      const wrong = marked.filter((m) => m.pick !== byId[m.id].q.answer), correct = marked.length - wrong.length, pct = Math.round((correct / marked.length) * 100);
      const topics = {};
      for (const m of marked) { const t = (topics[byId[m.id].q.topic] ||= { topic: byId[m.id].q.topic, title: topicTitle(b, byId[m.id].q.topic, ctx.lang), correct: 0, total: 0 }); t.total++; if (!wrong.includes(m)) t.correct++; }
      return { level: b.id, total: marked.length, correct, percent: pct, pass_mark: b.bank.passMark, passed: pct >= b.bank.passMark, topics: Object.values(topics),
        mistakes: wrong.map((m) => { const q = show(m.id, ctx, true); return { question_id: q.id, question: q.question, chosen: m.pick == null ? null : ABCD[m.pick], answer: q.answer, answer_text: q.answer_text, why: q.why, reference: q.reference }; }),
        read: reading(wrong.map((m) => m.id), ctx) };
    }),
  tool('question_of_the_day', 'Question of the day', 'Today\'s question, the same one the Telegram bot @iyt_test_bot sends: one text question per day (UTC), for one level when a level is given, without the answer.',
    { level: LEVEL, lang: LANG }, [], (a, ctx) => {
      const day = new Date().toISOString().slice(0, 10), level = a.level == null ? null : levelOf(a.level).id;
      return { day, question: show(questionOfTheDay(day, level).id, ctx) };
    }),
  tool('list_theory', 'List theory articles', 'The theory articles: one per topic, each in sections. With a level, the sections of its articles; without, which topics of every level have an article. Some topics have no article yet.',
    { level: LEVEL, lang: LANG }, [], (a, ctx) => {
      const one = a.level == null ? null : levelOf(a.level);
      return (one ? [one] : banks).map((b) => ({ level: b.id, title: b.bank.title, articles: Object.keys(b.theory).map((topic) => {
        const { a: art, lang } = article(b, topic, ctx.lang);
        return { topic, title: topicTitle(b, topic, ctx.lang), language: lang, russian: !!b.theory[topic].ru, ...(one ? { sections: art.sections.map((s) => ({ section: s.id, kicker: s.kicker, title: s.title })) } : { sections: art.sections.length }) };
      }) }));
    }),
  tool('get_theory', 'Read a theory article', 'A theory article, or one section of it, as text: the rule, the reason, tables and links to the drawings. Study notes close to the syllabus, not official course text.',
    { level: LEVEL, topic: { type: 'string', description: 'Topic id, e.g. buoyage.' }, section: { type: 'string', description: 'Section id, to read one section only.' }, lang: LANG },
    ['level', 'topic'], (a, ctx) => {
      const b = levelOf(a.level), topic = withArticle(b, a.topic), ids = article(b, topic, ctx.lang).a.sections.map((s) => s.id);
      need(a.section == null || ids.includes(a.section), `Unknown section "${a.section}". Sections: ${ids.join(', ')}.`);
      return articleText(b, topic, ctx.lang, a.section, ctx);
    }),
  tool('search_theory', 'Search theory', 'The sections of the theory articles that have the words (e.g. "scope", "cardinal marks"), with an excerpt of each.',
    { query: { type: 'string', description: 'Words to look for; all of them must be there.' }, level: LEVEL, count: { type: 'integer', minimum: 1, maximum: 20, description: 'How many (default 8).' }, lang: LANG },
    ['query'], (a, ctx) => {
      const level = a.level == null ? null : levelOf(a.level).id;
      return { sections: find(theoryHay(ctx.lang), termsOf(a.query), level, countOf(a.count, 8, 20)).map(({ head, text, body, ...r }) => ({ ...r, excerpt: body.length > 240 ? `${body.slice(0, 240)}…` : body })) };
    }),
  tool('explain_question', 'Explain a question', 'A question with its answer, the note that names the rule and the full text of the theory section that explains it.',
    { question_id: QID, lang: LANG }, ['question_id'], (a, ctx) => {
      const q = show(questionOf(a.question_id), ctx, true), { b } = byId[q.id], s = q.theory, art = s && article(b, s.topic, ctx.lang);
      const figure = q.figure && (q.figure.url ? `[${ctx.lang === 'ru' ? 'Рисунок' : 'Drawing'}](${q.figure.url})` : [q.figure.title, ...(q.figure.lines || [])].filter(Boolean).join('\n'));
      return [`**${q.id}** · ${b.bank.title} · ${q.topic_title}`, q.question, figure, Object.entries(q.options).map(([k, o]) => `${k}. ${o}`).join('\n'),
        `**${ctx.lang === 'ru' ? 'Ответ' : 'Answer'}: ${q.answer}.** ${q.why}\n_${q.reference}_`,
        s ? sectionText(b, s.topic, art.a.sections.find((x) => x.id === s.section), art.lang, ctx) : 'No theory section covers this question yet.'].filter(Boolean).join('\n\n');
    }),
  tool('practice_section', 'Practise a theory section', 'The questions on what a theory section explains, at random, without the answers.',
    { level: LEVEL, topic: { type: 'string', description: 'Topic id, e.g. buoyage.' }, section: { type: 'string', description: 'Section id, e.g. cardinal.' }, count: { type: 'integer', minimum: 1, maximum: 20, description: 'How many (default 5).' }, exclude: EXCLUDE, lang: LANG },
    ['level', 'topic', 'section'], (a, ctx) => {
      const b = levelOf(a.level), topic = withArticle(b, a.topic), en = b.theory[topic].en.sections;
      const s = en.find((x) => x.id === a.section);
      need(s, `Unknown section "${a.section ?? ''}". Sections: ${en.map((x) => x.id).join(', ')}.`);
      const ids = b.bank.questions.filter((q) => q.topic === topic && (s.refs || []).includes(q.ref)).map((q) => q.id);
      return { level: b.id, topic, section: s.id, matching: ids.length, questions: pick(ids, countOf(a.count, 5, 20), a.exclude).map((id) => show(id, ctx)) };
    }),
  tool('get_figure', 'Get a drawing', 'The drawing of a question or of a theory section as SVG markup.',
    { figure: { type: 'string', description: 'A question id (bs-001), or a theory drawing as level/topic/section/number (bareboat-skipper/buoyage/lateral/1).' }, lang: LANG },
    ['figure'], (a, ctx) => { const svg = figureSvg(a.figure, ctx.lang); need(svg, `No drawing "${a.figure ?? ''}". Give a question id that has a figure, or level/topic/section/number from get_theory.`); return svg; }),
];
const byName = Object.fromEntries(TOOLS.map((t) => [t.name, t]));

// The drawing behind an address: a question id, or level/topic/section/n for the nth figure of a theory section.
function figureSvg(id, lang) {
  if (typeof id !== 'string') return null;
  if (byId[id]) { const { q, b } = byId[id], l = local(q, b, lang); return drawing(l.figure, { ru: !!l._tr }); }
  const [level, topic, section, n] = id.split('/'), b = byLevel[level], art = b && article(b, topic, lang);
  const s = art && art.a.sections.find((x) => x.id === section), f = s && figuresOf(s)[+n - 1];
  return f ? drawing(f.fig, { ru: art.lang === 'ru', view: f.view }) : null;
}

// ---------- the protocol ----------
const VERSIONS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']; // newest first
const INSTRUCTIONS = `Sailing Certification Test: practice questions and theory for sailing certification levels, the Racing Rules of Sailing and the charter check-in (${Object.keys(byId).length} questions). ` +
  'Call list_levels first. Ask questions one at a time with options A to D and never reveal the answer before the student chooses; check_answer gives the verdict, the note and the theory section to read. ' +
  'Most questions have a drawing: show figure.url to the student (an SVG image) because the question usually depends on it; if you describe the drawing instead, say what is seen without naming what the question asks. ' +
  'The questions and articles are study material, not official exam content. The app itself: ' + `${SITE} and the Telegram bot @iyt_test_bot.`;
const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, GET, OPTIONS', 'access-control-allow-headers': 'content-type, accept, authorization, mcp-protocol-version, mcp-session-id', 'access-control-max-age': '86400' };
const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store', ...CORS } });
const fail = (id, code, message) => ({ jsonrpc: '2.0', id: id ?? null, error: { code, message } });
const MAX_BODY = 200_000; // chars; the largest real call is a graded exam, a few KB

// One JSON-RPC message → its response, or null for a notification.
function handle(msg, ctx) {
  if (!msg || typeof msg !== 'object' || Array.isArray(msg) || msg.jsonrpc !== '2.0') return fail(null, -32600, 'Invalid request');
  if (typeof msg.method !== 'string') return 'id' in msg && !('result' in msg) && !('error' in msg) ? fail(msg.id, -32600, 'Invalid request') : null; // a response to us: nothing to do
  if (!('id' in msg)) return null; // a notification (notifications/initialized, …)
  const ok = (result) => ({ jsonrpc: '2.0', id: msg.id, result }), p = msg.params && typeof msg.params === 'object' ? msg.params : {};
  if (msg.method === 'initialize') return ok({
    protocolVersion: VERSIONS.includes(p.protocolVersion) ? p.protocolVersion : VERSIONS[0],
    capabilities: { tools: { listChanged: false } },
    serverInfo: { name: 'iyt-test', title: 'Sailing Certification Test', version: '1.0.1', websiteUrl: `${SITE}/mcp`, icons: [{ src: `${SITE}/icon.png`, mimeType: 'image/png', sizes: ['192x192'] }] },
    instructions: INSTRUCTIONS,
  });
  if (msg.method === 'ping') return ok({});
  if (msg.method === 'tools/list') return ok({ tools: TOOLS.map(({ run, ...t }) => t) });
  if (msg.method === 'tools/call') {
    const t = typeof p.name === 'string' && byName[p.name], a = p.arguments && typeof p.arguments === 'object' && !Array.isArray(p.arguments) ? p.arguments : {};
    if (!t) return fail(msg.id, -32602, `Unknown tool: ${p.name}`);
    try {
      need(a.lang == null || LANGS.includes(a.lang), 'lang is en or ru.');
      const out = t.run(a, { ...ctx, lang: a.lang || 'en' });
      return ok({ content: [{ type: 'text', text: typeof out === 'string' ? out : JSON.stringify(out) }] });
    } catch (e) {
      if (!(e instanceof Bad)) console.error('mcp', p.name, e);
      return ok({ content: [{ type: 'text', text: e instanceof Bad ? e.message : 'The tool failed; try again.' }], isError: true });
    }
  }
  return fail(msg.id, -32601, `Method not found: ${msg.method}`);
}

export async function POST(request) {
  let body;
  try { const text = await request.text(); if (text.length > MAX_BODY) return json(fail(null, -32600, 'Request too large'), 413); body = JSON.parse(text); }
  catch { return json(fail(null, -32700, 'Parse error'), 400); }
  const ctx = { origin: new URL(request.url).origin };
  const batch = Array.isArray(body);
  if (batch && !body.length) return json(fail(null, -32600, 'Invalid request'), 400);
  const out = (batch ? body : [body]).map((m) => handle(m, ctx)).filter(Boolean);
  if (!out.length) return new Response(null, { status: 202, headers: CORS }); // only notifications
  return json(batch ? out : out[0]);
}

export function GET(request) {
  const url = new URL(request.url), id = url.searchParams.get('figure');
  if (id != null) {
    const svg = figureSvg(id, url.searchParams.get('lang') === 'ru' ? 'ru' : 'en');
    if (!svg) return new Response('no such figure', { status: 404, headers: { 'content-type': 'text/plain', ...CORS } });
    return new Response(svg, { headers: { 'content-type': 'image/svg+xml; charset=utf-8', 'cache-control': 'public, max-age=3600', ...CORS } });
  }
  return new Response('Sailing Certification Test MCP server: POST JSON-RPC here (Model Context Protocol, Streamable HTTP).', { status: 405, headers: { allow: 'POST, OPTIONS', 'content-type': 'text/plain', ...CORS } });
}

export const OPTIONS = () => new Response(null, { status: 204, headers: CORS });
