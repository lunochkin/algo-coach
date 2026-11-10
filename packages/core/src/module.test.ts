import { describe, expect, it } from 'vitest';

import { Board, focusLabel, focusLine, groupCell, levelCounts, loadSnapshot, startPreview } from './index';

const mk = (id: string, sub: string, level: number) => ({
  id, topic: 't', sub, level, kind: 'concept', prompt: id, format: 'choice' as const,
  choices: ['a', 'b', 'c'], answer: ['A'],
});
const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'c',
      definition: {
        title: 'C', pass_ratio: 1, kinds: ['concept'],
        topic: [{ slug: 't', tier: 1, title: 'Types', subs: ['s1', 's2'], sub_titles: { s1: 'Ints' } }],
      },
      questions: [mk('a', 's1', 0), mk('b', 's1', 0), mk('c', 's1', 1), mk('d', 's2', 0)],
    },
  ],
} as never);
const T = '2026-11-10T08:00:00.000Z';
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const g = (sub: string, level: number) => ({ course: 'c', topic: 't', sub, level });

describe('a group cell', () => {
  const b = Board.build(catalog, [{ t: T, course: 'c', id: 'd', ok: true }]);

  it('reads a group with every question passed as covered', () => {
    expect(groupCell(b, g('s2', 0))).toMatchObject({ state: 'covered', count: '1/1', line: '1/1 · covered' });
  });

  it('reads an open group by its passed share', () => {
    expect(groupCell(b, g('s1', 0))).toMatchObject({ state: 'open', count: '0/2', line: '0/2 · open' });
  });

  it('names what a locked group waits for', () => {
    const cell = groupCell(b, g('s1', 1));
    expect(cell.state).toBe('locked');
    expect(cell.line).toBe(`0/1 · ${cell.needs || 'locked'}`);
  });

  it('marks a group holding no questions', () => {
    expect(groupCell(b, g('s2', 1))).toMatchObject({ state: 'empty', count: '·', line: 'no questions' });
  });
});

describe('the counts per level', () => {
  it('sum the passed questions over every subtopic of the module', () => {
    const b = Board.build(catalog, [{ t: T, course: 'c', id: 'd', ok: true }]);
    expect(levelCounts(b, b.courses[0]).slice(0, 2)).toEqual([
      { level: 0, name: 'Foundation', passed: 1, total: 3 },
      { level: 1, name: 'Associate', passed: 0, total: 1 },
    ]);
  });
});

describe('the start sheet', () => {
  it('counts what its choices leave, and names the press', () => {
    const b = Board.build(catalog, []);
    expect(startPreview(b, { course: 'c', topic: 't', sub: 's1', level: 0 }, 10, NOW)).toMatchObject({
      reviews: 0, newLeft: 10, empty: false, label: 'Start · 0 reviews · 10 new',
    });
  });

  it('says so where nothing is ready', () => {
    const b = Board.build(catalog, []);
    expect(startPreview(b, { course: 'c', due: true }, 10, NOW).label).toBe('Nothing ready here');
  });
});

describe('the focus label', () => {
  it('names the topic and the subtopic by their titles', () => {
    expect(focusLabel({ course: 'c', topic: 't', sub: 's1' }, catalog)).toBe('C › Types › Ints');
  });
});

describe('the focus record', () => {
  it('clears the focus where none is given', () => {
    expect(focusLine(null)).toEqual({ course: null, topic: null, sub: null, strict: false });
  });

  it('names a certification only on a certification focus', () => {
    expect(focusLine({ course: 'c', topic: 't', sub: null, strict: true, cert: 'c-t-associate' })).toEqual({
      course: 'c', topic: 't', sub: null, strict: true, cert: 'c-t-associate',
    });
  });
});
