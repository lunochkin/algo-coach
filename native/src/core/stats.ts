import { passed, type Board } from './schedule';

const WEEK = 7 * 86_400_000;

export interface Summary {
  questions: number;
  passed: number;
  mastered: number;
  due: number;
  weak: number;
  soon: number; // due within 7 days, not due now
}

export function summary(b: Board, now: number): Summary {
  const s: Summary = { questions: 0, passed: 0, mastered: 0, due: 0, weak: 0, soon: 0 };
  for (const q of b.questions()) {
    const a = b.attempts(q);
    const st = b.status(q, now);
    s.questions++;
    if (passed(a)) s.passed++;
    if ((b.memory(q)?.stability ?? 0) >= b.rules.fsrs.mastered_stability_days) s.mastered++;
    if (st === 'due') s.due++;
    if (st === 'weak') s.weak++;
    if (st !== 'due' && b.status(q, now + WEEK) === 'due') s.soon++;
  }
  return s;
}
