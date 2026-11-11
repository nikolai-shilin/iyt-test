// Runs the question-of-the-day send by hand (the Vercel cron runs the same code every day at 09:00 UTC).
//
//   npm run bot:daily -- --to <chat id> [--ru|--en]   # today's question to one chat only (ignores the switches);
//                                                    # without --ru/--en, in the language picked in the app
//   npm run bot:daily -- --dry                   # how many users would get it today; sends nothing
//   npm run bot:daily                            # the real send to everyone who has it on and hasn't had it today

import { sendDaily, sendDailyTo } from '../daily.mjs';

const args = process.argv.slice(2);
const to = args.includes('--to') ? args[args.indexOf('--to') + 1] : null;
if (to) console.log(await sendDailyTo(to, { lang: args.includes('--ru') ? 'ru' : args.includes('--en') ? 'en' : undefined }));
else console.log(await sendDaily({ dry: args.includes('--dry') }));
