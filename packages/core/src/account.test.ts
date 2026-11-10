import { describe, expect, it } from 'vitest';

import { appLine, lastAt } from './index';

const NOW = Date.parse('2026-11-10T12:00:00Z');

describe("a signed-in app's line", () => {
  it('names the day it was last used and the day it signed in', () => {
    expect(appLine({ last_used_at: '2026-11-10T08:00:00Z', created_at: '2026-11-03T08:00:00Z' }, NOW)).toBe(
      'used today · signed in 7 days ago',
    );
  });

  it('reads a day never reached as never', () => {
    expect(lastAt(null, NOW)).toBe('never');
    expect(lastAt('2026-11-09T11:00:00Z', NOW)).toBe('yesterday');
  });
});
