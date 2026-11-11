import { describe, expect, it } from 'vitest';

import {
  caseLabel,
  clockState,
  cutValue,
  draftKey,
  isDraftKey,
  userDraftKey,
  duration,
  editorOpening,
  opening,
  preferenceAfter,
  shownSeconds,
  submissionView,
  VALUE_SHOWN,
  visibilityMove,
  type components,
  type Draft,
} from './index';

type Sitting = components['schemas']['Sitting'];
type Carry = components['schemas']['Carry'];
type Submitted = components['schemas']['Submitted'];

const sitting = (over: Partial<Sitting> = {}): Sitting =>
  ({ id: 's1', clock_started_at: '2026-11-11T10:00:00Z', ended_at: null, pauses: [], ...over }) as Sitting;
const carry = (over: Partial<Carry> = {}): Carry => ({
  code: null,
  at: null,
  solved_at: null,
  solved_sitting_id: null,
  solved_code: null,
  run_started_at: null,
  ...over,
});
const draft = (code: string, at: string, sittingId: string | null = 'old'): Draft => ({ code, at, sitting: sittingId });

describe('the sitting clock', () => {
  it('reads unstarted, running, paused and ended from the sitting', () => {
    expect(clockState(null)).toEqual({ unstarted: true, paused: false, ended: false, running: false });
    expect(clockState(sitting({ clock_started_at: null })).unstarted).toBe(true);
    expect(clockState(sitting()).running).toBe(true);
    const paused = sitting({ pauses: [{ at: '2026-11-11T10:05:00Z', until: null }] });
    expect(clockState(paused)).toMatchObject({ paused: true, running: false });
    expect(clockState(sitting({ ended_at: '2026-11-11T10:30:00Z' }))).toMatchObject({ ended: true, running: false });
  });

  it('counts on from the engine reading while running, and holds it otherwise', () => {
    expect(shownSeconds(60, 1000, 3500, true)).toBe(62.5);
    expect(shownSeconds(60, 1000, 3500, false)).toBe(60);
    expect(shownSeconds(null, 1000, 3500, true)).toBe(0);
    expect(duration(3725)).toBe('1:02:05');
    expect(duration(65.9)).toBe('1:05');
  });

  it('sets the preference on the press alone: start and resume on, pause off', () => {
    expect([preferenceAfter('start'), preferenceAfter('resume'), preferenceAfter('pause')]).toEqual([
      'on',
      'on',
      'off',
    ]);
  });

  it('pauses on hiding, and resumes on return only the pause hiding took', () => {
    const running = clockState(sitting());
    expect(visibilityMove(running, true, false)).toEqual({ move: 'pause', pausedByHiding: true });
    const paused = clockState(sitting({ pauses: [{ at: '2026-11-11T10:05:00Z', until: null }] }));
    expect(visibilityMove(paused, false, true)).toEqual({ move: 'resume', pausedByHiding: false });
    expect(visibilityMove(paused, false, false).move).toBeNull();
    expect(visibilityMove(clockState(null), true, false).move).toBeNull();
  });
});

describe("a draft's key", () => {
  it("names the user, so one account never opens another's code", () => {
    expect(userDraftKey('u-4f9c2a', 'p1')).not.toBe(userDraftKey('u-7b1e3d', 'p1'));
  });

  it("finds every draft a browser holds, a user's or one written before the user was named", () => {
    expect(isDraftKey(userDraftKey('u-4f9c2a', 'p1'))).toBe(true);
    expect(isDraftKey(draftKey('p1'))).toBe(true);
    expect(isDraftKey('algo-coach:clock')).toBe(false);
  });
});

describe('the code a sitting opens on', () => {
  it('opens on the newer of the draft and the last attempt', () => {
    const attempt = carry({ code: 'submitted', at: '2026-11-11T10:00:00Z' });
    expect(opening(draft('typed', '2026-11-11T11:00:00Z'), attempt)).toBe('typed');
    expect(opening(draft('typed', '2026-11-11T09:00:00Z'), attempt)).toBe('submitted');
  });

  it('never carries a solve, nor a draft from before the run or the solve', () => {
    const solved = carry({ solved_at: '2026-11-11T10:00:00Z', solved_sitting_id: 'old' });
    expect(opening(draft('answer', '2026-11-11T11:00:00Z', 'old'), solved)).toBeNull();
    expect(opening(draft('early', '2026-11-11T09:00:00Z', 'other'), solved)).toBeNull();
    const run = carry({ run_started_at: '2026-11-11T10:00:00Z' });
    expect(opening(draft('before', '2026-11-11T09:00:00Z'), run)).toBeNull();
  });

  it("finds the sitting's own draft on a reload, else opens on the signature", () => {
    const own = { ...draft('mine', '2026-11-11T09:00:00Z', 's1'), restored: true };
    expect(editorOpening(own, 's1', null, 'def solve(a):')).toEqual({ code: 'mine', restored: true });
    expect(editorOpening(null, null, null, 'def solve(a):')).toEqual({ code: 'def solve(a):\n    ', restored: false });
  });
});

describe('a submission read back', () => {
  it('reads the verdict, the failure mix and the first failing case whole', () => {
    const view = submissionView({
      attempt: { solved: false },
      verification: {
        results: [
          { case_id: 'a', outcome: 'passed' },
          { case_id: 'b', outcome: 'wrong' },
          { case_id: 'c', outcome: 'timeout' },
        ],
      },
      failure: { case_id: 'b', outcome: 'wrong', args: [1], expected: 2, returned: 3, error: null },
    } as unknown as Submitted);
    expect(view.verdict).toBe('Not solved: 1 of 3 cases passed');
    expect(view.overall).toBe('wrong');
    expect(view.failures).toBe('1 wrong answer · 1 timed out');
    expect(view.failure).toMatchObject({ title: 'Case 2: wrong answer', returned: 3 });
  });

  it('cuts a long value unless asked for it whole, and keeps a short one', () => {
    const long = 'x'.repeat(VALUE_SHOWN + 1);
    expect(cutValue(long, false)).toEqual({ text: `${'x'.repeat(VALUE_SHOWN)}…`, long: true });
    expect(cutValue(long, true).text).toBe(long);
    expect(cutValue('[1]', false)).toEqual({ text: '[1]', long: false });
  });

  it("names a case's mark by its outcome, and its time where one was measured", () => {
    expect(caseLabel(0, 'passed', 12)).toBe('case 1: passed, 12 ms');
    expect(caseLabel(1, 'crashed', null)).toBe('case 2: crashed');
  });
});
