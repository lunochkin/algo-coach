import { describe, expect, it } from 'vitest';

import { tableShape } from './table';

describe('table shape', () => {
  const header = ['method', '0 rows', '2+ rows'];
  const rows = [
    ['scalar_one()', 'NoResultFound', 'MultipleResultsFound'],
    ['first()', 'None', 'first row'],
  ];

  it('reads as a grid where the longest cells fit side by side', () => {
    // 12 + 13 + 20, and a gap of 2 between each pair of columns
    expect(tableShape(header, rows, 49)).toBe('grid');
  });

  it('reads as one block per row where they do not', () => {
    expect(tableShape(header, rows, 48)).toBe('rows');
  });

  it('counts a header longer than its cells', () => {
    expect(tableShape(['a long header', 'b'], [['x', 'y']], 15)).toBe('rows');
  });
});
