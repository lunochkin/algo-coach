import { answerResult, canSubmit, flipped, gradeResult, togglePick } from './answer';
import { cardLabel } from './records';
import type { Result } from './result';
import type { Question } from './types';
import { FINISH } from './words/pages';
import { ASK_NEXT, ASK_REVEAL, askSubmit } from './words/queue';

// one question's answer, for every platform: what the user has picked, typed
// and ticked, and the one press the question asks for at each point. Each
// platform holds the state and draws it: `pages.md`, The knowledge pages

export interface AskState {
  picked: number[]; // displayed positions
  text: string;
  guessing: boolean;
  revealed: boolean; // an open question's key, shown
  recalled: Set<number>;
  fell: Set<number>;
  wrong: boolean;
  result: Result | null;
}

export const initialAsk = (): AskState => ({
  picked: [],
  text: '',
  guessing: false,
  revealed: false,
  recalled: new Set(),
  fell: new Set(),
  wrong: false,
  result: null,
});

export type AskEvent =
  | { type: 'pick'; pos: number; multi: boolean }
  | { type: 'text'; text: string }
  | { type: 'guess'; on: boolean }
  | { type: 'reveal' }
  | { type: 'recall'; i: number }
  | { type: 'fall'; i: number }
  | { type: 'wrong' }
  | { type: 'answered'; result: Result };

/** One step of the answer. An answered question takes no more picks or ticks. */
export function askReducer(s: AskState, e: AskEvent): AskState {
  if (s.result && e.type !== 'answered') return s;
  switch (e.type) {
    case 'pick':
      return { ...s, picked: togglePick(s.picked, e.pos, e.multi) };
    case 'text':
      return { ...s, text: e.text };
    case 'guess':
      return { ...s, guessing: e.on };
    case 'reveal':
      return { ...s, revealed: true };
    case 'recall':
      return { ...s, recalled: flipped(s.recalled, e.i) };
    case 'fall':
      return { ...s, fell: flipped(s.fell, e.i) };
    case 'wrong':
      return { ...s, wrong: !s.wrong };
    case 'answered':
      return { ...s, result: e.result };
  }
}

export type AskPress = 'next' | 'reveal' | 'grade' | 'submit';

/**
 * The one press the question asks for: Next once answered, Reveal then the
 * grade on an open question, and the answer on the rest. An exam moves on at
 * once, so its last question's press finishes it.
 */
export function askAct(
  q: Question,
  s: AskState,
  exam: { last: boolean } | null,
): { act: AskPress; label: string; enabled: boolean } {
  if (s.result) return { act: 'next', label: exam?.last ? FINISH : ASK_NEXT, enabled: true };
  if (q.format === 'card') {
    if (!s.revealed) return { act: 'reveal', label: ASK_REVEAL, enabled: true };
    return { act: 'grade', label: cardLabel(q.key.length, s.recalled, s.fell, s.wrong), enabled: true };
  }
  const reply = { text: s.text, picked: s.picked, guessing: s.guessing };
  return { act: 'submit', label: askSubmit(!!exam, !!exam?.last), enabled: canSubmit(q, reply) };
}

/** The answer the press records: the grade on an open question, the reply on the rest. */
export function askResult(q: Question, order: number[], s: AskState): Result {
  if (q.format === 'card') return gradeResult(q, order, s.recalled, s.fell, s.wrong);
  return answerResult(q, order, { text: s.text, picked: s.picked, guessing: s.guessing });
}

/** A point of an open question's key, as its tick reads. */
export const keyPointLabel = (i: number, point: string) => `${i + 1}. ${point}`;
