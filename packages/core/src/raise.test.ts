import { describe, expect, it } from 'vitest';

import { NEW_PER_DAY, NEW_STEP, newPerDay, todayLimit } from './queue';

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
    expect(newPerDay([{ t: at(NOON), n: 20 }, { t: at(NOON - 3_600_000), n: 15 }])).toBe(20);
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
    expect(todayLimit([{ t: at(NOON), n: 3 }], [raise(NOON)], NOON, UTC)).toBe(3 + NEW_STEP);
  });
});
