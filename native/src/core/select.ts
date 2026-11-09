import { PRIORITY, type Board } from './schedule';
import type { Question } from './types';

export type Rng = () => number;

export function ranked(qs: Question[], b: Board, now: number, rng: Rng = Math.random): Question[] {
  return qs
    .map((q) => ({ q, p: PRIORITY[b.status(q, now)], r: rng() }))
    .sort((x, y) => x.p - y.p || x.r - y.r)
    .map((x) => x.q);
}

export function shuffle<T>(xs: T[], rng: Rng = Math.random): T[] {
  const a = [...xs];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
