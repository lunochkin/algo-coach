import { describe, expect, it } from 'vitest';

import { syncErrorSummary } from './syncError';

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
