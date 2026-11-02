/* IYT Test — Telegram mini app.
   Screens follow docs/design/flows.html (A1–A9 practice, B1–B5 mock exam, C1–C2 progress and profile); C4 Students
   (every student's results, api/admin.mjs) opens from the profile for the admins only.
   Banks are read from Supabase (fetchBank), with the static JSON files as fallback; progress lives on the device
   (localStorage + Telegram CloudStorage) and, inside Telegram, on the server (serverSave → api/progress.mjs), so the
   same code also runs in a plain browser for testing.
   Levels: every level with an `id` in LEVELS has a bank (bank() in the database, or data/<id>.json); all of them load at start (the home screen
   shows mastery for each), the one picked last (S.set.level) is the current level the other screens work on.
   Languages: English and Russian. Interface strings are in STR below; question text comes from the bank plus an
   optional overlay data/<level>.<lang>.json (see data/i18n.py) — questions it does not cover stay in English.
   Globals from the design files: rycIcon (icons.js), svg / paintIcons (test-icons.js), figSvg / FIG_TEXT (figures.js). */
'use strict';

const TG = window.Telegram && window.Telegram.WebApp;
const IN_TG = !!(TG && TG.initData);
const tgv = (v) => IN_TG && TG.isVersionAtLeast(v);
// Telegram's own MainButton + SecondaryButton (clients 7.10+) are square-cornered and cannot be styled, so every
// client gets the app's in-page bar with pill buttons instead; set to tgv('7.10') to go back to the native ones.
const NATIVE_BUTTONS = false;
const BOT_LINK = 'https://t.me/iyt_test_bot';
const $app = document.getElementById('app');

// IYT recreational levels in course-progression order (iytworld.com/students/recreational/iyt-course-progression).
// A level with an id has a bank (data/<id>.json, question ids <prefix>-nnn); the others show as coming.
const LEVELS = [
  { id: 'vhf-radio-operator', prefix: 'vhf', link: 'vhf', title: 'VHF Radio Operator' },
  { id: 'international-crew', prefix: 'ic', link: 'crew', title: 'International Crew' },
  { id: 'flotilla-skipper', prefix: 'fs', link: 'flotilla', title: 'Flotilla Skipper' },
  { id: 'bareboat-skipper', prefix: 'bs', link: 'bareboat', title: 'Bareboat Skipper' },
  { title: 'ICC', soon: 'planned' },
  { title: 'Yachtmaster Coastal', soon: 'soon' },
  { title: 'Yachtmaster Offshore', soon: 'soon2027' },
  { title: 'Yachtmaster Ocean', soon: 'planned' },
];
const DEFAULT_LEVEL = 'bareboat-skipper';
let LEVEL = LEVELS.find((l) => l.id === DEFAULT_LEVEL); // the current level
// Bareboat topics have no icon in the bank; the other banks carry topics[].icon.
const TOPIC_ICON = { terms: 'yacht', ropework: 'rope', safety: 'ring', colregs: 'compass', navigation: 'map', buoyage: 'buoy', weather: 'wind', anchoring: 'anchor', systems: 'wrench', emergency: 'radio' };
const LANGS = ['en', 'ru'];

const BASES = {};   // level id → the bank as loaded (English); a level whose bank failed to load is left out
let BASE = null;    // BASES of the current level
let BANK = null;    // the current level's bank in the current language
let OVERLAY = {};   // '<level>.<lang>' → overlay JSON (or null when there is none)
let Q = {}, TOPICS = [], TT = {}, TS = {};
let LANG = 'en';

/* ---------- interface strings ---------- */
// Plural forms: en [one, many]; ru [one, few, many] (1 вопрос, 2 вопроса, 5 вопросов).
const PL = {
  en: { question: ['question', 'questions'], topic: ['topic', 'topics'], mistake: ['mistake', 'mistakes'], exam: ['exam', 'exams'], day: ['day', 'days'], minute: ['minute', 'minutes'], student: ['student', 'students'] },
  ru: { question: ['вопрос', 'вопроса', 'вопросов'], topic: ['тема', 'темы', 'тем'], topicAcc: ['тему', 'темы', 'тем'], mistake: ['ошибка', 'ошибки', 'ошибок'], exam: ['экзамен', 'экзамена', 'экзаменов'], day: ['день', 'дня', 'дней'], minute: ['минута', 'минуты', 'минут'], student: ['ученик', 'ученика', 'учеников'] },
};
function word(n, key) {
  const f = (PL[LANG][key] || PL.en[key] || PL[LANG][key.replace(/Acc$/, '')]);
  if (LANG !== 'ru') return n === 1 ? f[0] : f[1];
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? f[0] : a >= 2 && a <= 4 && (b < 12 || b > 14) ? f[1] : f[2];
}
const pl = (n, key) => `${n} ${word(n, key)}`;

