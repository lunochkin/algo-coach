import { describe, expect, it } from 'vitest';

import { isExternal } from './pages';

describe('isExternal', () => {
  it('marks a web address and leaves an in-app link', () => {
    expect(['https://docs.python.org/3/', 'http://x.org', 'lesson:loops#for', '#anchor'].map(isExternal)).toEqual([
      true,
      true,
      false,
      false,
    ]);
  });
});
