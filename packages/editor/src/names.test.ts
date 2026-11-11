import { describe, expect, it } from 'vitest';

import { declaredNames, offered, wordBefore } from './names';

describe('the names a file declares', () => {
  it('reads every kind of binding, once each, in the order it appears', () => {
    const code = [
      'from bisect import bisect_left',
      'def solve(nums, k=1, *rest, **kw):',
      '    lo, hi = 0, len(nums)',
      '    for i, x in enumerate(nums):',
      '        seen = {y for y in nums}',
      '    with open(nums) as fh:',
      '        pass',
      '    if (m := 3):',
      '        pass',
      '    f = lambda a, b: a',
      '    return [z for z in nums if z]',
    ].join('\n');
    expect(declaredNames(code)).toEqual([
      'bisect',
      'bisect_left',
      'solve',
      'nums',
      'k',
      'rest',
      'kw',
      'lo',
      'hi',
      'i',
      'x',
      'seen',
      'y',
      'fh',
      'm',
      'f',
      'a',
      'b',
      'z',
    ]);
  });

  it('never offers a name the file only reads', () => {
    const names = declaredNames('def solve(a):\n    b = a\n    return len(sorted(b))');
    expect(names).toEqual(['solve', 'a', 'b']);
  });

  it('reads a file cut off mid-line, as one being typed is', () => {
    expect(declaredNames('def solve(nums):\n    total = 0\n    for i in ra')).toEqual(['solve', 'nums', 'total', 'i']);
  });
});

describe('the row', () => {
  it('narrows to the word being typed, and leaves the word itself out', () => {
    const names = ['nums', 'n', 'prefix', 'prev'];
    expect(offered(names, '')).toEqual(names);
    expect(offered(names, 'pre')).toEqual(['prefix', 'prev']);
    expect(offered(names, 'prev')).toEqual([]);
    expect(wordBefore('    total = pre')).toBe('pre');
    expect(wordBefore('    total = ')).toBe('');
    expect(wordBefore('x[i1')).toBe('i1');
  });
});
