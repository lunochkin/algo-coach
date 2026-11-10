import { describe, expect, it } from 'vitest';

import { dayStart, NEW_STEP, raised, todayLimit } from './queue';

// 2026-11-10 12:00 UTC, read at UTC so the 04:00 rollover is 04:00 UTC
const NOON = Date.UTC(2026, 10, 10, 12);
const UTC = 0;

describe("today's raise", () => {
  it('adds a step to the daily limit', () => {
    expect(todayLimit(10, raised(null, NOON, UTC), NOON, UTC)).toBe(10 + NEW_STEP);
  });
  it('accumulates within one day', () => {
    const twice = raised(raised(null, NOON, UTC), NOON + 3_600_000, UTC);
    expect(twice.extra).toBe(2 * NEW_STEP);
  });
  it('ends at the 04:00 rollover', () => {
    const raise = raised(null, NOON, UTC);
    const nextMorning = Date.UTC(2026, 10, 11, 4, 1);
    expect(todayLimit(10, raise, nextMorning, UTC)).toBe(10);
  });
  it('still counts before the rollover', () => {
    const raise = raised(null, NOON, UTC);
    const lateNight = Date.UTC(2026, 10, 11, 3, 59);
    expect(todayLimit(10, raise, lateNight, UTC)).toBe(10 + NEW_STEP);
  });
  it("starts afresh from yesterday's raise", () => {
    const yesterday = raised(null, NOON - 24 * 3_600_000, UTC);
    expect(raised(yesterday, NOON, UTC)).toEqual({ day: dayStart(NOON, UTC), extra: NEW_STEP });
  });
});
