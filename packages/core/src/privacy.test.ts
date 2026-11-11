import { describe, expect, it } from 'vitest';

import { privacyPolicy } from './index';

describe('the privacy policy', () => {
  it('reads its title and date into the header and leaves the prose', () => {
    const policy = privacyPolicy('# Privacy policy\n\nLast updated: 15 September 2026\n\nBody.\n');
    expect(policy).toEqual({ title: 'Privacy policy', updated: '15 September 2026', body: 'Body.\n' });
  });

  it('holds the text both clients render', () => {
    expect(privacyPolicy().title).toBe('Privacy policy');
    expect(privacyPolicy().updated).not.toBeNull();
  });
});