const STR = {
  en: {
    learn: 'Learn', exam: 'Exam', progress: 'Progress', profile: 'Profile', back: '‹ Back',
    soon: 'Coming soon', soon2027: 'Coming in 2027', planned: 'Planned',
    homeKicker: 'IYT theory · free', homeTitle: 'Pass your IYT&nbsp;exam',
    homeLead: 'Close-to-real questions for every certification level, with an explanation after each answer. Pick a level to continue.',
    streak: (n) => `${n}-day streak`,
    levelMeta: (t, q, ex) => `${pl(t, 'topic')} · ${pl(q, 'question')}${ex ? ' · ' + pl(ex, 'exam') + ' taken' : ''}`,
    examOpen: 'Mock exam in progress', continue: 'Continue',
    examLine: (a, n, left) => `${a} of ${n} answered · ${left} left`,
    mastered: 'mastered', halfway: 'halfway', halfwayN: (n) => `+${n} halfway`, moreLevels: 'More levels',
    levelText: (m, n, h, sn) => `${m} of ${n} mastered${h ? `, ${h} halfway there (right once)` : ''}. ${sn} seen so far.`,
    resumeK: 'Continue', resumeMeta: (sn, n, mis) => `${sn} of ${n} seen${mis ? ` · ${pl(mis, 'mistake')} to clear` : ''}`,
    practiseN: (n) => `Practise ${pl(n, 'question')}`, levelsK: 'Levels',
    mockExams: 'Mock exams', noExams: 'No mock exam yet — take one when you feel ready.', weakestTopics: 'Weakest topics', allTopics: 'All topics ›',
    themeDay: 'Day', themeNight: 'Night',
    weakest: (list) => ` Weakest: ${list}.`,
    levelFresh: 'A question counts as mastered once you answer it right twice in a row. Start with any topic.',
    practice: 'Practice', mockExam: 'Mock exam', mockShort: 'Mock exam',
    mistakesToClear: 'Mistakes to clear', toAnswerTwice: (n) => `${pl(n, 'question')} to answer right twice`, review: 'Review',
    topics: 'Topics', masteredTotal: 'mastered / total',
    questionOf: (i, n) => `Question ${i} of ${n}`, correct: 'Correct', notQuite: 'Not quite', why: 'Why',
    flag: 'Flag', flagged: 'Flagged', skip: 'Skip', check: 'Check', next: 'Next', finish: 'Finish', seeResults: 'See results',
    results: 'Results', heads: ['Excellent', 'Good session', 'Getting there', 'Keep going'],
    noMistakes: 'No mistakes this time.',
    score: 'score', time: 'time', byTopic: 'By topic', timeSpent: (s) => ` Time ${s}.`, statNew: 'first seen', statWrong: 'mistakes',
    spread: (w, k) => `${pl(w, 'mistake')} across ${pl(k, 'topic')} — no single weak spot yet.`,
    weakAll: (topic, r, n) => `${topic} is still your weak spot — ${r} of ${n} right across all your answers.`,
    seenRight: (s, r) => `seen ${s} · right ${r}`, whatNext: 'What next', nextMastered: (n) => `+${pl(n, 'question')} mastered`, nextMasteredMeta: 'Right twice in a row. They come back only now and then.',
    nextHalf: (n) => `${pl(n, 'question')} halfway`, nextHalfMeta: 'Right once. Answer right again in a later session to master.',
    nextWrong: (n) => `${pl(n, 'mistake')} come${n === 1 ? 's' : ''} back first`, nextWrongMeta: 'Until you answer right twice in a row.',
    practiseTopic: (t) => `Practise ${t}`, practiseMore: 'Practise more', mistakesN: (n) => `Mistakes · ${n}`,
    mistakesTitle: 'Mistakes', thisSession: 'This session', allMistakes: 'All mistakes', reviewTitle: 'Review mistakes',
    notAnswered: 'Not answered', nothingToReview: 'Nothing to review — no mistakes here.', practiseThese: 'Practise these again',
    examLead: (n) => `Like the real one: random questions from all ${n} topics, a timer, and the answers only at the end.`,
    questionsW: (n) => word(n, 'question'), minutesW: (n) => word(n, 'minute'), toPass: 'to pass', inProgress: 'In progress',
    rules: [['Answer in any order', 'Flag a question and come back to it from the overview grid.'],
      ['No explanations until you submit', 'Afterwards every mistake shows the right answer and why.'],
      ['Leaving pauses the timer', 'Close the app and the exam waits for you, up to 24 hours.']],
    lastAttempts: 'Last attempts', passedW: 'passed', notPassedW: 'not passed',
    examDefaults: 'Exam size, time and pass mark are app defaults, not confirmed IYT figures.',
    startExam: 'Start the exam', continueExam: 'Continue the exam', startOver: 'Start over',
    confirmRestart: 'Start a new exam? The one in progress will be dropped.',
    nOf: (i, n) => `${i} of ${n}`, nextArrow: 'Next ›', finishDots: 'Finish…', prevArrow: '‹ Previous', allQuestions: 'All questions',
    overview: 'Overview', answeredLeft: (a, l) => `${a} answered · ${l} left`, answered: 'Answered', notYet: 'Not yet',
    submitExam: 'Submit exam', submitHint: (l) => `Submitting with ${l} unanswered counts them as wrong.`, allAnswered: 'All answered — submit when you are ready.',
    confirmSubmit: (l) => `${pl(l, 'question')} unanswered will count as wrong. Submit the exam?`,
    result: 'Result', noResult: 'No exam result yet.', passed: 'Passed', notYetPass: (m) => `Not yet · ${m}% to pass`, okOf: (a, n) => `${a} of ${n}`,
    readyForExam: 'Ready for the&nbsp;exam', timeUsed: (t, m) => `Time used ${t} of ${m}:00. `,
    weakUnder: (w, m) => `${pl(w, 'topic')} under ${m}% — worth one more look.`, allAbove: (m) => `Every topic at ${m}% or more.`,
    closeShort: (w) => `Close — ${pl(w, 'topic')} short`, notPassedHead: 'Not passed this time',
    leftUnanswered: (n, auto) => `${pl(n, 'question')} ${n === 1 ? 'was' : 'were'} left unanswered${auto ? ' when the time ran out' : ''}. `,
    costMost: (list) => `${list} cost you the most points.`, workFirst: 'Work on these first', fine: 'Fine',
    backToLevel: 'Back to the level', practiseWeak: (w) => `Practise the ${pl(w, 'topic')}`.replace('topic', 'weak topic'), practise: 'Practise', share: 'Share',
    reviewN: (n) => `Review ${pl(n, 'mistake')}`,
    shareText: (p, lv) => `I scored ${p}% on the IYT ${lv} mock exam — practice questions for IYT levels:`, copied: 'Copied to the clipboard',
    thisWeek: 'This week', answeredW: 'answered', dayStreak: 'day streak', masteryByTopic: 'Mastery by topic', practiseWeakest: 'Practise weakest ›',
    misMeta: (n) => `${pl(n, 'question')} answered wrong and not yet mastered`, noneNow: 'None right now',
    flaggedQ: 'Flagged questions', flagHint: 'Flag a question to keep it here',
    guest: 'Guest', syncedTg: 'progress synced with Telegram', savedBrowser: 'Progress is saved in this browser',
    currentLevel: 'Current level', language: 'Language', theme: 'Theme', auto: 'Auto',
    daily: 'Question of the day', dailyMeta: 'Every morning in the chat with the bot', dailyAccess: 'Allow the bot to message you to get the question',
    shuffle: 'Shuffle options', shuffleMeta: 'Different order each time',
    explain: 'Explain after each answer', explainMeta: 'Off = exam style, results at the end',
    reset: 'Reset progress', resetMeta: 'Mastery, mistakes, streak and exams', resetBtn: 'Reset',
    confirmReset: 'Reset all progress? Mastery, mistakes, streak and exam history will be cleared.', resetDone: 'Progress reset',
    disclaimer: (v) => `Questions are written for study and are not official IYT exam content. Bank version ${v}.`, partEnglish: '', loading: 'Loading…',
    whatToPractise: 'What to practise?', all: 'All', none: 'None', weakPre: 'Weak topics are preselected. ', tapToggle: 'Tap to add or remove.',
    questionsK: 'Questions', allN: (n) => `All ${n}`, mistakesOnly: 'Mistakes only', showAnswer: 'Show the answer after each question',
    start: (n) => `Start · ${pl(n, 'question')}`, pickTopic: 'Pick a topic',
    noQuestions: 'No questions to practise', unflagged: 'Removed from flagged', flaggedToast: 'Flagged — find it in Progress',
    confirmQuit: 'Quit this session? Your answers so far are kept.',
    error: 'Something went wrong', bankError: (s) => `Could not load the question bank (${s})`,
    days: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'], locale: 'en-GB',
    // admin: students' results
    students: 'Students', studentsMeta: 'Results of everyone who uses the app', studentsFail: 'Could not load the results', studentsEmpty: 'Nobody has opened the app yet',
    studentsW: (n) => word(n, 'student'), activeWeek: 'active this week', examsTaken: (n) => word(n, 'exam') + ' taken', answeredN: (n) => `${n} answered`,
    noProgress: 'No answers yet', lastActive: 'Last active', joined: 'Joined', dailyOn: 'Question of the day on', dailyOff: 'Question of the day off',
    noExamsAdmin: 'No mock exam yet', reload: 'Reload', sortProgress: 'Progress', sortName: 'Name', sortJoined: 'Date joined',
  },
  ru: {
    learn: 'Учёба', exam: 'Экзамен', progress: 'Прогресс', profile: 'Профиль', back: '‹ Назад',
    soon: 'Скоро', soon2027: 'В 2027 году', planned: 'В планах',
    homeKicker: 'Теория IYT · бесплатно', homeTitle: 'Сдайте экзамен&nbsp;IYT',
    homeLead: 'Вопросы, близкие к настоящему экзамену, для каждого уровня — с пояснением после каждого ответа. Выберите уровень.',
    streak: (n) => `${pl(n, 'day')} подряд`,
    levelMeta: (t, q, ex) => `${pl(t, 'topic')} · ${pl(q, 'question')}${ex ? ' · ' + pl(ex, 'exam') : ''}`,
    examOpen: 'Пробный экзамен не закончен', continue: 'Продолжить',
    examLine: (a, n, left) => `отвечено ${a} из ${n} · осталось ${left}`,
    mastered: 'освоено', halfway: 'на полпути', halfwayN: (n) => `+${n} на полпути`, moreLevels: 'Другие уровни',
    levelText: (m, n, h, sn) => `Освоено ${m} из ${n}${h ? `, на полпути ${h} (верно один раз)` : ''}. Уже видели: ${sn}.`,
    resumeK: 'Продолжить', resumeMeta: (sn, n, mis) => `Видели ${sn} из ${n}${mis ? ` · ошибок к разбору: ${mis}` : ''}`,
    practiseN: (n) => `Тренировка · ${pl(n, 'question')}`, levelsK: 'Уровни',
    mockExams: 'Пробные экзамены', noExams: 'Пробных экзаменов ещё не было — попробуйте, когда будете готовы.', weakestTopics: 'Самые слабые темы', allTopics: 'Все темы ›',
    themeDay: 'День', themeNight: 'Ночь',
    weakest: (list) => ` Слабее всего: ${list}.`,
    levelFresh: 'Вопрос считается освоенным, когда вы дважды подряд отвечаете на него верно. Начните с любой темы.',
    practice: 'Тренировка', mockExam: 'Пробный экзамен', mockShort: 'Экзамен',
    mistakesToClear: 'Ошибки к разбору', toAnswerTwice: (n) => `${pl(n, 'question')} — ответьте верно дважды`, review: 'Разобрать',
    topics: 'Темы', masteredTotal: 'освоено / всего',
    questionOf: (i, n) => `Вопрос ${i} из ${n}`, correct: 'Верно', notQuite: 'Неверно', why: 'Почему',
    flag: 'Отметить', flagged: 'Отмечен', skip: 'Пропустить', check: 'Проверить', next: 'Далее', finish: 'Закончить', seeResults: 'Результаты',
    results: 'Результаты', heads: ['Отлично', 'Хорошая тренировка', 'Почти получилось', 'Продолжайте'],
    noMistakes: 'Ни одной ошибки.',
    score: 'результат', time: 'время', byTopic: 'По темам', timeSpent: (s) => ` Время ${s}.`, statNew: 'впервые', statWrong: 'ошибок',
    spread: (w, k) => `Ошибок: ${w}, в разных темах (${k}) — явно слабой темы пока нет.`,
    weakAll: (topic, r, n) => `Слабое место — тема «${topic}»: верно ${r} из ${n} по всем вашим ответам.`,
    seenRight: (s, r) => `видели ${s} · верно ${r}`, whatNext: 'Что дальше', nextMastered: (n) => `Освоено: +${pl(n, 'question')}`, nextMasteredMeta: 'Верно дважды подряд. Будут попадаться лишь изредка.',
    nextHalf: (n) => `На полпути: ${pl(n, 'question')}`, nextHalfMeta: 'Верно один раз. Ответьте верно ещё раз в следующих тренировках — и вопрос освоен.',
    nextWrong: (n) => `Первыми вернутся ошибки: ${n}`, nextWrongMeta: 'Пока не ответите верно дважды подряд.',
    practiseTopic: (t) => `Тренировать: ${t}`, practiseMore: 'Ещё тренировка', mistakesN: (n) => `Ошибки · ${n}`,
    mistakesTitle: 'Ошибки', thisSession: 'Эта тренировка', allMistakes: 'Все ошибки', reviewTitle: 'Разбор ошибок',
    notAnswered: 'Нет ответа', nothingToReview: 'Разбирать нечего — ошибок нет.', practiseThese: 'Повторить эти вопросы',
    examLead: (n) => `Как настоящий: случайные вопросы из всех ${n} тем, таймер и ответы только в конце.`,
    questionsW: (n) => word(n, 'question'), minutesW: (n) => word(n, 'minute'), toPass: 'для сдачи', inProgress: 'Не закончен',
    rules: [['Отвечайте в любом порядке', 'Отметьте вопрос и вернитесь к нему из общей сетки.'],
      ['Пояснения — только после сдачи', 'Потом у каждой ошибки будет верный ответ и пояснение.'],
      ['Выход ставит таймер на паузу', 'Закройте приложение — экзамен подождёт до 24 часов.']],
    lastAttempts: 'Последние попытки', passedW: 'сдан', notPassedW: 'не сдан',
    examDefaults: 'Число вопросов, время и проходной балл — настройки приложения, а не подтверждённые данные IYT.',
    startExam: 'Начать экзамен', continueExam: 'Продолжить экзамен', startOver: 'Начать заново',
    confirmRestart: 'Начать новый экзамен? Текущий будет сброшен.',
    nOf: (i, n) => `${i} из ${n}`, nextArrow: 'Далее ›', finishDots: 'Завершить…', prevArrow: '‹ Назад', allQuestions: 'Все вопросы',
    overview: 'Обзор', answeredLeft: (a, l) => `Отвечено ${a} · осталось ${l}`, answered: 'Отвечен', notYet: 'Без ответа',
    submitExam: 'Сдать экзамен', submitHint: (l) => `Вопросы без ответа (${l}) будут засчитаны как неверные.`, allAnswered: 'Все вопросы отвечены — сдавайте, когда будете готовы.',
    confirmSubmit: (l) => `Без ответа: ${l}. Они будут засчитаны как неверные. Сдать экзамен?`,
    result: 'Результат', noResult: 'Результатов экзамена пока нет.', passed: 'Сдано', notYetPass: (m) => `Пока нет · нужно ${m}%`, okOf: (a, n) => `${a} из ${n}`,
    readyForExam: 'Готовы к&nbsp;экзамену', timeUsed: (t, m) => `Время: ${t} из ${m}:00. `,
    weakUnder: (w, m) => `Тем ниже ${m}%: ${w} — стоит повторить.`, allAbove: (m) => `Все темы — ${m}% и выше.`,
    closeShort: (w) => `Почти — подтяните ${pl(w, 'topicAcc')}`, notPassedHead: 'В этот раз не сдано',
    leftUnanswered: (n, auto) => `Без ответа осталось вопросов: ${n}${auto ? ' — время вышло' : ''}. `,
    costMost: (list) => `Больше всего баллов потеряно в темах: ${list}.`, workFirst: 'Сначала подтяните', fine: 'В порядке',
    backToLevel: 'К уровню', practiseWeak: (w) => `Тренировать слабые темы (${w})`, practise: 'Тренировка', share: 'Поделиться',
    reviewN: (n) => `Разобрать ошибки (${n})`,
    shareText: (p, lv) => `Мой результат на пробном экзамене IYT ${lv} — ${p}%. Вопросы для подготовки к IYT:`, copied: 'Скопировано',
    thisWeek: 'Эта неделя', answeredW: 'отвечено', dayStreak: (n) => `${word(n, 'day')} подряд`, masteryByTopic: 'Освоение по темам', practiseWeakest: 'Тренировать слабые ›',
    misMeta: (n) => `Вопросов с ошибкой, ещё не освоенных: ${n}`, noneNow: 'Сейчас нет',
    flaggedQ: 'Отмеченные вопросы', flagHint: 'Отметьте вопрос — он появится здесь',
    guest: 'Гость', syncedTg: 'прогресс сохраняется в Telegram', savedBrowser: 'Прогресс сохраняется в этом браузере',
    currentLevel: 'Текущий уровень', language: 'Язык', theme: 'Тема', auto: 'Авто',
    daily: 'Вопрос дня', dailyMeta: 'Каждое утро в чате с ботом', dailyAccess: 'Разрешите боту писать вам, чтобы получать вопрос',
    shuffle: 'Перемешивать варианты', shuffleMeta: 'Каждый раз в другом порядке',
    explain: 'Пояснение после ответа', explainMeta: 'Выкл. — как на экзамене, итог в конце',
    reset: 'Сбросить прогресс', resetMeta: 'Освоение, ошибки, серия дней и экзамены', resetBtn: 'Сбросить',
    confirmReset: 'Сбросить весь прогресс? Освоение, ошибки, серия дней и история экзаменов будут удалены.', resetDone: 'Прогресс сброшен',
    disclaimer: (v) => `Вопросы написаны для подготовки и не являются официальными вопросами экзамена IYT. Версия банка ${v}.`,
    loading: 'Загрузка…',
    partEnglish: ' Перевод вопросов готовится — пока часть из них на английском.',
    whatToPractise: 'Что тренируем?', all: 'Все', none: 'Снять все', weakPre: 'Слабые темы уже выбраны. ', tapToggle: 'Нажмите, чтобы добавить или убрать.',
    questionsK: 'Вопросы', allN: (n) => `Все ${n}`, mistakesOnly: 'Только ошибки', showAnswer: 'Показывать ответ после каждого вопроса',
    start: (n) => `Начать · ${pl(n, 'question')}`, pickTopic: 'Выберите тему',
    noQuestions: 'Нет вопросов для тренировки', unflagged: 'Отметка снята', flaggedToast: 'Отмечен — он в разделе «Прогресс»',
    confirmQuit: 'Выйти из тренировки? Ответы сохранятся.',
    error: 'Что-то пошло не так', bankError: (s) => `Не удалось загрузить вопросы (${s})`,
    days: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'], locale: 'ru-RU',
    // admin: students' results
    students: 'Ученики', studentsMeta: 'Результаты всех, кто пользуется приложением', studentsFail: 'Не удалось загрузить результаты', studentsEmpty: 'Приложение ещё никто не открывал',
    studentsW: (n) => word(n, 'student'), activeWeek: 'активны за неделю', examsTaken: (n) => word(n, 'exam') + ' пройдено', answeredN: (n) => `${n} отвечено`,
    noProgress: 'Ответов ещё нет', lastActive: 'Последняя активность', joined: 'В приложении с', dailyOn: 'Вопрос дня включён', dailyOff: 'Вопрос дня выключен',
    noExamsAdmin: 'Экзаменов ещё не было', reload: 'Обновить', sortProgress: 'Прогресс', sortName: 'Имя', sortJoined: 'Дата',
  },
};
const t = (k, ...a) => { const v = STR[LANG][k] ?? STR.en[k]; return typeof v === 'function' ? v(...a) : v; };

