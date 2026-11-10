import { describe, expect, it } from 'vitest';

import { moduleCounts, refusal, settingRange, signOutWarning, waitingToSend } from './home';

describe('home words', () => {
  it('counts a module row due first, then its questions', () => {
    expect(moduleCounts(3, 1)).toBe('3 due · 1 question');
    expect(moduleCounts(0, 12)).toBe('0 due · 12 questions');
  });

  it('counts the records waiting to be sent', () => {
    expect(waitingToSend(1)).toBe('1 record waits to be sent');
    expect(waitingToSend(4)).toBe('4 records wait to be sent');
  });

  it('names the unsent records and the device signing out', () => {
    expect(signOutWarning(1, 'browser')).toBe(
      'One record did not reach the engine. Signing out now deletes it from this browser.',
    );
    expect(signOutWarning(3, 'phone')).toBe(
      '3 records did not reach the engine. Signing out now deletes them from this phone.',
    );
  });

  it('reads an unknown refusal as an incomplete sign-in', () => {
    expect(refusal('uninvited')).toBe('That address has no invitation.');
    expect(refusal('something-new')).toBe(refusal('incomplete'));
  });

  it('reads a setting range from the engine bounds', () => {
    expect(settingRange('new_per_day')).toBe('0 to 200');
  });
});
