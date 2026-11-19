// Runs the browser's analyze() from web/js/core/domain.js on datasets and prints the results as JSON.
import fs from 'node:fs';
import { makeEnv } from './fe_env.mjs';

const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const env = makeEnv();
env.load(['js/core/config.js', 'js/core/util.js', 'js/core/domain.js']);
const out = cases.map(c => {
  env.ctx.today = () => c.today;
  env.ctx.state.items = c.items;
  const a = env.ctx.analyze();
  return { score: a.score, tier: a.tier, current: a.current, longest: a.longest, daysKept: a.daysKept, ticks: a.A.ticks, elapsed: a.A.elapsed,
           notes: a.A.notes, completed: a.A.completed, rate: a.rate, cons: a.cons, rec: a.rec, idle: a.idle, pts: a.pts };
});
console.log(JSON.stringify(out));
