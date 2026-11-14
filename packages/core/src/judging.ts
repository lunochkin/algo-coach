import type { components } from './api/schema';
import { described, type EngineClient } from './engine';
import type { Outcome } from './sittingrun';

type Served = components['schemas']['JudgedItem'];
type Decided = components['schemas']['JudgeDecided'];
export type Verdict = Decided['verdict'];

export const JUDGE_TITLE = 'Judge a solution';
export const JUDGE_NOTE = 'Read the solution. Is it correct, or is one line wrong?';
export const JUDGE_CLEAN = 'Correct';
export const JUDGE_FLAWED = 'One line is wrong';
export const JUDGE_TAP = 'Tap the line that is wrong.';
export const JUDGE_SUBMIT = 'Submit';
export const JUDGE_NEXT = 'Next';
export const JUDGE_NONE = 'No solution is left to judge here.';
export const judgeFrom = (cardTitle: string) => `Judge ${cardTitle}`;
/** A form's difficulty, as its card's depth in the card graph: a root teaches the basic forms. */
export const judgeDepth = (depth: number) => (depth === 0 ? 'Root card' : `Depth ${depth}`);

/** A value as the page prints it: JSON, which is what a case holds. */
const shown = (value: unknown) => JSON.stringify(value);

/** The spec a served item states its question by: one of its template's cases. */
export function judgeExample(example: Served['example']): string {
  return `solve(${example.args.map(shown).join(', ')}) returns ${shown(example.expected)}`;
}

/** Each verdict as the result reads it. */
export const VERDICTS: Record<Verdict, string> = {
  right: 'Right: the solution is correct.',
  false_alarm: 'The solution was correct: no line is wrong.',
  located: 'Found: that line is the wrong one.',
  spotted: 'Right that it is wrong, but the flaw is on another line.',
  missed: 'Missed: one line is wrong.',
};

/** The flawed line as the form writes it: what the line should have read. Null on a clean item. */
export function judgeCorrection(decided: Decided): { label: string; code: string } | null {
  if (decided.line == null || decided.correct == null) return null;
  return { label: `Line ${decided.line} should read`, code: decided.correct };
}

/** Whether the result reads as a success, for the verdict's colour. */
export const verdictPassed = (verdict: Verdict) => verdict === 'right' || verdict === 'located';

/** The separating case, line by line: the arguments, what was expected, what the flawed code gave. */
export function separatingLines(decided: Decided): string[] {
  const one = decided.case;
  if (!one) return [];
  const gave = one.outcome === 'crashed' ? 'raised an error' : `returned ${shown(one.returned)}`;
  return [`solve(${one.args.map(shown).join(', ')})`, `expected ${shown(one.expected)}`, `the flawed code ${gave}`];
}

/** The next item to judge, from every card or from one. `null` where none is left. */
export async function nextJudged(client: EngineClient, card: string | null): Promise<Outcome<Served | null>> {
  try {
    const { data, error, response } = await client.GET('/api/judging/next', {
      params: { query: card ? { card } : {} },
    });
    if (response.status === 404 && card === null) return { ok: true, value: null };
    if (response.status === 404 && error && described(error) === 'no item to judge') return { ok: true, value: null };
    return error === undefined && data ? { ok: true, value: data } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}

/** Sends one answer: Correct, or the tapped line. */
export async function judge(client: EngineClient, itemId: string, line: number | null): Promise<Outcome<Decided>> {
  try {
    const { data, error } = await client.POST('/api/judging/{item_id}', {
      params: { path: { item_id: itemId } },
      body: { called_clean: line === null, line },
    });
    return error === undefined && data ? { ok: true, value: data } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}
