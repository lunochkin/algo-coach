import { describe, expect, it } from 'vitest';

import {
  meLine,
  moduleStats,
  named,
  refusal,
  settingRange,
  signInUnread,
  signOutWarning,
  waitingToSend,
} from './home';

describe('home words', () => {
  it('counts a module row due first, then its questions', () => {
    expect(moduleStats(3, 1)).toEqual([
      { value: 3, label: 'due' },
      { value: 1, label: 'question' },
    ]);
    expect(moduleStats(0, 12)[1]).toEqual({ value: 12, label: 'questions' });
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

  it('names a user by the verified address, else by the engine id', () => {
    expect(named({ email: 'a@example.invalid', user_id: 'u-4f9c2a' })).toBe('a@example.invalid');
    expect(named({ email: null, user_id: 'u-4f9c2a' })).toBe('u-4f9c2a');
    expect(named(undefined)).toBe('Signed in');
  });

  it('reads the engine id under an address, and why there is none without one', () => {
    expect(meLine({ email: 'a@example.invalid', user_id: 'u-4f9c2a' })).toBe('u-4f9c2a');
    expect(meLine({ email: null, user_id: 'u-4f9c2a' })).toBe('Signed in with no provider linked');
    expect(meLine(undefined)).toBe('Reading the session…');
  });

  it('says the sign-in needs a connection when the network is down', () => {
    expect(signInUnread('Network request failed')).toBe('No connection. The sign-in is read from the engine.');
    expect(signInUnread('/sign-in 500: boom')).toBe('The sign-in did not load: /sign-in 500: boom');
  });

  it('reads a setting range from the engine bounds', () => {
    expect(settingRange('new_per_day')).toBe('0 to 200');
  });
});
