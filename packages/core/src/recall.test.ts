import { describe, expect, it } from 'vitest';

import { failures, nextHint, recallBlank, recallView, type components } from './index';

type RecallAttempt = components['schemas']['RecallAttempt'];
type Outcome = components['schemas']['CaseOutcome'];

const ran = (outcomes: Outcome[], hints: RecallAttempt['hints'] = []): RecallAttempt =>
  ({ results: outcomes.map((outcome, i) => ({ case_id: `c${i}`, outcome })), hints }) as RecallAttempt;

describe('the recall trainer', () => {
  it('offers the notes, then the form, then nothing', () => {
    expect([nextHint([]), nextHint(['notes']), nextHint(['notes', 'form'])]).toEqual(['notes', 'form', null]);
  });

  it('opens on the signature and an indented blank line', () => {
    expect(recallBlank('def solve(a, x):')).toBe('def solve(a, x):\n    ');
  });

  it('reads a clean pass as recalled cold', () => {
    const view = recallView(ran(['passed', 'passed']));
    expect(view).toEqual({
      recalled: true,
      verdict: 'Recalled: 2 of 2 cases passed',
      failures: null,
      hints: 'Recalled cold, with no hint taken.',
    });
  });

  it('names the failures by severity, and the hints a pass took', () => {
    const view = recallView(ran(['wrong', 'crashed', 'passed', 'wrong'], ['notes']));
    expect(view.recalled).toBe(false);
    expect(view.failures).toBe('1 crashed · 2 wrong answer');
    expect(view.hints).toBe('Taken on the way: the notes.');
  });

  it('reads a run with no cases as not recalled', () => {
    expect(recallView(ran([])).recalled).toBe(false);
    expect(failures([])).toEqual([]);
  });
});
