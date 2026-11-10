import { describe, expect, it } from 'vitest';

import { NEW_PER_DAY, NEW_STEP, newPerDay, todayLimit } from './queue';
import { setting, SETTING_DEFAULT, validSetting } from './settings';

// 2026-11-10 12:00 UTC, read at UTC so the 04:00 rollover is 04:00 UTC
const NOON = Date.UTC(2026, 10, 10, 12);
const UTC = 0;
const at = (ms: number) => new Date(ms).toISOString();
const raise = (ms: number) => ({ t: at(ms), n: NEW_STEP });

describe('the daily limit', () => {
  it('is the default where no device set one', () => {
    expect(newPerDay([])).toBe(NEW_PER_DAY);
  });

  it('is the latest set, whatever order the records arrived in', () => {
    // a phone's later setting synced before a browser's earlier one
    const limit = (ms: number, n: number) => ({ t: at(ms), name: 'new_per_day' as const, n });
    expect(newPerDay([limit(NOON, 20), limit(NOON - 3_600_000, 15)])).toBe(20);
  });
});

describe("today's raise", () => {
  it('adds a step to the daily limit', () => {
    expect(todayLimit([], [raise(NOON)], NOON, UTC)).toBe(NEW_PER_DAY + NEW_STEP);
  });

  it('adds up across devices within one day', () => {
    expect(todayLimit([], [raise(NOON), raise(NOON + 3_600_000)], NOON + 7_200_000, UTC)).toBe(
      NEW_PER_DAY + 2 * NEW_STEP,
    );
  });

  it('ends at the rollover', () => {
    expect(todayLimit([], [raise(NOON)], Date.UTC(2026, 10, 11, 4, 1), UTC)).toBe(NEW_PER_DAY);
  });

  it('still counts before the rollover', () => {
    expect(todayLimit([], [raise(NOON)], Date.UTC(2026, 10, 11, 3, 59), UTC)).toBe(NEW_PER_DAY + NEW_STEP);
  });

  it('raises the limit the latest record set', () => {
    expect(todayLimit([{ t: at(NOON), name: 'new_per_day', n: 3 }], [raise(NOON)], NOON, UTC)).toBe(3 + NEW_STEP);
  });
});

describe('the exam size', () => {
  it('is the default where no device set one', () => {
    expect(setting([], 'exam_size')).toBe(SETTING_DEFAULT.exam_size);
  });

  it('is read apart from the daily limit', () => {
    const records = [
      { t: at(NOON), name: 'new_per_day' as const, n: 20 },
      { t: at(NOON - 3_600_000), name: 'exam_size' as const, n: 25 },
    ];
    expect(setting(records, 'exam_size')).toBe(25);
    expect(newPerDay(records)).toBe(20);
  });

  it('takes one question at least, where a day may allow none', () => {
    expect(validSetting('exam_size', 0)).toBe(false);
    expect(validSetting('new_per_day', 0)).toBe(true);
    expect(validSetting('exam_size', 2.5)).toBe(false);
  });
});
