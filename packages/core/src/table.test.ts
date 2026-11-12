import { describe, expect, it } from 'vitest';

import { isTable, tableShape } from './table';

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

describe('a markdown table', () => {
  it('is a header, a rule and rows, each line between bars', () => {
    expect(isTable('| a | b |\n|:--|--:|\n| 1 | 2 |\n')).toBe(true);
  });

  it('needs the rule under its header', () => {
    expect(isTable('| a | b |\n| 1 | 2 |')).toBe(false);
  });

  it('is the whole text, with no line around it', () => {
    expect(isTable('a table:\n| a |\n|---|')).toBe(false);
    expect(isTable('| a |\n|---|\nafter')).toBe(false);
  });
});
