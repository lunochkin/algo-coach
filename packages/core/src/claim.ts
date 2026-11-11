import type { components } from './api/schema';
import { described, type EngineClient } from './engine';
import { duration } from './sitting';

// the claim and the self-label asked after a sitting, for every platform:
// `flows.md`, Drill loop. Which modes an attempt's verdict leaves open, and
// the skip on an attempt that crashed on every case, are the engine's: it
// sends them with each attempt and refuses a label outside them

type FailureMode = components['schemas']['FailureMode'];
type Attempt = components['schemas']['Attempt'];

export type Confidence = 'guess' | 'leaning' | 'sure';
export const CONFIDENCES: Confidence[] = ['guess', 'leaning', 'sure'];

// each mode beside a gloss: the word alone does not separate `rust` from `gap`
export const MODE_GLOSS: Record<FailureMode, string> = {
  speed: 'I got there, slower than I should have',
  none: 'Nothing went wrong',
  gap: 'I did not hold the form',
  rust: 'I held the form and did not reach it',
  syntax: 'I slipped writing code I know',
};

/** The techniques ticked before the user answers: the one the problem was picked by, where the problem carries it. */
export const claimDefault = (drilled: string | null, techniques: string[]): string[] =>
  drilled && techniques.includes(drilled) ? [drilled] : [];

/** A tick toggled. A decline clears the ticks rather than hiding them, so undoing it starts from nothing. */
export function claimToggled(chosen: string[], technique: string): string[] {
  return chosen.includes(technique) ? chosen.filter((one) => one !== technique) : [...chosen, technique];
}

/** The claim can be saved once it names a technique or declines, and says how sure. */
export const claimReady = (chosen: string[], declined: boolean, confidence: Confidence | null) =>
  (declined || chosen.length > 0) && confidence !== null;

export function attemptLine(index: number, count: number, attempt: Attempt): string {
  const time = attempt.time_to_solve_sec != null ? ` · ${duration(attempt.time_to_solve_sec)}` : '';
  return `Attempt ${index + 1} of ${count} · ${attempt.solved ? 'solved' : 'not solved'}${time}`;
}

export const CLAIM_QUESTION = 'Which techniques did this code use?';
export const CLAIM_DECLINE = 'None of these';
export const CLAIM_CONFIDENCE = 'How sure are you?';
export const LABEL_QUESTION = 'Why did it go that way?';
export const LABEL_OPTIONAL = 'Answering is optional, and a skipped label leaves the attempt unlabelled.';
export const claimRefused = (why: string) => `The answer was refused: ${why}`;
export const saveLabel = (sending: boolean) => (sending ? 'Saving…' : 'Save');

/** A decline clears the ticks rather than hiding them, so undoing it starts from nothing. */
export function claimDeclined(declined: boolean, chosen: string[]): { declined: boolean; chosen: string[] } {
  return declined ? { declined: false, chosen } : { declined: true, chosen: [] };
}

/**
 * Sends one attempt's claim, then its label where a mode was picked: naming
 * the techniques is what the label asks about. Returns the refusal, or null.
 */
export async function sendClaim(
  client: EngineClient,
  attemptId: string,
  form: { chosen: string[]; declined: boolean; confidence: Confidence; mode: FailureMode | null },
): Promise<string | null> {
  try {
    const params = { params: { path: { attempt_id: attemptId } } };
    const claimed = await client.POST('/api/attempts/{attempt_id}/claims', {
      ...params,
      body: { techniques: form.chosen, declined: form.declined, confidence: form.confidence },
    });
    if (!claimed.data) return described(claimed.error);
    if (form.mode) {
      const labelled = await client.POST('/api/attempts/{attempt_id}/labels', { ...params, body: { mode: form.mode } });
      if (!labelled.data) return described(labelled.error);
    }
    return null;
  } catch (reason) {
    return String(reason);
  }
}
