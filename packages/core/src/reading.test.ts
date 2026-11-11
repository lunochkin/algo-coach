import { describe, expect, it } from 'vitest';

import { copyReading, pageReading } from './index';

describe("a page's reading", () => {
  it('fails on a named error, loads while nothing arrived, and reads an empty list as blank', () => {
    expect(pageReading('the board', { error: 'down' }).kind).toBe('failed');
    expect(pageReading('the board', { data: null, error: '' }).kind).toBe('loading');
    expect(pageReading('the board', { data: [] }, 'Nothing yet')).toEqual({ kind: 'blank', line: 'Nothing yet' });
    expect(pageReading('the board', { data: [1] }, 'Nothing yet')).toEqual({ kind: 'content', data: [1] });
  });

  it('reads the copy once ready, and fails with the sync only while the copy holds nothing', () => {
    expect(copyReading(false, null, [1])).toEqual({ data: undefined, error: null });
    expect(copyReading(true, 'offline', null)).toEqual({ data: null, error: 'offline' });
    expect(copyReading(true, 'offline', [1])).toEqual({ data: [1], error: null });
  });
});
