import { cardFields } from './records';
import { gradeChoice, hasAnswer, matchShort, splitGuess } from './reply';
import type { Result } from './result';
import type { Question } from './types';

/** What the user typed, picked and ticked on one question, before it is answered. */
export interface Reply {
  text: string;
  picked: number[]; // displayed positions
  guessing: boolean;
}

/** A short or a choice question's answer. A reply ending in `?` is a guess too. */
export function answerResult(q: Question, order: number[], reply: Reply): Result {
  if (q.format === 'short') {
    const [text, suffix] = splitGuess(reply.text);
    return { q, correct: matchShort(text, q), guess: reply.guessing || suffix, order, picked: [], reply: text };
  }
  const { picked } = reply;
  return { q, correct: gradeChoice(q, order, picked), guess: reply.guessing, order, picked, reply: '' };
}

/** An open question's answer, graded from the points recalled, the traps fallen into and anything else wrong. */
export function gradeResult(
  q: Question,
  order: number[],
  recalled: Set<number>,
  fell: Set<number>,
  wrong: boolean,
): Result {
  const card = cardFields(q.key.length, recalled, fell, wrong);
  return { q, correct: card.grade === 'k', guess: false, order, picked: [], reply: '', grade: card.grade, card };
}

export function togglePick(picked: number[], pos: number, multi: boolean): number[] {
  if (!multi) return [pos];
  return picked.includes(pos) ? picked.filter((p) => p !== pos) : [...picked, pos];
}

export function canSubmit(q: Question, reply: Reply): boolean {
  return q.format === 'short' ? hasAnswer(reply.text) : reply.picked.length > 0;
}

export function flipped(s: Set<number>, i: number): Set<number> {
  const next = new Set(s);
  if (next.has(i)) next.delete(i);
  else next.add(i);
  return next;
}
