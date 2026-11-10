import { FSRS6_DEFAULT_WEIGHTS, FSRS6_MODEL_BOUNDS, FSRS6Algorithm } from 'ts-fsrs/models/fsrs-6';

import type { Attempt, FsrsRules } from './types';

const DAY = 86_400_000;
const MINUTE = 60_000;

export const AGAIN = 1;
export const HARD = 2;
export const GOOD = 3;

/** The libraries' defaults (py-fsrs and ts-fsrs agree), except fuzzing, which is off. */
export const DEFAULT_FSRS: FsrsRules = {
  version: 6,
  desired_retention: 0.9,
  maximum_interval: 36500,
  learning_steps_minutes: [1, 10],
  relearning_steps_minutes: [10],
  enable_fuzzing: false,
  parameters: [...FSRS6_DEFAULT_WEIGHTS],
  mastered_stability_days: 21,
};

export interface Memory {
  stability: number; // days
  difficulty: number; // 1..10
  due: number; // epoch ms
  learning: boolean; // in a (re)learning step (minutes), not yet on day-scale review
}

const algos = new Map<string, FSRS6Algorithm>();
function algo(p: number[]): FSRS6Algorithm {
  const k = p.join(',');
  let a = algos.get(k);
  if (!a) algos.set(k, (a = new FSRS6Algorithm(p, true, FSRS6_MODEL_BOUNDS)));
  return a;
}

/** Next step or graduation within (re)learning, as py-fsrs's Scheduler does it. */
function stepDue(steps: number[], step: number, rating: number): { step: number; wait: number } | null {
  if (!steps.length) return null;
  if (rating === AGAIN) return { step: 0, wait: steps[0] * MINUTE };
  if (rating === HARD) {
    if (step === 0) return { step, wait: (steps.length === 1 ? steps[0] * 1.5 : (steps[0] + steps[1]) / 2) * MINUTE };
    return { step, wait: steps[step] * MINUTE };
  }
  if (rating === GOOD && step + 1 < steps.length) return { step: step + 1, wait: steps[step + 1] * MINUTE };
  return null; // graduates to review
}

/**
 * FSRS state after reviewing each attempt at its own time. The memory model is ts-fsrs's FSRS-6;
 * the scheduling around it (elapsed days as whole 24 h periods, minute steps, no fuzz) mirrors
 * py-fsrs's Scheduler, which the CLI uses, so both compute the same due.
 */
export function replay(attempts: Attempt[], rules: FsrsRules = DEFAULT_FSRS): Memory | null {
  if (!attempts.length) return null;
  const a = algo(rules.parameters);
  let s = 0;
  let d = 0;
  let last = 0;
  let due = 0;
  let state: 'learning' | 'review' | 'relearning' = 'learning';
  let step = 0;
  for (const { t, rating } of attempts) {
    if (s === 0) {
      ({ stability: s, difficulty: d } = a.next_state(null, 0, rating));
    } else {
      const elapsed = Math.max(0, Math.floor((t - last) / DAY));
      ({ stability: s, difficulty: d } = a.next_state({ stability: s, difficulty: d }, elapsed, rating));
    }
    const days = Math.min(a.next_interval(s, rules.desired_retention), rules.maximum_interval) * DAY;
    if (state === 'review') {
      if (rating === AGAIN && rules.relearning_steps_minutes.length) {
        state = 'relearning';
        step = 0;
        due = t + rules.relearning_steps_minutes[0] * MINUTE;
      } else due = t + days;
    } else {
      const steps = state === 'learning' ? rules.learning_steps_minutes : rules.relearning_steps_minutes;
      const next = stepDue(steps, step, rating);
      if (next) {
        step = next.step;
        due = t + next.wait;
      } else {
        state = 'review';
        step = 0;
        due = t + days;
      }
    }
    last = t;
  }
  return { stability: s, difficulty: d, due, learning: state !== 'review' };
}
