import type { components } from './api/schema';
import { described, type EngineClient } from './engine';
import type { Outcome } from './sittingrun';
import { A_FORM } from './words/pages';

// the recall trainer, for every platform: `flows.md`, Recalling a template

type Hint = components['schemas']['Hint'];
type CaseResult = components['schemas']['CaseResult'];
type RecallAttempt = components['schemas']['RecallAttempt'];
type Prompted = components['schemas']['Prompted'];

// the order the trainer offers them, and each one answers more of the
// question than the last
export const HINTS: Hint[] = ['notes', 'form'];
export const HINT_NAMES: Record<Hint, string> = { notes: 'the notes', form: 'the form' };

export const nextHint = (taken: Hint[]): Hint | null => HINTS[taken.length] ?? null;

// the signature, and the file otherwise blank: `corpus.md` gives why the
// parameter order is stated rather than inferred
export const recallBlank = (signature: string) => `${signature}\n    `;

/** Whether the form this recall asks for is the card's optional one. */
export const recallOptional = (prompt: Prompted | undefined): boolean =>
  prompt?.templates.some((one) => one.slug === prompt.template_slug && one.optional) ?? false;

// a wrong answer and a timeout read apart, in the order `corpus.md` folds a run by
export const OUTCOME_LABELS = {
  passed: 'passed',
  wrong: 'wrong answer',
  timeout: 'timed out',
  crashed: 'crashed',
} as const;
export const SEVEREST = ['crashed', 'wrong', 'timeout', 'passed'] as const;

/** The mix of failures in words, since a strip of marks carries it in colour alone. */
export function failures(results: CaseResult[]): string[] {
  return SEVEREST.filter((outcome) => outcome !== 'passed')
    .map((outcome) => [outcome, results.filter((one) => one.outcome === outcome).length] as const)
    .filter(([, count]) => count > 0)
    .map(([outcome, count]) => `${count} ${OUTCOME_LABELS[outcome]}`);
}

export interface RecallView {
  recalled: boolean;
  verdict: string;
  // the failures in words, or null where every case passed
  failures: string | null;
  // a hinted pass is a pass with its hints, which the record keeps
  hints: string;
}

export function recallView(ran: RecallAttempt): RecallView {
  const results = ran.results ?? [];
  const hints = ran.hints ?? [];
  const passed = results.filter((one) => one.outcome === 'passed').length;
  const recalled = results.length > 0 && passed === results.length;
  const failed = failures(results);
  return {
    recalled,
    verdict: `${recalled ? 'Recalled' : 'Not recalled'}: ${passed} of ${results.length} cases passed`,
    failures: failed.length ? failed.join(' · ') : null,
    hints:
      hints.length === 0
        ? 'Recalled cold, with no hint taken.'
        : `Taken on the way: ${hints.map((one) => HINT_NAMES[one]).join(', ')}.`,
  };
}

export const RECALL_TITLE = 'Recall a form';
export const RECALL_THIS = 'Recall this form';
// the trainer drew the form, so its title stays withheld and the trigger names it
export const recallNote = (drawn: boolean) =>
  drawn
    ? 'The trigger names the form. Type it from memory, and reach for a hint where memory fails.'
    : 'The form is withheld. Type it from memory, and reach for a hint where memory fails.';
export const RECALL_TRIGGER = 'When to reach for it';
export const RECALLING = 'Recalling';
export const RECALL_OPTIONAL = 'optional';
export const RECALL_NO_CASES = 'no cases';
export const hintTaken = (hint: Hint) => `Hint taken: ${HINT_NAMES[hint]}`;
export const takeHint = (hint: Hint) => `Take: ${HINT_NAMES[hint]}`;
export const runLabel = (running: boolean) => (running ? 'Running…' : 'Run');
export const recallRefused = (why: string) => `The recall did not run: ${why}`;
export const RECALL_FORM = 'The form';
export const REVEAL_FORM = 'Reveal the form';
export const RECALL_ANOTHER = 'Recall another';
export const BACK_TO_CARD = 'Back to the card';

// the trainer's requests: a hint at a time, the run with the hints taken, and
// the form revealed after a run. Each returns a value or a refusal in words
const path = (slug: string, template: string) => ({ slug, template_slug: template });

export async function requestHint(
  client: EngineClient,
  slug: string,
  template: string,
  hint: Hint,
): Promise<Outcome<{ hint: Hint; text: string }>> {
  try {
    const { data, error } = await client.GET('/api/cards/{slug}/recall/{template_slug}/hints/{hint}', {
      params: { path: { ...path(slug, template), hint } },
    });
    return data ? { ok: true, value: { hint: data.hint, text: data.text } } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}

export async function runRecall(
  client: EngineClient,
  slug: string,
  template: string,
  code: string,
  hints: Hint[],
): Promise<Outcome<RecallAttempt>> {
  try {
    const { data, error } = await client.POST('/api/cards/{slug}/recall/{template_slug}', {
      params: { path: path(slug, template) },
      body: { code, hints },
    });
    return data ? { ok: true, value: data } : { ok: false, refused: described(error) };
  } catch (reason) {
    return { ok: false, refused: String(reason) };
  }
}

/** The form a run revealed on a press, or null where the engine gave none. */
export async function revealForm(client: EngineClient, slug: string, template: string): Promise<string | null> {
  const shown = await requestHint(client, slug, template, 'form');
  return shown.ok ? shown.value.text : null;
}

/** One entry of the trainer's menu: a template no case checks is named and never offered. */
export interface RecallMenuItem {
  slug: string;
  title: string;
  note: string | null;
  current: boolean;
  enabled: boolean;
}

export function recallMenu(prompt: Pick<Prompted, 'templates' | 'template_slug'>): {
  here: string;
  items: RecallMenuItem[];
} {
  const items = prompt.templates.map((one) => ({
    slug: one.slug,
    title: one.title,
    note: !one.recallable ? RECALL_NO_CASES : one.optional ? RECALL_OPTIONAL : null,
    current: one.slug === prompt.template_slug,
    enabled: one.recallable,
  }));
  // the press names the form being recalled, and a form when none is named
  return { here: items.find((one) => one.current)?.title ?? A_FORM, items };
}