// Built-in labels drawn by figures.js. Used only on questions that are themselves translated, so a figure never
// mixes languages.
const FIG_RU = {
  wind: 'ветер', N: 'N', You: 'Вы', Other: 'Другое судно', 'Night · lights seen ahead': 'Ночь · огни по курсу',
  'Light at night': 'Огонь ночью', 'N (true)': 'N ист.', MN: 'N магн.', Variation: 'Склонение', Deviation: 'Девиация',
  'True course': 'ИК', W: 'W', E: 'E', 'Depths in metres below chart datum': 'Глубины в метрах от нуля глубин',
  Anchoring: 'Якорная стоянка', 'Northern hemisphere': 'Северное полушарие',
};

/* ---------- small helpers ---------- */
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad = (n) => String(n).padStart(2, '0');
const dkey = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const fmt = (ms) => { const s = Math.max(0, Math.round(ms / 1000)); return `${Math.floor(s / 60)}:${pad(s % 60)}`; };
const short = (id) => TS[id] || TT[id].split(' (')[0].split(' & ')[0];
const lower = (s) => (LANG === 'en' && /^[A-Z][a-z]/.test(s) ? s[0].toLowerCase() + s.slice(1) : s);
const day = (at) => new Date(at).toLocaleDateString(t('locale'), { day: 'numeric', month: 'short' });
function figHtml(q) {
  if (!q.figure) return '';
  for (const k in FIG_TEXT) delete FIG_TEXT[k];
  if (q._tr && LANG === 'ru') Object.assign(FIG_TEXT, FIG_RU);
  const f = q.figure;
  if (f.type === 'card') return `<div class="figcard">${f.tag ? `<span class="figtag">${esc(f.tag)}</span>` : ''}<span class="kicker">${esc(f.title || '')}</span>` +
    `<ul>${(f.lines || []).map((l) => `<li>${esc(l)}</li>`).join('')}</ul></div>`;
  return `<div class="fig">${figSvg(q.figure)}</div>`;
}

function hap(kind) {
  if (!tgv('6.1')) return;
  try { kind === 'sel' ? TG.HapticFeedback.selectionChanged() : TG.HapticFeedback.notificationOccurred(kind); } catch (e) {}
}
const confirmBox = (msg) => new Promise((res) => (tgv('6.2') ? TG.showConfirm(msg, res) : res(window.confirm(msg))));
function toast(text) {
  $app.querySelector('.toast')?.remove();
  $app.insertAdjacentHTML('beforeend', `<div class="toast" role="status" aria-live="polite">${esc(text)}</div>`);
  const el = $app.querySelector('.toast');
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 200); }, 1400);
}

/* ---------- state: mastery per question, activity per day, exams; saved locally and to CloudStorage ---------- */
// q[id] = [last two results as '0'/'1', wrong count]. Mastered = right twice in a row (docs/data-model.md).
const KEY = 'iyt-test-state-v1';
const fresh = () => ({ v: 1, ts: 0, q: {}, days: {}, total: 0, flags: [], exams: [], exam: null, held: {}, last: null, set: { theme: 'auto', shuffle: true, feedback: true, lang: '', level: '' } });
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
  if (cloud) serverSave();
}

// Server copy of the progress, inside Telegram only (api/progress.mjs → Supabase public.progress): the newest state
// wins, as with CloudStorage, and each answer since the last sync goes to the answers log. Unsent answers wait in
// localStorage. serverOn turns off when the server cannot help (no database, launch data refused).
const OUTBOX = 'iyt-test-outbox';
let outbox = [];
try { outbox = JSON.parse(localStorage.getItem(OUTBOX) || '[]'); } catch (e) {}
const keepOutbox = () => { try { localStorage.setItem(OUTBOX, JSON.stringify(outbox)); } catch (e) {} };
let serverOn = IN_TG, serverTimer = null;
function progressApi(body, keepalive = false) {
  return fetch('/api/progress', { method: 'POST', keepalive, body, headers: { 'x-telegram-init-data': TG.initData, 'content-type': 'application/json' } })
    .then((r) => { if (r.status === 403 || r.status === 503) serverOn = false; return r.ok ? r.json() : Promise.reject(new Error(r.status)); });
}
function serverSave(now = false) {
  if (!serverOn) return;
  clearTimeout(serverTimer);
  if (!now) { serverTimer = setTimeout(() => serverSave(true), 3000); return; }
  const answers = outbox.slice(0, 500), body = JSON.stringify({ state: S, answers });
  progressApi(body, body.length < 60000) // keepalive lets the last save finish while the app closes (64 KB cap)
    .then(() => { outbox = outbox.slice(answers.length); keepOutbox(); if (outbox.length) serverSave(); })
    .catch(() => {});
}
// The server's copy, or null (outside Telegram, no database, or no answer within 5 s — the app starts anyway).
function serverLoad() {
  if (!serverOn) return Promise.resolve(null);
  return Promise.race([progressApi('{}').catch(() => null), new Promise((res) => setTimeout(() => res(null), 5000))]);
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
const halfway = (id) => !mastered(id) && rec(id)[0].endsWith('1');
function record(id, ok, mode = 'practice', option = null) {
  const [h, w] = rec(id);
  S.q[id] = [(h + (ok ? '1' : '0')).slice(-2), w + (ok ? 0 : 1)];
  const d = dkey();
  S.days[d] = (S.days[d] || 0) + 1;
  S.total++;
  if (serverOn) { outbox.push({ q: id, ok, o: option, m: mode, at: new Date().toISOString() }); outbox = outbox.slice(-5000); keepOutbox(); }
}
let BY_TOPIC = {};
const topicIds = (tp) => BY_TOPIC[tp] || [];
const topicPct = (tp) => { const ids = topicIds(tp); return Math.round((ids.filter(mastered).length / ids.length) * 100); };
const levelPct = (b = BANK) => Math.round((b.questions.filter((q) => mastered(q.id)).length / b.questions.length) * 100);
const seenPct = (b = BANK) => Math.round((b.questions.filter((q) => touched(q.id)).length / b.questions.length) * 100);
// mastery ring; a lighter second step shows questions seen but not yet mastered, so early sessions show up
const ring = (lp, sp, cls = '', inner = `<b>${lp}%</b>`) => `<span class="ring seen${cls}" style="--v:${lp};--s:${Math.max(lp, sp)}">${inner}</span>`;
const ready = () => LEVELS.filter((l) => l.id && BASES[l.id]);
// Exams are kept per level; records from before levels existed have no lv and are Bareboat Skipper's.
const lvOf = (x) => (x && x.lv) || DEFAULT_LEVEL;
const myExams = (id = LEVEL.id) => S.exams.filter((e) => lvOf(e) === id);
const allMistakes = () => BANK.questions.filter((q) => isMistake(q.id)).map((q) => q.id);
// accuracy of the last attempt on every touched question of a topic (null when untouched)
const topicAcc = (tp) => { const ids = topicIds(tp).filter(touched); return ids.length ? ids.filter((id) => rec(id)[0].endsWith('1')).length / ids.length : null; };
const topicSeen = (tp) => topicIds(tp).filter(touched).length;
// weak = under 60 % right on the last attempt, judged only once a topic has 5 answered questions
const weakTopics = () => TOPICS.filter((tp) => { const a = topicAcc(tp.id); return a != null && a < 0.6 && topicSeen(tp.id) >= 5; }).map((tp) => tp.id);
let WEAK = new Set();
function streak() {
  const d = new Date();
  if (!S.days[dkey(d)]) d.setDate(d.getDate() - 1); // today not practised yet: the streak is still alive
  let n = 0;
  while (S.days[dkey(d)]) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function prune() { const c = new Date(); c.setDate(c.getDate() - 90); const k = dkey(c); for (const d in S.days) if (d < k) delete S.days[d]; }

/* ---------- language: interface strings + the bank overlay ---------- */
// The language follows the user's Telegram app (initData user.language_code; the browser outside Telegram) until
// they pick one with the EN/RU switch in the profile: that choice is saved with the progress and wins from then on,
// on every device. The default is the bot's rule (bot/core.mjs RU).
const TG_LANG = (IN_TG && TG.initDataUnsafe?.user?.language_code) || '';
function pickLang() {
  if (LANGS.includes(S.set.lang)) return S.set.lang;
  return /^(ru|uk|be|kk)\b/i.test(TG_LANG || navigator.language || '') ? 'ru' : 'en';
}
// Banks come from Supabase (docs/data-model.md: bank() and bank_overlay() return the same shape as the files);
// the JSON files shipped next to the app are the fallback when the database is slow, down or lacks the level.
// The publishable key only reads the catalogue.
const SUPABASE = { url: 'https://xpdhkahgvusuicynssxq.supabase.co', key: 'sb_publishable_WKUQdLYP62nam72_h4p5QA_Sz8nxD_Y' };
async function fetchBank(level, lang = 'en') {
  const fn = lang === 'en' ? `bank?p_level=${level}` : `bank_overlay?p_level=${level}&p_lang=${lang}`;
  try {
    const ctl = typeof AbortController === 'function' ? new AbortController() : null;
    const timer = ctl && setTimeout(() => ctl.abort(), 8000);
    const r = await fetch(`${SUPABASE.url}/rest/v1/rpc/${fn}`, { headers: { apikey: SUPABASE.key }, signal: ctl && ctl.signal });
    const b = r.ok ? await r.json() : null;
    clearTimeout(timer);
    if (b) return b;
  } catch (e) {}
  const r = await fetch(`data/${lang === 'en' ? level : `${level}.${lang}`}.json`, { cache: 'no-cache' });
  return r.ok ? r.json() : r.status;
}
async function loadOverlay(lang, lv = LEVEL.id) {
  const k = `${lv}.${lang}`;
  if (lang === 'en' || k in OVERLAY) return;
  try {
    const o = await fetchBank(lv, lang);
    OVERLAY[k] = o && o.questions ? o : null;
  } catch (e) { OVERLAY[k] = null; }
}
function setPath(obj, path, val) {
  const k = path.split('.');
  let o = obj;
  for (let i = 0; i < k.length - 1; i++) { o = o?.[k[i]]; if (o == null) return; }
  if (o != null) o[k[k.length - 1]] = val;
}
// Rebuilds BANK/Q/TOPICS in LANG. Option order never changes, so progress and exams keyed by option index stay valid.
function localise() {
  BASE = BASES[LEVEL.id];
  const ov = (LANG !== 'en' && OVERLAY[`${LEVEL.id}.${LANG}`]) || null;
  const tq = (ov && ov.questions) || {};
  const questions = BASE.questions.map((q) => {
    const tr = tq[q.id];
    if (!tr || !tr.q || (tr.options || []).length !== 4) return q;
    const figure = q.figure ? JSON.parse(JSON.stringify(q.figure)) : null;
    if (figure) for (const [p, v] of Object.entries(tr.figure || {})) setPath(figure, p, v);
    return { ...q, q: tr.q, options: tr.options, why: tr.why || q.why, ref: tr.ref || q.ref, figure, _tr: true };
  });
  BANK = { ...BASE, questions, topics: BASE.topics.map((tp) => ({ ...tp, title: (ov && ov.topics && ov.topics[tp.id]) || tp.title })) };
  BANK.translated = questions.filter((q) => q._tr).length;
  Q = {}; BY_TOPIC = {};
  questions.forEach((q) => { Q[q.id] = q; (BY_TOPIC[q.topic] = BY_TOPIC[q.topic] || []).push(q.id); });
  TOPICS = BANK.topics;
  TT = Object.fromEntries(TOPICS.map((tp) => [tp.id, tp.title]));
  TS = (ov && ov.short) || {};
  document.documentElement.lang = LANG;
}
async function setLang(lang) {
  LANG = lang;
  await loadOverlay(lang);
  localise();
}
// Makes another level current. An exam in progress is put aside and comes back when you return to its level.
async function setLevel(id) {
  const l = LEVELS.find((x) => x.id === id && BASES[x.id]);
  if (!l || l === LEVEL) return;
  stopTimer();
  LEVEL = l;
  S.set.level = id;
  swapExam();
  await loadOverlay(LANG);
  localise();
  expireExam();
  save();
}
// Keeps S.exam for the current level only; exams of other levels wait in S.held.
function swapExam() {
  S.held = S.held || {};
  if (S.exam && lvOf(S.exam) !== LEVEL.id) { S.held[lvOf(S.exam)] = S.exam; S.exam = null; }
  if (!S.exam && S.held[LEVEL.id]) { S.exam = S.held[LEVEL.id]; delete S.held[LEVEL.id]; }
}

/* ---------- navigation: a stack of views, one optional sheet on top ---------- */
let stack = [{ v: 'home' }];
let sheet = null;
let P = null; // the running practice session (memory only)
// The question-of-the-day switch lives on the server (api/settings.mjs, the same flag as the bot's /settings).
// undefined = not asked yet, null = unavailable (outside Telegram, no database, request failed) and the row is hidden.
let DAILY, ADMIN = false; // ADMIN: the server said this user may see every student's results (ADMINS in api/settings.mjs)
const settingsApi = (body) => fetch('/api/settings', {
  method: body ? 'POST' : 'GET', body: body && JSON.stringify(body),
  headers: { 'x-telegram-init-data': TG.initData, ...(body && { 'content-type': 'application/json' }) },
}).then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))));
function loadDaily() {
  if (!IN_TG || DAILY !== undefined) return;
  DAILY = null;
  settingsApi().then((j) => {
    if (typeof j.daily !== 'boolean') return;
    DAILY = j.daily; ADMIN = j.admin === true;
    if (cur().v === 'profile' && !sheet) render();
  }).catch(() => {});
}
// Admin: every student's results from api/admin.mjs. undefined = not asked, 'loading', null = failed, or the list.
let ADM;
function loadStudents(again) {
  if (ADM !== undefined && !again) return; // a failure stays on screen until Reload is tapped
  ADM = 'loading';
  fetch('/api/admin', { headers: { 'x-telegram-init-data': IN_TG ? TG.initData : '' } })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
    .then((j) => { ADM = Array.isArray(j.users) ? j.users : null; })
    .catch(() => { ADM = null; })
    .then(() => { if (cur().v === 'admin') render(true); if (ADM) loadPhotos(); });
}
// Students' Telegram photos, fetched one by one through api/admin.mjs (?photo=id) with the same launch data; a
// student with no photo the bot may see gets null and keeps their initials. Each photo is put into the page as it
// arrives, so the list does not re-render.
const PHOTOS = {};
let photoQueue = [];
function loadPhotos() {
  photoQueue = ADM.filter((u) => !(u.id in PHOTOS)).map((u) => u.id);
  for (let k = 0; k < 3; k++) nextPhoto();
}
function nextPhoto() {
  const id = photoQueue.shift();
  if (id == null) return;
  PHOTOS[id] = undefined;
  fetch(`/api/admin?photo=${id}`, { headers: { 'x-telegram-init-data': IN_TG ? TG.initData : '' } })
    .then((r) => (r.status === 200 ? r.blob() : null))
    .then((b) => { PHOTOS[id] = b ? URL.createObjectURL(b) : null; })
    .catch(() => { PHOTOS[id] = null; })
    .then(() => {
      if (PHOTOS[id]) $app.querySelectorAll(`[data-ava="${id}"]`).forEach((el) => { el.innerHTML = `<img src="${PHOTOS[id]}" alt="">`; });
      nextPhoto();
    });
}
const avatar = (u, cls, style = '') => `<span class="${cls}" data-ava="${u.id}" style="${style}">${PHOTOS[u.id] ? `<img src="${PHOTOS[u.id]}" alt="">` : esc(initials(studentName(u)))}</span>`;
let ADM_SORT = 'progress'; // 'progress' | 'name' | 'joined'
function sortedStudents() {
  const list = ADM.slice(), pct = (u) => { const L = studentLevel(u); return L ? L.pct : -1; };
  const plain = (u) => studentName(u).replace(/^@/, ''); // a username stands in for a missing name; sort it by its letters
  if (ADM_SORT === 'name') list.sort((a, b) => plain(a).localeCompare(plain(b), t('locale')));
  else if (ADM_SORT === 'joined') list.sort((a, b) => Date.parse(b.joined) - Date.parse(a.joined));
  else list.sort((a, b) => pct(b) - pct(a) || b.total - a.total || Date.parse(b.active) - Date.parse(a.active));
  return list;
}
// Grey shapes in the layout of what is loading (the boot skeleton of the home screen is in index.html).
const sk = (w, h, more = '') => `<span class="sk" style="width:${w};height:${h}${more}"></span>`;
function skeleton(kind) {
  if (kind === 'students') {
    const stat = `<div class="stat">${sk('40%', '22px')}${sk('70%', '10px')}</div>`;
    const row = `<div class="topic x3"><span class="ico sk"></span>${sk('55%', '15px', ';grid-column:2')}${sk('70%', '11px', ';grid-column:2')}<span class="n">${sk('44px', '16px', ';margin-left:auto')}${sk('64px', '11px', ';margin:4px 0 0 auto')}</span></div>`;
    return `<div aria-busy="true"><span class="sk-label">${t('loading')}</span><div class="stats">${stat.repeat(3)}</div><div class="topics" style="margin-top:16px">${row.repeat(5)}</div></div>`;
  }
  return '';
}
const levelOfPrefix = (p) => LEVELS.find((l) => l.prefix === p);
// A student's mastery of a level, in % of its bank; the level they work on, or the one they have seen most of.
function studentLevel(u) {
  const lv = (u.level && LEVELS.find((l) => l.id === u.level && BASES[l.id])) ||
    ready().slice().sort((a, b) => ((u.levels[b.prefix] || {}).seen || 0) - ((u.levels[a.prefix] || {}).seen || 0))[0];
  if (!lv || !BASES[lv.id]) return null;
  const n = BASES[lv.id].questions.length, L = u.levels[lv.prefix] || { mastered: 0, seen: 0, mistakes: 0 };
  return { lv, n, ...L, pct: Math.round((L.mastered / n) * 100), seenPct: Math.round((L.seen / n) * 100) };
}
const studentName = (u) => u.name || (u.username ? '@' + u.username : String(u.id));
const initials = (name) => name.replace(/^@/, '').split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();
async function toggleDaily(el) {
  if (typeof DAILY !== 'boolean') return;
  const on = !DAILY;
  // the bot can only message people who allowed it; Telegram asks once and remembers
  if (on && tgv('6.9') && !(await new Promise((res) => TG.requestWriteAccess(res)))) return toast(t('dailyAccess'));
  DAILY = on; hap('sel'); el?.classList.toggle('on', on); await new Promise((res) => setTimeout(res, 220)); render();
  try { DAILY = (await settingsApi({ daily: on })).daily; } catch (e) { DAILY = !on; toast(t('error')); }
  if (cur().v === 'profile') render();
}
let mainCb = null, secCb = null;
const cur = () => stack[stack.length - 1];

