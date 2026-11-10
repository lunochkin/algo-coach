import { type Board } from './schedule';
import { shuffle, type Rng } from './select';
import type { Question } from './types';

/** Exam pool: level L in unlocked groups, no cards. */
export function examPool(b: Board, level: number): Question[] {
  const out: Question[] = [];
  for (const qs of b.servedGroups()) {
    if (qs[0].level !== level || !b.unlocked(qs[0])) continue;
    for (const q of qs) if (q.format !== 'card') out.push(q);
  }
  return out;
}

/** Uniform random sample of min(n, pool) questions, in sampled order. */
export function selectExam(b: Board, level: number, n: number, rng: Rng = Math.random): Question[] {
  return shuffle(examPool(b, level), rng).slice(0, n);
}

/** Score per `course/topic`, in order of first appearance. */
export function byTopic(results: { q: Question; correct: boolean }[]) {
  const m = new Map<string, { score: number; n: number }>();
  for (const r of results) {
    const k = `${r.q.course}/${r.q.topic}`;
    const e = m.get(k) ?? { score: 0, n: 0 };
    e.score += r.correct ? 1 : 0;
    e.n += 1;
    m.set(k, e);
  }
  return [...m].map(([topic, e]) => ({ topic, ...e }));
}
