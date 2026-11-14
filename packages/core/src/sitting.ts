import type { components } from './api/schema';
import { failures, OUTCOME_LABELS, SEVEREST } from './recall';
import { BACK_BOARD, BACK_PROBLEMS } from './words/pages';

// a sitting, for every platform: `flows.md`, Drill loop, and `log.md`,
// Sittings. Each platform keeps the draft and the clock preference in its own
// storage, and times its own ticks; what they mean is decided here

type Sitting = components['schemas']['Sitting'];
type Carry = components['schemas']['Carry'];
type CaseResult = components['schemas']['CaseResult'];
type Submitted = components['schemas']['Submitted'];
type Outcome = components['schemas']['CaseOutcome'];

export interface ClockState {
  // no clock has run: no sitting yet, or one a submission minted
  unstarted: boolean;
  paused: boolean;
  ended: boolean;
  running: boolean;
}

export function clockState(sitting: Sitting | null): ClockState {
  const unstarted = sitting === null || sitting.clock_started_at == null;
  const paused = sitting?.pauses?.at(-1)?.until === null;
  const ended = sitting?.ended_at != null;
  return { unstarted, paused, ended, running: !unstarted && !paused && !ended };
}

/**
 * The seconds a clock shows: the engine's reading, counted on by the
 * platform's monotonic clock since the reading arrived, so a device clock set
 * wrong moves nothing.
 */
export function shownSeconds(elapsedSec: number | null, receivedAt: number, now: number, running: boolean): number {
  if (elapsedSec === null) return 0;
  return running ? elapsedSec + Math.max(0, now - receivedAt) / 1000 : elapsedSec;
}

