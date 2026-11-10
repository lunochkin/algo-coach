import { describe, expect, it } from 'vitest';

import { deviceLine, deviceName, lastAt } from './index';

const NOW = Date.parse('2026-11-10T12:00:00Z');

describe("a signed-in device's line", () => {
  it('names the day it was last used and the day it signed in', () => {
    expect(deviceLine({ last_used_at: '2026-11-10T08:00:00Z', created_at: '2026-11-03T08:00:00Z' }, NOW)).toBe(
      'used today · signed in 7 days ago',
    );
  });

  it('reads a day never reached as never', () => {
    expect(lastAt(null, NOW)).toBe('never');
    expect(lastAt('2026-11-09T11:00:00Z', NOW)).toBe('yesterday');
    expect(lastAt('2026-10-05T12:00:00Z', NOW)).toBe('a month ago');
    expect(lastAt('2026-09-05T12:00:00Z', NOW)).toBe('2 months ago');
  });
});

describe("a signed-in device's name", () => {
  it('names an app by its device', () => {
    expect(deviceName({ kind: 'app', name: 'phone' })).toBe('phone');
  });

  it("names a browser by its agent's browser and system", () => {
    const chrome = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Safari/537.36';
    expect(deviceName({ kind: 'browser', name: chrome })).toBe('Chrome on macOS');
    expect(deviceName({ kind: 'browser', name: 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/150.0' })).toBe('Firefox on Linux');
  });

  it('names a browser it cannot read plainly', () => {
    expect(deviceName({ kind: 'browser', name: null })).toBe('A browser');
  });
});
