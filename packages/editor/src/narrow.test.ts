import { describe, expect, it } from 'vitest';

import { hangStyle, leadingSpaces } from './narrow';

describe('the narrow indent', () => {
  it('counts the spaces a line opens with, and nothing after the first character', () => {
    expect(leadingSpaces('        x = 1')).toBe(8);
    expect(leadingSpaces('x =    1')).toBe(0);
  });

  it('hangs a wrap two characters under a line drawn at half its indent', () => {
    expect(hangStyle(8)).toBe('padding-left: calc(6ch + 6px); text-indent: -6ch');
    expect(hangStyle(0)).toBe('padding-left: calc(2ch + 6px); text-indent: -2ch');
  });
});