export function duration(seconds: number): string {
  const whole = Math.floor(seconds);
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const rest = String(whole % 60).padStart(2, '0');
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}` : `${minutes}:${rest}`;
}

// the clock preference: whether the next clock starts by itself. The user's
// own press alone sets it, so a pause a hidden page took says nothing
export type ClockMove = 'start' | 'pause' | 'resume' | 'end';
export const CLOCK_PREFERENCE_KEY = 'climb:clock';
export const preferenceAfter = (pressed: 'start' | 'pause' | 'resume') => (pressed === 'pause' ? 'off' : 'on');
export const clockStartsItself = (stored: string | null) => stored === 'on';

/**
 * What the page hiding or returning does to the clock. Hiding pauses a
 * running clock, and returning resumes only the pause hiding took, never one
 * the user pressed.
 */
export function visibilityMove(
  state: ClockState,
  hidden: boolean,
  pausedByHiding: boolean,
): { move: 'pause' | 'resume' | null; pausedByHiding: boolean } {
  if (state.ended || state.unstarted) return { move: null, pausedByHiding };
  if (hidden && !state.paused) return { move: 'pause', pausedByHiding: true };
  if (!hidden && pausedByHiding) return { move: 'resume', pausedByHiding: false };
  return { move: null, pausedByHiding };
}

// the code a user typed on a problem and not yet submitted, kept per problem
// so the next sitting on it can find it. `at` is when it was typed, since a
// draft is carried by when it was written. `sitting` is where it was typed, so
// a reload finds its own draft whatever the device's clock says. `restored`
// says the sitting restored an earlier solve, which its attempts then report
export interface Draft {
  code: string;
  at: string;
  sitting: string | null;
  restored?: boolean;
}

export const draftKey = (problemId: string) => `climb:problem:${problemId}:draft`;

/**
 * A browser's key for one user's draft. A browser is shared between the
 * accounts signed in on it, and an unsent draft is that user's own code.
 */
export const userDraftKey = (user: string, problemId: string) => `climb:user:${user}:problem:${problemId}:draft`;

/** Every draft key a browser holds, any user's or none, which signing out deletes. */
export const isDraftKey = (key: string) => key.startsWith('climb:') && key.endsWith(':draft');

export function isDraft(value: unknown): value is Draft {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as Draft).code === 'string' &&
    typeof (value as Draft).at === 'string' &&
    (typeof (value as Draft).sitting === 'string' || (value as Draft).sitting === null)
  );
}

/**
 * What a new sitting opens on: the newer of the draft and the last attempt's
 * code, where each is work in progress. A draft from the solving sitting, or
 * typed before the solve or the card's run, is an answer or an earlier run's
 * work, and is left where it is.
 */
export function opening(draft: Draft | null, carry: Carry | null): string | null {
  const drafted =
    draft !== null &&
    (draft.sitting === null || draft.sitting !== carry?.solved_sitting_id) &&
    (!carry?.solved_at || Date.parse(draft.at) > Date.parse(carry.solved_at)) &&
    (!carry?.run_started_at || Date.parse(draft.at) >= Date.parse(carry.run_started_at));
  const submitted = carry?.code != null && carry.at != null ? { code: carry.code, at: carry.at } : null;
  if (!drafted) return submitted?.code ?? null;
  if (submitted === null) return draft.code;
  return Date.parse(draft.at) >= Date.parse(submitted.at) ? draft.code : submitted.code;
}

/**
 * The code the editor opens on and whether it carries a restore: a reload
 * during the sitting finds what was typed in it, and a new sitting opens on
 * the work in progress, else on the signature.
 */
export function editorOpening(
  kept: Draft | null,
  sittingId: string | null,
  carry: Carry | null,
  signature: string | null,
): { code: string; restored: boolean } {
  const own = kept !== null && sittingId !== null && kept.sitting === sittingId;
  if (own) return { code: kept.code, restored: kept.restored === true };
  return { code: opening(kept, carry) ?? (signature ? `${signature}\n    ` : ''), restored: false };
}

/** The outcome a run reads as: its severest case, so a verdict's line and its marks agree. */
export function severest(results: CaseResult[]): Outcome | undefined {
  return SEVEREST.find((outcome) => results.some((one) => one.outcome === outcome));
}

export interface SubmissionView {
  solved: boolean;
  overall: Outcome | undefined;
  verdict: string;
  failures: string | null;
  // the first case failed, whole: the failing case is debugged by reading it
  failure: {
    title: string;
    outcome: Outcome;
    args: unknown[];
    expected: unknown;
    returned: unknown | null;
    error: string | null;
  } | null;
}

// cut on screen past this many characters: a separating case weighs up to a
// mebibyte, and drawing it whole stalls the page. The response stays whole
export const VALUE_SHOWN = 2_000;

/** A failing case's value as the page draws it: cut unless the reader asked for it whole. */
export function cutValue(full: string, whole: boolean): { text: string; long: boolean } {
  const long = full.length > VALUE_SHOWN;
  return { text: long && !whole ? `${full.slice(0, VALUE_SHOWN)}…` : full, long };
}

export function submissionView(submitted: Submitted): SubmissionView {
  const results = submitted.verification.results ?? [];
  const passed = results.filter((one) => one.outcome === 'passed').length;
  const failed = failures(results);
  const failure = submitted.failure;
  const index = failure ? results.findIndex((one) => one.case_id === failure.case_id) : -1;
  return {
    solved: submitted.attempt.solved,
    overall: severest(results),
    verdict: `${submitted.attempt.solved ? 'Solved' : 'Not solved'}: ${passed} of ${results.length} cases passed`,
    failures: failed.length ? failed.join(' · ') : null,
    failure: failure && {
      title: `Case ${index + 1}: ${OUTCOME_LABELS[failure.outcome]}`,
      outcome: failure.outcome,
      args: failure.args,
      expected: failure.expected,
      // a returned value reads only where the case returned the wrong one
      returned: failure.outcome === 'wrong' ? failure.returned : null,
      error: failure.error,
    },
  };
}

/** The page a problem was opened from: the way back from it returns there, `pages.md` Sections. */
export type ProblemFrom =
  | { kind: 'card'; slug: string; title: string | null }
  | { kind: 'listing' }
  | { kind: 'technique'; technique: string }
  | { kind: 'board' };

// a card names the page before a listing filtered to one tag does, and that
// tag is a technique the pick did not come from
export function problemFrom(
  card: { slug: string; title: string | null } | null,
  technique: string | null,
  listing: boolean,
): ProblemFrom {
  if (card !== null) return { kind: 'card', ...card };
  if (listing) return { kind: 'listing' };
  if (technique !== null) return { kind: 'technique', technique };
  return { kind: 'board' };
}

/** The page's header link back, named as the page it returns to. */
export function backLabel(from: ProblemFrom): string {
  switch (from.kind) {
    case 'card':
      return from.title ?? from.slug;
    case 'listing':
      return BACK_PROBLEMS;
    case 'technique':
      return from.technique;
    case 'board':
      return BACK_BOARD;
  }
}

// the sitting's words, each said on every platform
export function sittingBack(from: ProblemFrom): string {
  switch (from.kind) {
    case 'card':
      return 'Back to the card';
    case 'listing':
      return 'Back to the problems';
    case 'technique':
      return `Back to ${from.technique}`;
    case 'board':
      return 'Back to the board';
  }
}
export const CLOCK_RUNNING = 'The clock is running';
export const CLOCK_PAUSED = 'paused';
export const SITTING_ENDED = 'This sitting has ended';
export const CLOCK_START = 'Start';
export const CLOCK_PAUSE = 'Pause';
export const SITTING_END = 'End';
export const END_TITLE = 'End the sitting?';
export const END_NOTE =
  'The clock stops for good, and no more submissions are taken. Each attempt is then asked about in turn.';
export const END_KEEP = 'Keep solving';
export const submitLabel = (running: boolean) => (running ? 'Running…' : 'Submit');
export const RESTORE_SOLVE = 'Restore my last solve';
export const sittingRefused = (why: string) => `Refused: ${why}`;
export const CLAIM_TITLE = 'The claim';
export const CLAIM_NOTE = 'Asked of each attempt now, while the code is minutes old.';
export const FAILURE_ARGS = 'Arguments';
export const FAILURE_EXPECTED = 'Expected';
export const FAILURE_RETURNED = 'Returned';
export const FAILURE_ERROR = 'Error';
