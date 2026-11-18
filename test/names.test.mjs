// A Regatta player's name carries no emoji, as the scores API gives it and as a new account is named. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
const { noEmoji } = await import('../api/settings.mjs');
const { fullName, shortName } = await import('../api/game.mjs');
const { accountName } = await import('../api/regatta-session.mjs');

test('emoji are taken out of a name, and the spaces they leave', () => {
  for (const [s, want] of [
    ['Kalopas \u{1F549}️', 'Kalopas'],
    ['Dmitry \u{1F30A} Zamyatin', 'Dmitry Zamyatin'],
    ['Максим\u{1F4AA}\u{1F3FB}', 'Максим'], // a skin tone
    ['\u{1F468}‍\u{1F469}‍\u{1F467} Anna', 'Anna'], // joined into one
    ['\u{1F1F7}\u{1F1FA} Anna', 'Anna'], // a country's flag
    ['1️⃣ Anna', 'Anna'], // a keycap, its digit too
    ['\u{1F681}\u{1F681}', ''],
  ]) assert.equal(noEmoji(s), want, s);
});

test('letters, digits and marks of any script stay', () => {
  for (const s of ['Anna 1', 'No. 7', 'J#24', "O'Neil", 'Zoë', 'Глеб Гужов', '李娜']) assert.equal(noEmoji(s), s);
});

test('the rating and the top three read names without emoji', () => {
  assert.equal(fullName('Kalopas \u{1F549}️'), 'Kalopas');
  assert.equal(shortName('\u{1F30A} Dmitry \u{1F30A} Zamyatin'), 'Dmitry Z.');
  assert.equal(fullName('\u{1F681}\u{1F681}'), null); // nothing else in it: no name
  assert.equal(shortName('\u{1F681}\u{1F681}'), null);
});

test('a new account from Telegram is named without emoji', () => {
  assert.equal(accountName({ first_name: 'Vadim ⛵️', last_name: 'Petrov' }), 'Vadim P.');
  assert.equal(accountName({ first_name: 'Anna', last_name: '\u{1F30A}' }), 'Anna');
  assert.equal(accountName({ first_name: '\u{1F681}', username: 'pilot' }), 'pilot');
  assert.equal(accountName({ first_name: '\u{1F681}' }), null);
});
