import { describe, expect, it } from 'vitest';

import { codeLines, codeRows, codeWraps } from './code';

describe('code blocks', () => {
  it('wraps a named language and keeps a diagram whole', () => {
    expect(codeWraps('python')).toBe(true);
    expect(codeWraps('text')).toBe(false);
    expect(codeWraps(undefined)).toBe(false);
  });

  it('splits each line at its indent', () => {
    expect(codeLines('for x in xs:\n    print(x)\n\n')).toEqual([
      { indent: '', text: 'for x in xs:' },
      { indent: '    ', text: 'print(x)' },
    ]);
  });

  it('keeps a line that fits as one row', () => {
    expect(codeRows('    print(x)', 20)).toEqual([
      { line: 0, indent: '    ', from: 0, text: 'print(x)', cont: false, gap: '' },
    ]);
  });

  it('breaks a long line at a space, the rest marked and under its indent', () => {
    const rows = codeRows('    total = first + second + third', 26);
    expect(rows.map((r) => [r.text, r.cont])).toEqual([
      ['total = first + second', false],
      ['+ third', true],
    ]);
    expect(rows[0].gap).toBe(' ');
    expect(rows[1]).toMatchObject({ indent: '    ', from: 23 });
  });

  it('breaks at punctuation where a line has no space near the edge', () => {
    expect(codeRows('print(list(zip(names,[36,54])))', 20).map((r) => r.text)).toEqual([
      'print(list(zip',
      '(names,[36,54])))',
    ]);
  });

  it('cuts a word with no space near the edge', () => {
    expect(codeRows('x' + 'y'.repeat(29), 20).map((r) => r.text.length)).toEqual([20, 10]);
  });
});
