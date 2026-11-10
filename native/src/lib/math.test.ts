import { describe, expect, it } from 'vitest';

import { texText, withMath } from './math';

describe('a formula read as text', () => {
  it('reads the comparisons, the text and the powers', () => {
    expect(texText('0 \\le \\text{len}(a), \\text{len}(b) \\le 2 \\times 10^5')).toBe('0 ≤ len(a), len(b) ≤ 2 × 10⁵');
    expect(texText('-10^9 \\le a[i], b[i] \\le 10^9')).toBe('-10⁹ ≤ a[i], b[i] ≤ 10⁹');
    expect(texText('0 \\le k < \\text{len}(readings)')).toBe('0 ≤ k < len(readings)');
  });

  it('keeps a script no Unicode character carries as its source', () => {
    expect(texText('x_{ij}')).toBe('xᵢⱼ');
    expect(texText('2^{w}')).toBe('2^w');
    expect(texText('\\{1, 2\\}')).toBe('{1, 2}');
  });

  it('leaves an unknown command as written', () => {
    expect(texText('\\binom{n}{k}')).toBe('\\binomnk');
  });
});

describe('math in a statement', () => {
  it('converts the formulas and leaves the code alone', () => {
    expect(withMath('The rank $k$ is $1 \\le k$, and `$x$` stays.')).toBe('The rank k is 1 ≤ k, and `$x$` stays.');
  });

  it('leaves a dollar followed by a space alone', () => {
    expect(withMath('It costs $ 5 and $ 6.')).toBe('It costs $ 5 and $ 6.');
  });
});
