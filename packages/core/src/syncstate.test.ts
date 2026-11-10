import { describe, expect, it } from 'vitest';

import { syncErrorSummary, syncLine } from './syncstate';

describe('syncErrorSummary', () => {
  it('points to Settings once the token is gone', () => {
    expect(syncErrorSummary('signed out: sign in again in Settings')).toBe('Not signed in: sign in from Settings');
  });
  it('points to Settings without an engine address', () => {
    expect(syncErrorSummary('no engine address: set one in Settings')).toBe('No engine address: set one in Settings');
  });
  it('recognises being offline', () => {
    expect(syncErrorSummary('TypeError: Network request failed')).toBe('Offline · retrying automatically');
  });
  it('falls back to a generic line', () => {
    expect(syncErrorSummary('something else')).toBe('Sync failed · retrying automatically');
  });
});

describe('syncLine', () => {
  const now = Date.parse('2026-11-10T12:00:00Z');
  it('names when the last sync finished', () => {
    expect(syncLine({ running: false, lastAt: '2026-11-10T11:57:00Z' }, now)).toBe('Synced 3 min ago');
  });
  it('says so while one runs, and before the first', () => {
    expect(syncLine({ running: true, lastAt: null }, now)).toBe('Syncing…');
    expect(syncLine({ running: false, lastAt: null }, now)).toBe('Not synced yet');
  });
});
