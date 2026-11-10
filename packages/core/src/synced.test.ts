import { describe, expect, it } from 'vitest';

import { syncedLine } from './index';

const T = '2026-11-10T10:00:00+00:00';

describe('a record the sync returned', () => {
  it("splits into the merge's fields and learn's line", () => {
    const line = syncedLine({ kind: 'attempt', client_id: 'c1', device: 'phone', t: T, course: 'python', id: 'q', ok: true });
    expect(line).toEqual({
      kind: 'attempt',
      client_id: 'c1',
      device: 'phone',
      t: T,
      rest: { t: T, course: 'python', id: 'q', ok: true },
    });
  });
  it.each([
    [{ client_id: 'c1', device: 'phone', t: T }],
    [{ kind: 'attempt', device: 'phone', t: T }],
    [{ kind: 'attempt', client_id: 'c1', t: T }],
    [{ kind: 'attempt', client_id: 'c1', device: 'phone' }],
    [{ kind: 'attempt', client_id: 7, device: 'phone', t: T }],
  ])('is skipped where a field the merge reads is missing or not text: %o', (record) => {
    expect(syncedLine(record)).toBeNull();
  });
});