function go(v, p = {}) { stack.push({ v, ...p }); sheet = null; render(true); }
function replace(v, p = {}) { stack[stack.length - 1] = { v, ...p }; sheet = null; render(true); }
function tab(v) { stack = [{ v }]; sheet = null; P = null; enterTab = true; render(true); }
let enterTab = false; // the next render(true) is a tab switch: fade only, no stagger
// Closes the sheet with its exit animation, then rebuilds the screen without it.
function closeSheet() {
  const sh = $app.querySelector('.sheet');
  sheet = null;
  if (!sh) return render();
  sh.classList.add('out'); $app.querySelector('.scrim')?.classList.add('out');
  setTimeout(() => { if (!sheet) render(); }, 180);
}
async function back() {
  if (sheet) return closeSheet();
  const c = cur();
  if (c.v === 'question' && P && !P.done) {
    if (!(await confirmBox(t('confirmQuit')))) return;
    P = null;
  }
  if (c.v === 'exam') { stopTimer(); save(); }
  if (stack.length > 1) { stack.pop(); render(true); }
}

/* ---------- theme: day / night / auto (follows Telegram, or the system outside it) ---------- */
function isNight() {
  const th = S.set.theme;
  if (th !== 'auto') return th === 'night';
  return IN_TG ? TG.colorScheme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
}
function applyTheme() {
  const n = isNight();
  $app.classList.toggle('theme-night', n);
  document.documentElement.dataset.theme = n ? 'dark' : 'light';
  document.documentElement.style.colorScheme = n ? 'dark' : 'light';
  const meta = document.querySelector('meta[name=theme-color]'); if (meta) meta.content = n ? '#000000' : '#ffffff';
  if (tgv('6.9')) {
    const bg = n ? '#000000' : '#ffffff';
    try { TG.setHeaderColor(bg); TG.setBackgroundColor(bg); if (tgv('7.10')) TG.setBottomBarColor(bg); } catch (e) {}
  }
}
const tok = (name) => getComputedStyle($app).getPropertyValue(name).trim();
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
// A number that counts up to its value when its screen opens (data-count="82" data-suffix="%").
function countUp(el) {
  const to = +el.dataset.count, suffix = el.dataset.suffix || '', t0 = performance.now(), dur = 600;
  if (!(to > 0)) return;
  const step = (now) => {
    const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(to * e) + suffix;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ---------- rendering ---------- */
const NAV = [['home', 'book', 'learn'], ['examIntro', 'timer', 'exam'], ['progress', 'chart', 'progress'], ['profile', 'user', 'profile']];

function render(toTop) {
  if (cur().v === 'exam' && !S.exam) stack[stack.length - 1] = { v: 'examIntro' };
  const c = cur();
  WEAK = new Set(weakTopics());
  const V = VIEWS[c.v](c);
  const old = $app.querySelector('.scroll');
  const keep = !toTop && old ? old.scrollTop : 0;
  let h = '';
  if (!IN_TG) h += `<div class="tgh"><span>${stack.length > 1 || sheet ? `<button data-act="back">${t('back')}</button>` : ''}</span><b>${esc(V.title)}</b><span></span></div>`;
  const enter = toTop ? (enterTab ? ' in in-tab' : ' in') : ''; enterTab = false;
  h += `<div class="scroll wrap${enter}">${V.body}</div>`;
  if (V.nav && stack.length === 1) h += `<nav class="nav">${NAV.map(([v, i, k]) => `<a class="${v === V.nav ? 'on' : ''}" data-act="tab" data-v="${v}"${v === V.nav ? ' aria-current="page"' : ''}><span data-i="${i}" aria-hidden="true"></span>${t(k)}</a>`).join('')}</nav>`;
  const B = sheet ? {} : V;
  mainCb = B.main ? B.main.act : null;
  secCb = B.second ? B.second.act : null;
  if (!NATIVE_BUTTONS && (B.main || B.second)) {
    const b = (x, k, cls) => `<button class="b ${cls}${x.off ? ' off' : ''}" data-act="${k}">${x.icon ? `<span data-i="${x.icon}" data-s="18"></span>` : ''}<span class="t">${esc(x.text)}</span></button>`;
    const both = B.main && B.second;
    h += `<div class="tgmain wrap${enter}">` +
      (both && B.second.pos !== 'bottom' ? `<div class="row2">${b(B.second, 'second', 'b2')}${b(B.main, 'main', '')}</div>` :
        (B.main ? b(B.main, 'main', '') : '') + (B.second ? b(B.second, 'second', 'b2') : '')) + '</div>';
  }
  if (sheet) h += `<div class="scrim" data-act="back"></div><div class="sheet"><div class="grip"></div><div class="wrap stack g16">${SHEETS[sheet.v](sheet)}</div></div>`;
  $app.innerHTML = h;
  $app.querySelectorAll('[data-act]:not(button):not(.scrim)').forEach((el) => {
    if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
    if (!el.classList.contains('locked') && !el.classList.contains('off')) el.tabIndex = 0;
  });
  paintIcons($app);
  const sc = $app.querySelector('.scroll');
  if (keep) sc.scrollTop = keep;
  if (enter && !REDUCED) {
    // rows of a list rise one after another (--i is the row's place in its list, capped so long lists stay quick)
    const idx = new Map();
    $app.querySelectorAll('.in .lvl, .in .topic, .in .opt, .in .stat, .in .set, .in .att, .in .tbar, .in .step').forEach((el) => {
      const i = idx.get(el.parentElement) || 0; idx.set(el.parentElement, i + 1); el.style.setProperty('--i', Math.min(i, 8));
    });
    $app.querySelectorAll('.in [data-count]').forEach(countUp);
  }
  if (NATIVE_BUTTONS) nativeButtons(B);
  if (tgv('6.1')) (stack.length > 1 || sheet ? TG.BackButton.show() : TG.BackButton.hide());
  if (c.v === 'exam' && S.exam) { startTimer(); if (tgv('6.2')) TG.enableClosingConfirmation(); }
  else { stopTimer(); if (tgv('6.2')) TG.disableClosingConfirmation(); }
}

function nativeButtons(B) {
  const MB = TG.MainButton, SB = TG.SecondaryButton;
  if (B.main) {
    const off = !!B.main.off;
    MB.setParams({ text: B.main.text, color: off ? tok('--band') : tok('--accent-ink'), text_color: off ? tok('--muted') : tok('--on-accent'), is_active: !off, is_visible: true });
  } else MB.hide();
  if (B.second) SB.setParams({ text: B.second.text, color: tok('--band'), text_color: tok('--accent-ink'), is_active: true, is_visible: true, position: B.second.pos || 'left' });
  else SB.hide();
}

/* ---------- pieces shared by several screens ---------- */
function topicRows(list = TOPICS) {
  return `<div class="topics">${list.map((tp) => {
    const ids = topicIds(tp.id), m = ids.filter(mastered).length, p = Math.round((m / ids.length) * 100);
    const h = ids.filter(halfway).length, hp = Math.round((h / ids.length) * 100);
    const seen = topicSeen(tp.id), right = ids.filter((id) => rec(id)[0].endsWith('1')).length;
    const sp = Math.max(0, Math.round((seen / ids.length) * 100) - p - hp); // seen, not yet right: the third, grey step
    const weak = p < 100 && WEAK.has(tp.id);
    const cls = p >= 100 ? ' done' : weak ? ' weak' : '';
    const line = seen && p < 100 ? `<span class="tmeta${weak ? ' bad-t' : ''}">${t('seenRight', seen, right)}</span>` : '';
    return `<div class="topic${cls}${line ? ' x3' : ''}" data-act="setup" data-t="${tp.id}"><span class="ico">${p >= 100 ? svg('check', 18) : svg(tp.icon || TOPIC_ICON[tp.id] || 'book', 18)}</span>` +
      `<span class="card-title">${esc(tp.title)}</span>${line}<span class="n"><b>${m}/${ids.length}</b>${h ? `<span class="acc">${t('halfwayN', h)}</span>` : ''}</span>` +
      `<span class="bar"><i style="width:${p}%"></i><i class="half" style="left:${p}%;width:${hp}%"></i><i class="seen" style="left:${p + hp}%;width:${sp}%"></i></span></div>`;
  }).join('')}</div>`;
}
function tbars(per, limit = 60) {
  return `<div class="tbars">${TOPICS.filter((tp) => per[tp.id]).map((tp) => {
    const [a, b] = per[tp.id], p = Math.round((a / b) * 100);
    return `<div class="tbar${p < limit ? ' weak' : ''}"><span class="card-title">${esc(tp.title)}</span><span class="n">${a}/${b}</span><span class="bar"><i style="width:${p}%"></i></span></div>`;
  }).join('')}</div>`;
}
function perTopic(ids, isOk) {
  const per = {};
  ids.forEach((id) => { const tp = Q[id].topic; per[tp] = per[tp] || [0, 0]; per[tp][1]++; if (isOk(id)) per[tp][0]++; });
  return per;
}
function examLine() {
  const E = S.exam;
  const a = E.ids.filter((id) => E.ans[id] != null).length;
  return t('examLine', a, E.ids.length, fmt(remaining()));
}

/* ---------- views ---------- */
const VIEWS = {
  /* A1 Home */
  home() {
    const st = streak();
    const returning = S.total > 0;
    const lv = LEVELS.filter((l) => l.id && BASES[l.id]).map((l) => {
      const b = BASES[l.id], lp = levelPct(b);
      return `<div class="lvl${l === LEVEL ? ' on' : ''}" data-act="level" data-id="${l.id}">${ring(lp, seenPct(b))}<div><div class="card-title">${l.title}</div>` +
        `<div class="card-meta">${t('levelMeta', b.topics.length, b.questions.length, myExams(l.id).length)}</div></div><span class="chev" data-i="next" data-s="20"></span></div>`;
    }).join('');
    // first visit: the pitch; afterwards: pick up where you left off
    const lp = levelPct(), mis = allMistakes().length;
    const top = returning
      ? `<div class="band resume"><span class="kicker">${t('resumeK')}</span>
          <div class="row" style="gap:14px;align-items:center">${ring(lp, seenPct())}<div><div class="card-title">${esc(LEVEL.title)}</div><div class="card-meta">${t('resumeMeta', BANK.questions.filter((q) => touched(q.id)).length, BANK.questions.length, mis)}</div></div></div>
          <button class="pill pill-primary pill-wide" data-act="resume"><span data-i="play" data-s="18"></span>${t('practiseN', 10)}</button></div>`
      : `<div class="stack g12"><span class="meta">${t('homeKicker')}</span><h1 class="display">${t('homeTitle')}</h1>
        <p class="body-muted">${t('homeLead')}</p></div>`;
    return {
      title: 'IYT Test', nav: 'home',
      body: `<div class="row sb-between" style="min-height:40px"><img class="logo" src="design/logo-black.svg" alt="RYC">${st ? `<span class="streak"><span class="fire" data-i="fire" data-s="14"></span>${t('streak', st)}</span>` : ''}</div>
        ${top}
        ${S.exam ? `<div class="continue" data-act="examIntro"><div><span class="meta">${t('examOpen')}</span><div class="card-title" style="margin-top:4px">${examLine()}</div></div><span class="mini mini-accent">${t('continue')}</span></div>` : ''}
        <div class="stack" style="gap:10px">${returning ? `<span class="kicker">${t('levelsK')}</span>` : ''}${lv}</div>
        <div class="band soonlist"><span class="kicker">${t('moreLevels')}</span>${LEVELS.filter((l) => !(l.id && BASES[l.id])).map((l) => `<div class="att"><span class="card-title" style="font-weight:400">${l.title}</span><span class="card-meta">${t(l.soon || 'soon')}</span></div>`).join('')}</div>`,
    };
  },

  /* A2 Level */
  level() {
    const lp = levelPct(), m = BANK.questions.filter((q) => mastered(q.id)).length;
    const any = BANK.questions.some((q) => touched(q.id));
    const weakest = weakTopics().sort((a, b) => topicAcc(a) - topicAcc(b)).slice(0, 2).map(short);
    const sn = BANK.questions.filter((q) => touched(q.id)).length;
    const text = any ? t('levelText', m, BANK.questions.length, BANK.questions.filter((q) => halfway(q.id)).length, sn) + (weakest.length ? t('weakest', weakest.join(', ')) : '') : t('levelFresh');
    const mis = allMistakes().length;
    return {
      title: LEVEL.title,
      body: `<div class="row" style="gap:18px;align-items:center">${ring(lp, seenPct(), ' l', `<b data-count="${lp}" data-suffix="%">${lp}%</b><small>${t('mastered')}</small>`)}
          <p class="body-s">${esc(text)}</p></div>
        <div class="row" style="gap:10px"><button class="pill pill-primary lvl-btn" data-act="setup"><span data-i="play" data-s="20"></span>${t('practice')}</button>
          <button class="pill lvl-btn" data-act="examIntro"><span data-i="timer" data-s="20"></span>${t('mockShort')}</button></div>
        ${mis ? `<div class="row sb-between"><div><div class="card-title">${t('mistakesToClear')}</div><div class="card-meta">${t('toAnswerTwice', mis)}</div></div><button class="mini mini-accent" data-act="allMistakes">${t('review')}</button></div>` : ''}
        <div class="stack g8"><div class="row sb-between"><span class="kicker">${t('topics')}</span><span class="meta">${t('masteredTotal')}</span></div>${topicRows()}</div>`,
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
      after = `<div class="verdict ${ok ? 'ok' : 'bad'}"><span class="ico">${svg(ok ? 'check' : 'x', 16)}</span>${ok ? t('correct') : t('notQuite')}</div>
        <div class="band why" id="why"><span class="kicker">${t('why')}</span><p class="body-s">${esc(q.why)}</p><span class="chip ref">${svg('book', 12)}${esc(q.ref)}</span></div>`;
    }
    const flagged = S.flags.includes(id);
    const tools = `<div class="qtools"><button class="mini${flagged ? ' on' : ''}" data-act="flag"><span data-i="flag" data-s="14"></span>${flagged ? t('flagged') : t('flag')}</button>` +
      (!P.checked && !last ? `<button class="mini" data-act="skip"><span data-i="next" data-s="14"></span>${t('skip')}</button>` : '') + '</div>';
    let main;
    if (!P.checked && P.fb) main = { text: t('check'), off: P.sel == null, act: check };
    else if (!P.checked) main = { text: last ? t('finish') : t('next'), off: P.sel == null, act: silentNext };
    else main = { text: last ? t('seeResults') : t('next'), act: nextQ };
    return {
      title: t('practice'), main,
      body: `<div class="progress">${segs}</div>
        <div class="qhead"><span class="meta meta-ink">${t('questionOf', P.i + 1, n)}</span><span class="chip">${esc(short(q.topic))}</span></div>
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
    const half = P.ids.filter(halfway).length, fresh = done.filter((id) => !P.seen.has(id)).length;
    const per = perTopic(done, (id) => P.res[id] === 'ok');
    // one session has a question or two per topic, so a topic is called out only if it is weak over all answers too
    const missed = Object.entries(per).filter(([, [a, b]]) => a < b);
    const worst = missed.filter(([tp]) => WEAK.has(tp)).sort((x, y) => topicAcc(x[0]) - topicAcc(y[0]))[0];
    const rightAll = (tp) => topicIds(tp).filter((id) => touched(id) && rec(id)[0].endsWith('1')).length;
    const heads = t('heads');
    const head = heads[pct >= 90 ? 0 : pct >= 70 ? 1 : pct >= 50 ? 2 : 3];
    const copy = (!wrong.length ? t('noMistakes') : worst ? t('weakAll', short(worst[0]), rightAll(worst[0]), topicSeen(worst[0])) : t('spread', wrong.length, missed.length)) + t('timeSpent', fmt(P.secs * 1000));
    const reviewAct = () => go('review', { items: wrong.map((id) => ({ id, pick: P.picks[id] })), label: 'thisSession', from: 'session' });
    // what the next sessions will do with this one's answers
    const nextRow = (icon, title, meta) => `<div class="r"><span>${svg(icon, 16)}</span><div><div class="card-title">${title}</div><div class="card-meta">${meta}</div></div></div>`;
    const next = (plus ? nextRow('trophy', t('nextMastered', plus), t('nextMasteredMeta')) : '') +
      (half ? nextRow('check', t('nextHalf', half), t('nextHalfMeta')) : '') +
      (wrong.length ? nextRow('refresh', t('nextWrong', wrong.length), t('nextWrongMeta')) : '');
    return {
      title: t('results'),
      main: worst ? { text: t('practiseTopic', lower(short(worst[0]))), act: () => startPractice(pickFor(topicIds(worst[0]), 10)) }
        : wrong.length ? { text: t('reviewN', wrong.length), icon: 'refresh', act: reviewAct } : { text: t('practiseMore'), act: () => openSetup() },
      second: worst ? { pos: 'bottom', text: t('mistakesN', wrong.length), icon: 'refresh', act: reviewAct }
        : wrong.length ? { pos: 'bottom', text: t('practiseMore'), act: () => openSetup() } : null,
      body: `<div class="score"><span class="ring l" style="--v:${pct}"><b>${ok}/${done.length}</b><small>${t('correct')}</small></span>
          <h2 class="display" style="font-size:34px">${head}</h2><p class="body-muted">${esc(copy)}</p></div>
        <div class="stats"><div class="stat"><b>+${fresh}</b><span class="meta">${t('statNew')}</span></div><div class="stat"><b>${half}</b><span class="meta">${t('halfway')}</span></div><div class="stat"><b>${wrong.length}</b><span class="meta">${t('statWrong')}</span></div></div>
        <div class="stack g8"><span class="kicker">${t('byTopic')}</span>${tbars(per)}</div>
        ${next ? `<div class="band next-band"><span class="kicker">${t('whatNext')}</span>${next}</div>` : ''}`,
    };
  },

  /* A9 Review mistakes (a session's, an exam's, or the running list) */
  review(c) {
    const items = c.items.filter((x) => Q[x.id]);
    const cards = items.map(({ id, pick }) => {
      const q = Q[id];
      const yours = c.from === 'all' ? '' : pick == null
        ? `<div class="ans bad"><span class="l">${svg('x', 12)}</span><span>${t('notAnswered')}</span></div>`
        : pick !== q.answer ? `<div class="ans bad"><span class="l">${svg('x', 12)}</span><span>${esc(q.options[pick])}</span></div>` : '';
      return `<div class="rev"><span class="chip" style="align-self:flex-start">${esc(TT[q.topic])}</span>${figHtml(q)}<p class="q">${esc(q.q)}</p>${yours}
        <div class="ans ok"><span class="l">${svg('check', 12)}</span><span>${esc(q.options[q.answer])}</span></div>
        <p class="body-muted" style="font-size:14px">${esc(q.why)}</p></div>`;
    }).join('');
    const total = allMistakes().length;
    return {
      title: t('mistakesTitle'),
      main: items.length ? { text: t('practiseThese'), act: () => startPractice(shuffle(items.map((x) => x.id)), true) } : null,
      body: `<div class="stack g4"><span class="meta">${t(c.label)} · ${items.length}</span><h2 class="display-s">${t('reviewTitle')}</h2></div>
        ${cards || `<p class="body-muted empty">${t('nothingToReview')}</p>`}
        ${c.from !== 'all' && total ? `<div class="row sb-between" style="padding-top:4px"><span class="kicker">${t('allMistakes')}</span><button class="meta acc" data-act="allMistakes">${pl(total, 'question')} ›</button></div>` : ''}`,
    };
  },

  /* B1 Exam intro (also the Exam tab) */
  examIntro() {
    const atts = myExams().slice(0, 5).map((e) => `<div class="att"><span class="card-meta">${day(e.at)}</span><span class="card-meta">${e.pct}% · <span class="${e.passed ? 'acc' : 'bad-t'}">${e.passed ? t('passedW') : t('notPassedW')}</span></span></div>`).join('');
    const rules = t('rules').map(([a, b], i) => `<div class="step step-num"><span class="step-ico">${i + 1}</span><div><div class="card-title">${a}</div><div class="card-meta">${b}</div></div></div>`).join('');
    return {
      title: t('mockExam'), nav: 'examIntro',
      main: { text: S.exam ? t('continueExam') : t('startExam'), act: startExam },
      body: `<div class="stack g8"><span class="meta">${LEVEL.title}</span><h2 class="display">${t('mockExam')}</h2>
          <p class="body-muted">${t('examLead', TOPICS.length)}</p></div>
        <div class="stats"><div class="stat"><b>${BANK.examQuestions}</b><span class="meta">${t('questionsW', BANK.examQuestions)}</span></div><div class="stat"><b>${BANK.examMinutes}</b><span class="meta">${t('minutesW', BANK.examMinutes)}</span></div><div class="stat"><b>${BANK.passMark}%</b><span class="meta">${t('toPass')}</span></div></div>
        ${S.exam ? `<div class="row sb-between"><div><span class="meta">${t('inProgress')}</span><div class="card-title" style="margin-top:4px">${examLine()}</div></div><button class="danger-link" data-act="restart">${t('startOver')}</button></div>` : ''}
        <div class="steps steps-plain">${rules}</div>
        ${atts ? `<div class="band" style="padding:16px 18px"><div class="card-title" style="margin-bottom:4px">${t('lastAttempts')}</div>${atts}</div>` : ''}
        <p class="hint">${t('examDefaults')}</p>`,
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
      title: t('mockExam'),
      main: E.i < n - 1 ? { text: t('nextArrow'), act: () => examMove(1) } : { text: t('finishDots'), act: () => { sheet = { v: 'grid' }; render(); } },
      second: E.i > 0 ? { text: t('prevArrow'), act: () => examMove(-1) } : null,
      body: `<div class="bar ink"><i style="width:${((E.i + 1) / n) * 100}%"></i></div>
        <div class="qhead"><span class="meta meta-ink">${t('nOf', E.i + 1, n)}</span><span class="timer${left < 300000 ? ' low' : ''}"><span data-i="timer" data-s="16"></span><b>${fmt(left)}</b></span></div>
        ${figHtml(q)}<p class="q">${esc(q.q)}</p><div class="opts">${opts}</div>
        <div class="qtools"><button class="mini${fl ? ' on' : ''}" data-act="eflag"><span data-i="flag" data-s="14"></span>${fl ? t('flagged') : t('flag')}</button>
          <button class="mini" data-act="grid"><span data-i="board-view" data-s="14"></span>${t('allQuestions')}</button></div>`,
    };
  },

  /* B4 Passed / B5 Not passed */
  examResult() {
    const R = S.last;
    if (!R) return { title: t('result'), body: `<p class="body-muted empty">${t('noResult')}</p>` };
    const ids = R.ids.filter((id) => Q[id]);
    const per = perTopic(ids, (id) => R.ans[id] === Q[id].answer);
    const weak = TOPICS.filter((tp) => per[tp.id] && per[tp.id][0] / per[tp.id][1] < BANK.passMark / 100).map((tp) => tp.id);
    const wrong = ids.filter((id) => R.ans[id] !== Q[id].answer);
    const names = weak.slice().sort((a, b) => (per[a][0] - per[a][1]) - (per[b][0] - per[b][1])).slice(0, 3).map(short);
    const reviewAct = () => go('review', { items: wrong.map((id) => ({ id, pick: R.ans[id] })), label: 'mockExam', from: 'exam' });
    let head, copy, bars;
    if (R.passed) {
      head = R.pct >= 85 ? t('readyForExam') : t('passed');
      copy = t('timeUsed', fmt(R.secs * 1000), BANK.examMinutes) + (weak.length ? t('weakUnder', weak.length, BANK.passMark) : t('allAbove', BANK.passMark));
      bars = `<div class="stack g8"><span class="kicker">${t('byTopic')}</span>${tbars(per, BANK.passMark)}</div>`;
    } else {
      head = R.pct >= BANK.passMark - 10 && weak.length ? t('closeShort', weak.length) : t('notPassedHead');
      copy = (R.left ? t('leftUnanswered', R.left, R.auto) : '') + (names.length ? t('costMost', names.join(', ')) : '');
      const fine = {}, bad = {};
      for (const tp in per) (weak.includes(tp) ? bad : fine)[tp] = per[tp];
      bars = (weak.length ? `<div class="stack g8"><span class="kicker">${t('workFirst')}</span>${tbars(bad, BANK.passMark)}</div>` : '') +
        (Object.keys(fine).length ? `<div class="stack g8"><span class="kicker">${t('fine')}</span>${tbars(fine, BANK.passMark)}</div>` : '');
    }
    return {
      title: t('result'),
      main: R.passed
        ? (wrong.length ? { text: t('mistakesN', wrong.length), icon: 'refresh', act: reviewAct } : { text: t('backToLevel'), act: () => { stack = [{ v: 'home' }, { v: 'level' }]; render(true); } })
        : { text: weak.length ? t('practiseWeak', weak.length) : t('practise'), icon: 'play', act: () => startPractice(pickFor(weak.flatMap(topicIds), 20)) },
      second: R.passed ? { text: t('share'), icon: 'share', act: () => share(R) } : (wrong.length ? { text: t('reviewN', wrong.length), act: reviewAct, pos: 'bottom' } : null),
      body: `<div class="score">${R.passed ? `<span class="pass">${svg('trophy', 16)}${t('passed')}</span>` : `<span class="pass no">${svg('x', 16)}${t('notYetPass', BANK.passMark)}</span>`}
          <span class="ring l${R.passed ? '' : ' bad'}" style="--v:${R.pct}"><b data-count="${R.pct}" data-suffix="%">${R.pct}%</b><small>${t('okOf', R.ok, R.n)}</small></span>
          <h2 class="display" style="font-size:34px">${head}</h2><p class="body-muted">${esc(copy)}</p></div>${bars}`,
    };
  },

  /* C1 Progress */
  progress() {
    const lp = levelPct(), st = streak();
    const week = Array.from({ length: 7 }, (_, k) => { const d = new Date(); d.setDate(d.getDate() - 6 + k); return { d, n: S.days[dkey(d)] || 0 }; });
    const max = Math.max(1, ...week.map((w) => w.n)), sum = week.reduce((a, w) => a + w.n, 0);
    const names = t('days');
    const days = week.map((w, k) => `<div class="${k === 6 ? 'today' : ''}"><i class="${w.n ? '' : 'z'}" style="height:${w.n ? Math.max(8, (w.n / max) * 100) : 4}%"></i><span>${names[w.d.getDay()]}</span></div>`).join('');
    const mis = allMistakes().length, fl = S.flags.filter((id) => Q[id]).length;
    const exams = myExams().slice(0, 5).map((e) => `<div class="att"><span class="card-meta">${day(e.at)}</span><span class="card-meta">${e.pct}% · <span class="${e.passed ? 'acc' : 'bad-t'}">${e.passed ? t('passedW') : t('notPassedW')}</span></span></div>`).join('');
    const weakest = TOPICS.filter((tp) => topicSeen(tp.id)).sort((a, b) => topicAcc(a.id) - topicAcc(b.id) || topicPct(a.id) - topicPct(b.id)).slice(0, 3);
    return {
      title: 'IYT Test', nav: 'progress',
      body: `<div class="stack g4"><span class="meta">${LEVEL.title}</span><h2 class="display-s">${t('progress')}</h2></div>
        <div class="stats"><div class="stat"><b data-count="${lp}" data-suffix="%">${lp}%</b><span class="meta">${t('mastered')}</span></div><div class="stat"><b data-count="${S.total}">${S.total}</b><span class="meta">${t('answeredW')}</span></div><div class="stat"><b data-count="${st}">${st}</b><span class="meta">${t('dayStreak', st)}</span></div></div>
        <div class="band" style="padding:16px 18px"><div class="row sb-between" style="margin-bottom:12px"><span class="kicker">${t('thisWeek')}</span><span class="meta">${pl(sum, 'question')}</span></div><div class="days">${days}</div></div>
        <div class="row sb-between"><div><div class="card-title">${t('mistakesToClear')}</div><div class="card-meta">${mis ? t('misMeta', mis) : t('noneNow')}</div></div><button class="mini mini-accent${mis ? '' : ' off'}" data-act="allMistakes">${t('review')}</button></div>
        <div class="row sb-between"><div><div class="card-title">${t('flaggedQ')}</div><div class="card-meta">${fl ? pl(fl, 'question') : t('flagHint')}</div></div><button class="mini mini-accent${fl ? '' : ' off'}" data-act="flagged">${t('practise')}</button></div>
        <div class="band" style="padding:16px 18px"><div class="row sb-between" style="margin-bottom:4px"><span class="kicker">${t('mockExams')}</span><button class="meta acc" data-act="examIntro">${t('mockShort')} ›</button></div>${exams || `<p class="card-meta" style="margin:6px 0 0">${t('noExams')}</p>`}</div>
        ${weakest.length ? `<div class="stack g8"><div class="row sb-between"><span class="kicker">${t('weakestTopics')}</span><button class="meta acc" data-act="level">${t('allTopics')}</button></div>${topicRows(weakest)}</div>` : ''}`,
    };
  },

  /* C2 Profile */
  profile() {
    const u = (IN_TG && TG.initDataUnsafe && TG.initDataUnsafe.user) || null;
    const name = u ? [u.first_name, u.last_name].filter(Boolean).join(' ') : t('guest');
    const ini = name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();
    const ava = u && u.photo_url ? `<img src="${esc(u.photo_url)}" alt="">` : esc(ini);
    const th = S.set.theme;
    const seg = (act, val, on, inner) => `<button class="lang${on ? ' lang-on' : ''}" data-act="${act}" data-t="${val}">${inner}</button>`;
    const tog = (k) => `<button class="toggle${S.set[k] ? ' on' : ''}" data-act="set" data-k="${k}" aria-pressed="${S.set[k]}" aria-label="${esc(t(k === 'shuffle' ? 'shuffle' : 'explain'))}"></button>`;
    const partial = LANG !== 'en' && BANK.translated < BANK.questions.length ? t('partEnglish') : '';
    loadDaily();
    // with several levels the row opens the level list on Home; with one it is plain text
    const lvl = ready().length > 1
      ? `<div class="set" data-act="tab" data-v="home"><div class="card-title">${t('currentLevel')}</div><span class="val">${esc(LEVEL.title)}${svg('next', 16)}</span></div>`
      : `<div class="set"><div class="card-title">${t('currentLevel')}</div><span class="val">${esc(LEVEL.title)}</span></div>`;
    const daily = typeof DAILY === 'boolean'
      ? `<div class="set"><div><div class="card-title">${t('daily')}</div><div class="card-meta">${t('dailyMeta')}</div></div><button class="toggle${DAILY ? ' on' : ''}" data-act="daily" aria-pressed="${DAILY}" aria-label="${esc(t('daily'))}"></button></div>` : '';
    // admins get the students' results page (api/admin.mjs says who)
    const admin = ADMIN ? `<div class="set" data-act="admin"><div><div class="card-title">${t('students')}</div><div class="card-meta">${t('studentsMeta')}</div></div><span class="val">${svg('next', 16)}</span></div>` : '';
    return {
      title: 'IYT Test', nav: 'profile',
      body: `<div class="row" style="gap:14px"><span class="tg-ava" style="width:52px;height:52px;font-size:16px">${ava}</span><div><div class="card-title" style="font-size:18px">${esc(name)}</div>
          <div class="card-meta">${u ? (u.username ? '@' + esc(u.username) + ' · ' : '') + t('syncedTg') : t('savedBrowser')}</div></div></div>
        <div class="stack">
          ${daily}${lvl}${admin}
          <div class="set"><div class="card-title">${t('language')}</div><div class="langs">${LANGS.map((l) => seg('lang', l, LANG === l, l.toUpperCase())).join('')}</div></div>
          <div class="set"><div class="card-title">${t('theme')}</div><div class="langs">${seg('theme', 'day', th === 'day', svg('sun', 14) + t('themeDay'))}${seg('theme', 'night', th === 'night', svg('moon', 14) + t('themeNight'))}${seg('theme', 'auto', th === 'auto', t('auto'))}</div></div>
          <div class="set"><div><div class="card-title">${t('shuffle')}</div><div class="card-meta">${t('shuffleMeta')}</div></div>${tog('shuffle')}</div>
          <div class="set"><div><div class="card-title">${t('explain')}</div><div class="card-meta">${t('explainMeta')}</div></div>${tog('feedback')}</div>
          <div class="set"><div><div class="card-title">${t('reset')}</div><div class="card-meta">${t('resetMeta')}</div></div><button class="danger-link" data-act="reset">${t('resetBtn')}</button></div>
        </div>
        <p class="hint">${esc(t('disclaimer', BANK.version) + partial)}</p>`,
    };
  },

  /* C4 Students (admins only): every student's results */
  admin() {
    loadStudents();
    let body;
    if (ADM === 'loading' || ADM === undefined) body = skeleton('students');
    else if (ADM === null) body = `<div class="empty stack g12"><p class="body-muted">${t('studentsFail')}</p><button class="pill" style="margin:0 auto" data-act="adminReload">${t('reload')}</button></div>`;
    else if (!ADM.length) body = `<div class="empty"><p class="body-muted">${t('studentsEmpty')}</p></div>`;
    else {
      const active = ADM.filter((u) => u.week > 0).length, exams = ADM.reduce((a, u) => a + u.exams.length, 0);
      const chip = (k) => `<button class="tag${ADM_SORT === k ? ' tag-on' : ''}" style="min-height:36px;font-size:14px;padding:0 12px" data-act="sort" data-s="${k}">${t('sort' + k[0].toUpperCase() + k.slice(1))}</button>`;
      const rows = sortedStudents().map((u) => {
        const name = studentName(u), L = studentLevel(u);
        const meta = [u.username && u.name ? '@' + u.username : '', L && L.seen ? L.lv.title : '', day(u.active)].filter(Boolean).join(' · ');
        const right = u.total ? `<b>${L ? L.pct + '%' : '–'}</b>${t('answeredN', u.total)}` : t('noProgress');
        const bar = L && L.seen ? `<span class="bar"><i style="width:${L.pct}%"></i><i class="seen" style="left:${L.pct}%;width:${Math.max(0, L.seenPct - L.pct)}%"></i></span>` : '';
        return `<div class="topic${bar ? ' x3' : ''} stu" data-act="student" data-id="${u.id}">${avatar(u, 'ico')}<span class="card-title">${esc(name)}</span><span class="tmeta">${esc(meta)}</span>${bar}<span class="n">${right}</span></div>`;
      }).join('');
      body = `<div class="stats"><div class="stat"><b data-count="${ADM.length}">${ADM.length}</b><span class="meta">${t('studentsW', ADM.length)}</span></div><div class="stat"><b>${active}</b><span class="meta">${t('activeWeek')}</span></div><div class="stat"><b>${exams}</b><span class="meta">${t('examsTaken', exams)}</span></div></div>
        <div class="tags" style="margin-top:4px">${chip('progress')}${chip('name')}${chip('joined')}</div>
        <div class="topics">${rows}</div>`;
    }
    return {
      title: t('students'),
      body: `<div class="stack g4"><span class="meta">${t('profile')}</span><h2 class="display-s">${t('students')}</h2><p class="body-muted">${t('studentsMeta')}</p></div>${body}`,
    };
  },
};

/* A3 Set up a session · B3 Exam grid · C4 one student */
const SHEETS = {
  student(s) {
    const u = Array.isArray(ADM) && ADM.find((x) => x.id === s.id);
    if (!u) return `<div class="empty"><span class="meta">${t('studentsFail')}</span></div>`;
    const name = studentName(u);
    const per = {};
    ready().forEach((l) => { const L = u.levels[l.prefix]; if (L && L.seen) per[l.id] = [L.mastered, BASES[l.id].questions.length]; });
    const bars = Object.keys(per).map((id) => { const [a, b] = per[id], p = Math.round((a / b) * 100), L = u.levels[LEVELS.find((l) => l.id === id).prefix];
      return `<div class="tbar"><span class="card-title">${esc(LEVELS.find((l) => l.id === id).title)}</span><span class="n">${p}%</span><span class="bar"><i style="width:${p}%"></i></span><span class="card-meta" style="grid-column:1/-1">${t('levelText', a, b, 0, L.seen)}${L.mistakes ? ' ' + t('misMeta', L.mistakes) + '.' : ''}</span></div>`; }).join('');
    const exams = u.exams.map((e) => `<div class="att"><span class="card-meta">${day(e.at)} · ${esc((LEVELS.find((l) => l.id === e.lv) || {}).title || e.lv)}</span><span class="card-meta">${e.pct}% · <span class="${e.passed ? 'acc' : 'bad-t'}">${e.passed ? t('passedW') : t('notPassedW')}</span></span></div>`).join('');
    return `<div class="row" style="gap:14px">${avatar(u, 'tg-ava', 'width:52px;height:52px;font-size:16px')}<div><div class="card-title" style="font-size:18px">${esc(name)}</div>
        <div class="card-meta">${u.username ? '@' + esc(u.username) + ' · ' : ''}${u.lang.toUpperCase()} · ${u.daily ? t('dailyOn') : t('dailyOff')}</div></div></div>
      <div class="stats"><div class="stat"><b>${u.total}</b><span class="meta">${t('answeredW')}</span></div><div class="stat"><b>${u.streak}</b><span class="meta">${t('dayStreak', u.streak)}</span></div><div class="stat"><b>${u.week}</b><span class="meta">${t('thisWeek').toLowerCase()}</span></div></div>
      <div class="att"><span class="card-meta">${t('joined')}</span><span class="card-meta">${day(u.joined)}</span></div>
      <div class="att"><span class="card-meta">${t('lastActive')}</span><span class="card-meta">${day(u.active)}</span></div>
      ${bars ? `<div class="stack g8"><span class="kicker">${t('levelsK')}</span><div class="tbars">${bars}</div></div>` : `<p class="body-muted">${t('noProgress')}</p>`}
      <div class="stack g8"><span class="kicker">${t('mockExams')}</span>${exams || `<p class="card-meta" style="margin:0">${t('noExamsAdmin')}</p>`}</div>`;
  },
  setup(s) {
    const pool = setupPool(s), N = pool.length, size = s.size === 'all' ? N : Math.min(s.size, N);
    const misAll = allMistakes();
    const chips = TOPICS.map((tp) => {
      const c = s.mis ? topicIds(tp.id).filter(isMistake).length : topicIds(tp.id).length;
      return `<button class="tag${s.on.has(tp.id) ? ' tag-on' : ''}${s.mis && !c ? ' off' : ''}" style="min-height:40px;font-size:14px;padding:0 12px;gap:6px" data-act="chip" data-t="${tp.id}">${esc(short(tp.id))}<span class="tag-count">${c}</span></button>`;
    }).join('');
    const sz = (v, label) => `<button class="tag${s.size === v ? ' tag-on' : ''}" style="min-height:40px;font-size:15px" data-act="size" data-s="${v}">${label}</button>`;
    return `<div class="stack g4"><span class="meta">${t('practice')}</span><h2 class="display-s">${t('whatToPractise')}</h2></div>
      <div class="stack g8"><div class="row sb-between"><span class="kicker">${t('topics')}</span><button class="meta acc" data-act="chipsAll">${s.on.size === TOPICS.length ? t('none') : t('all')}</button></div>
        <div class="tags">${chips}</div><span class="hint">${weakTopics().length ? t('weakPre') : ''}${t('tapToggle')}</span></div>
      <div class="stack g8"><span class="kicker">${t('questionsK')}</span><div class="tags">${N > 10 ? sz(10, '10') : ''}${N > 20 ? sz(20, '20') : ''}${sz('all', t('allN', N))}
        ${misAll.length ? `<button class="tag${s.mis ? ' tag-on' : ''}" style="min-height:40px;font-size:15px" data-act="mis"><span data-i="refresh" data-s="16"></span>${t('mistakesOnly')}<span class="tag-count">${misAll.length}</span></button>` : ''}</div></div>
      <div class="set" style="border:0;padding:6px 0 0"><div><div class="card-title">${t('showAnswer')}</div><div class="card-meta">${t('explainMeta')}</div></div><button class="toggle${s.fb ? ' on' : ''}" data-act="fb" aria-pressed="${s.fb}" aria-label="${esc(t('showAnswer'))}"></button></div>
      <div class="sheet-foot"><button class="pill pill-primary pill-wide${size ? '' : ' off'}" data-act="start">${size ? t('start', size) : t('pickTopic')}</button></div>`;
  },
  grid() {
    const E = S.exam, a = E.ids.filter((id) => E.ans[id] != null).length, left = E.ids.length - a;
    const cells = E.ids.map((id, k) => `<span class="${E.ans[id] != null ? 'a' : ''}${E.flags.includes(k) ? ' f' : ''}${k === E.i ? ' now' : ''}" data-act="jump" data-n="${k}">${k + 1}</span>`).join('');
    return `<div class="row sb-between"><div class="stack g4"><span class="meta">${t('overview')}</span><h2 class="display-s" style="font-size:26px">${t('answeredLeft', a, left)}</h2></div>
        <span class="timer"><span data-i="timer" data-s="16"></span><b>${fmt(remaining())}</b></span></div>
      <div class="grid40">${cells}</div>
      <div class="legend-row"><span><i class="a"></i>${t('answered')}</span><span><i></i>${t('notYet')}</span><span><i class="f"></i>${t('flagged')}</span></div>
      <button class="pill ${left ? 'pill-quiet' : 'pill-primary'} pill-wide" data-act="submit">${t('submitExam')}</button>
      <span class="hint" style="text-align:center">${left ? t('submitHint', left) : t('allAnswered')}</span>`;
  },
};

/* ---------- practice ---------- */
function defaultTopics() {
  const w = weakTopics();
  return w.length ? w : TOPICS.map((tp) => tp.id);
}
function openSetup(topics) {
  sheet = { v: 'setup', on: new Set(topics || defaultTopics()), size: 10, mis: false, fb: S.set.feedback };
  render();
}
function setupPool(s) {
  const ids = TOPICS.filter((tp) => s.on.has(tp.id)).flatMap((tp) => topicIds(tp.id));
  return s.mis ? ids.filter(isMistake) : ids;
}
// Mistakes first, then questions not yet mastered, then the rest; the chosen ones come in random order.
// A session mixes mistakes (up to 40 %), questions answered right once (up to 30 %, so the second right answer comes
// and they become mastered) and new ones; empty slots are filled in that order, then from the rest.
function pickFor(pool, n) {
  const mis = shuffle(pool.filter(isMistake)), half = shuffle(pool.filter((id) => halfway(id) && !isMistake(id)));
  const fresh = shuffle(pool.filter((id) => !touched(id))), done = shuffle(pool.filter(mastered));
  const rest = shuffle(pool.filter((id) => touched(id) && !mastered(id) && !isMistake(id) && !halfway(id)));
  const out = [...mis.splice(0, Math.ceil(n * 0.4)), ...half.splice(0, Math.ceil(n * 0.3))];
  for (const g of [fresh, mis, half, rest, done]) out.push(...g.splice(0, n - out.length));
  return shuffle(out.slice(0, n));
}
function startPractice(ids, fb = S.set.feedback) {
  ids = ids.filter((id) => Q[id]);
  if (!ids.length) return toast(t('noQuestions'));
  P = {
    ids, i: 0, res: {}, picks: {}, sel: null, checked: false, fb, t0: Date.now(), done: false,
    orders: Object.fromEntries(ids.map((id) => [id, S.set.shuffle ? shuffle([0, 1, 2, 3]) : [0, 1, 2, 3]])),
    before: Object.fromEntries(ids.map((id) => [id, mastered(id)])), seen: new Set(ids.filter(touched)),
  };
  if (['results', 'review', 'examResult'].includes(cur().v)) replace('question'); else go('question');
}
function check() {
  if (P.sel == null || P.checked) return;
  const id = P.ids[P.i], oi = P.orders[id][P.sel], ok = oi === Q[id].answer;
  record(id, ok, 'practice', oi);
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
  record(id, ok, 'practice', oi);
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
  $app.querySelectorAll('.timer').forEach((el) => el.classList.toggle('low', left < 300000));
  if (left <= 0) return submitExam(true);
  if (++ticks % 5 === 0) save(false);
}
function buildExam() {
  const n = Math.min(BANK.examQuestions, BANK.questions.length);
  const groups = shuffle(TOPICS.map((tp) => shuffle(topicIds(tp.id)))); // round-robin over topics: an even spread
  const ids = [];
  while (ids.length < n && groups.some((g) => g.length)) for (const g of groups) if (g.length && ids.length < n) ids.push(g.pop());
  const order = shuffle(ids);
  S.exam = { lv: LEVEL.id, ids: order, ord: Object.fromEntries(order.map((id) => [id, S.set.shuffle ? shuffle([0, 1, 2, 3]) : [0, 1, 2, 3]])), ans: {}, flags: [], el: 0, i: 0, at: Date.now(), last: Date.now() };
  save();
}
function startExam() {
  if (S.exam && S.exam.ids.some((id) => !Q[id])) S.exam = null; // the bank changed under a saved exam
  if (!S.exam) buildExam();
  go('exam');
}
async function restartExam() {
  if (!(await confirmBox(t('confirmRestart')))) return;
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
  if (!auto && left && !(await confirmBox(t('confirmSubmit', left)))) return;
  stopTimer();
  let ok = 0;
  E.ids.forEach((id) => {
    if (!Q[id]) return;
    const a = E.ans[id], c = a === Q[id].answer;
    if (c) ok++;
    if (a != null) record(id, c, 'exam', a); // unanswered questions do not touch mastery
  });
  const n = E.ids.length, pct = Math.round((ok / n) * 100), passed = pct >= BANK.passMark;
  const R = { at: Date.now(), ok, n, pct, passed, secs: Math.round(E.el / 1000), left, auto: !!auto, ids: E.ids, ans: E.ans };
  S.exams = [{ lv: LEVEL.id, at: R.at, ok, n, pct, passed, secs: R.secs }, ...S.exams].slice(0, 40);
  S.last = R;
  S.exam = null;
  save();
  cloudSave();
  hap(passed ? 'success' : 'error');
  if (cur().v === 'exam') { sheet = null; replace('examResult'); }
}
function share(R) {
  const text = t('shareText', R.pct, LEVEL.title);
  if (IN_TG) TG.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(BOT_LINK)}&text=${encodeURIComponent(text)}`);
  else if (navigator.share) navigator.share({ text, url: BOT_LINK }).catch(() => {});
  else { navigator.clipboard?.writeText(`${text} ${BOT_LINK}`); toast(t('copied')); }
}

/* ---------- taps ---------- */
const ACT = {
  back,
  main: () => mainCb && mainCb(),
  second: () => secCb && secCb(),
  tab: (d) => tab(d.v),
  level: async (d) => { if (d.id) await setLevel(d.id); go('level'); },
  resume: () => startPractice(pickFor(BANK.questions.map((q) => q.id), 10)),
  examIntro: () => (cur().v === 'examIntro' ? null : go('examIntro')),
  setup: (d) => openSetup(d.t ? [d.t] : undefined),
  allMistakes: () => go('review', { items: allMistakes().map((id) => ({ id })), label: 'allMistakes', from: 'all' }),
  flagged: () => startPractice(pickFor(S.flags.filter((id) => Q[id]), 20)),
  // set-up sheet
  chip: (d) => { const s = sheet; s.on.has(d.t) ? s.on.delete(d.t) : s.on.add(d.t); hap('sel'); render(); },
  chipsAll: () => { sheet.on = new Set(sheet.on.size === TOPICS.length ? [] : TOPICS.map((tp) => tp.id)); render(); },
  size: (d) => { sheet.size = d.s === 'all' ? 'all' : +d.s; hap('sel'); render(); },
  mis: () => { sheet.mis = !sheet.mis; if (sheet.mis) sheet.size = 'all'; render(); },
  fb: () => { sheet.fb = !sheet.fb; S.set.feedback = sheet.fb; save(); render(); },
  start: () => { const s = sheet, pool = setupPool(s); startPractice(pickFor(pool, s.size === 'all' ? pool.length : s.size), s.fb); },
  // practice question
  opt: (d) => { if (P.checked) return; P.sel = +d.n; hap('sel'); render(); },
  flag: () => {
    const id = P.ids[P.i], k = S.flags.indexOf(id);
    k >= 0 ? S.flags.splice(k, 1) : S.flags.push(id);
    save(); render(); toast(k >= 0 ? t('unflagged') : t('flaggedToast'));
  },
  skip: () => { const [id] = P.ids.splice(P.i, 1); P.ids.push(id); P.sel = null; render(true); },
  // exam
  eopt: (d) => { const E = S.exam, id = E.ids[E.i]; E.ans[id] = E.ord[id][+d.n]; hap('sel'); save(false); render(); },
  eflag: () => { const E = S.exam, k = E.flags.indexOf(E.i); k >= 0 ? E.flags.splice(k, 1) : E.flags.push(E.i); save(false); render(); },
  grid: () => { sheet = { v: 'grid' }; render(); },
  jump: (d) => { S.exam.i = +d.n; sheet = null; save(false); render(true); },
  submit: () => submitExam(false),
  restart: () => restartExam(),
  // profile
  lang: async (d) => { S.set.lang = d.t; save(); await setLang(d.t); render(); },
  theme: (d) => { S.set.theme = d.t; save(); applyTheme(); render(); },
  set: (d, el) => { S.set[d.k] = !S.set[d.k]; save(); el.classList.toggle('on', S.set[d.k]); setTimeout(render, 220); },
  daily: (d, el) => toggleDaily(el),
  admin: () => go('admin'),
  adminReload: () => { loadStudents(true); render(); },
  student: (d) => { sheet = { v: 'student', id: +d.id }; render(); },
  sort: (d) => { ADM_SORT = d.s; hap('sel'); render(); },
  reset: async () => {
    if (!(await confirmBox(t('confirmReset')))) return;
    const set = S.set;
    S = fresh(); S.set = set;
    save(); cloudSave(); toast(t('resetDone')); render();
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
  // Enter / Space on a focused card or row acts like a tap (buttons do this on their own)
  const f = document.activeElement;
  if ((e.key === 'Enter' || e.key === ' ') && f && f !== document.body && f.matches('[data-act]:not(button)') && $app.contains(f)) { e.preventDefault(); f.click(); return; }
  const c = cur();
  if (sheet || (c.v !== 'question' && c.v !== 'exam')) return;
  const k = 'abcd'.indexOf(e.key.toLowerCase()), num = '1234'.indexOf(e.key);
  const n = k >= 0 ? k : num;
  if (n >= 0) ACT[c.v === 'exam' ? 'eopt' : 'opt']({ n });
  if (e.key === 'Enter' && mainCb) { e.preventDefault(); ACT.main(); }
});
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') { if (timerInt) tick(); save(false); cloudSave(); serverSave(true); }
  else lastTick = Date.now(); // time spent away does not count
});

/* ---------- start ---------- */
function deepLink() {
  const p = (IN_TG && TG.initDataUnsafe && TG.initDataUnsafe.start_param) || new URLSearchParams(location.search).get('screen') || '';
  if (p === 'exam') stack = [{ v: 'examIntro' }];
  else if (p === 'progress') stack = [{ v: 'progress' }];
  else if (p === 'profile' || p === 'settings') stack = [{ v: 'profile' }];
  else if (p === 'admin' || p === 'students') stack = [{ v: 'profile' }, { v: 'admin' }];
  else if (p === 'level' || LEVELS.some((l) => l.link === p && BASES[l.id])) stack = [{ v: 'home' }, { v: 'level' }];
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
  LANG = pickLang();
  document.documentElement.lang = LANG;
  const boot = $app.querySelector('.sk-label');
  if (boot) boot.textContent = t('loading');
  const server = serverLoad(); // in parallel with the banks
  const banks = await Promise.all(LEVELS.filter((l) => l.id).map((l) =>
    fetchBank(l.id).catch(() => 0).then((b) => [l.id, b])));
  for (const [id, b] of banks) if (b && b.questions) BASES[id] = b;
  if (!BASES[DEFAULT_LEVEL]) throw new Error(t('bankError', banks.find(([id]) => id === DEFAULT_LEVEL)[1]));
  const remote = await cloudLoad();
  if (remote && remote.ts > S.ts) { S = merge(remote); applyTheme(); try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  // The server copy wins when newer (another phone); progress made only on this device is sent up once now.
  const srv = await server;
  if (srv && srv.state && srv.ts > S.ts) { S = merge(srv.state); applyTheme(); try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  else if (srv && S.ts > srv.ts) serverSave(true);
  const link = (IN_TG && TG.initDataUnsafe && TG.initDataUnsafe.start_param) || new URLSearchParams(location.search).get('screen') || '';
  const want = (LEVELS.find((l) => l.link === link) || {}).id || S.set.level;
  LEVEL = LEVELS.find((l) => l.id === want && BASES[l.id]) || LEVELS.find((l) => l.id === DEFAULT_LEVEL);
  S.set.level = LEVEL.id;
  swapExam();
  await setLang(pickLang());
  prune();
  expireExam();
  const then = deepLink();
  render(true);
  if (then === 'setup') openSetup();
}
init().catch((e) => {
  $app.innerHTML = `<div class="boot"><div class="stack g8" style="padding:24px;text-align:center"><span class="meta">${t('error')}</span><p class="body-muted">${esc(e.message)}</p></div></div>`;
  console.error(e);
});
