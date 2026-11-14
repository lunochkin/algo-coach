import { describe, expect, it } from 'vitest';

import { judgeCorrection, judgeDepth, judgeExample, separatingLines, VERDICTS, verdictPassed } from './index';
import type { components } from './api/schema';

type Decided = components['schemas']['JudgeDecided'];

describe('a served item', () => {
  it("reads its card's depth as its difficulty", () => {
    expect([judgeDepth(0), judgeDepth(2)]).toEqual(['Root card', 'Depth 2']);
  });

  it('states its question by one case, as JSON', () => {
    expect(judgeExample({ args: [[3, 9, 4], 'ab'], expected: 9 })).toBe('solve([3,9,4], "ab") returns 9');
  });
});

describe('a decided answer', () => {
  it('reads every verdict, and only right and located as a success', () => {
    expect(Object.keys(VERDICTS).sort()).toEqual(['false_alarm', 'located', 'missed', 'right', 'spotted']);
    expect(verdictPassed('located')).toBe(true);
    expect(verdictPassed('spotted')).toBe(false);
  });

  it('shows the separating case, and what the flawed code gave', () => {
    const decided = {
      verdict: 'missed',
      line: 4,
      case: { args: [[9, 2]], expected: 9, outcome: 'wrong', returned: 2 },
    } as Decided;
    expect(separatingLines(decided)).toEqual(['solve([9,2])', 'expected 9', 'the flawed code returned 2']);
  });

  it('names a crash rather than a value, and shows no case on a clean item', () => {
    const crashed = {
      verdict: 'missed',
      line: 2,
      case: { args: [[]], expected: null, outcome: 'crashed', returned: null },
    } as Decided;
    expect(separatingLines(crashed)[2]).toBe('the flawed code raised an error');
    expect(separatingLines({ verdict: 'right', line: null, case: null } as Decided)).toEqual([]);
  });

  it('names the line as the form writes it, and nothing on a clean item', () => {
    const decided = { verdict: 'missed', line: 23, correct: '    best = max(best, area)', case: null } as Decided;
    expect(judgeCorrection(decided)).toEqual({ label: 'Line 23 should read', code: '    best = max(best, area)' });
    expect(judgeCorrection({ verdict: 'right', line: null, correct: null, case: null } as Decided)).toBeNull();
  });
});
