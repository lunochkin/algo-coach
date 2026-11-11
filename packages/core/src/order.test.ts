import { describe, expect, it } from 'vitest';

import type { Board } from './schedule';
import type { Course } from './types';
import { bySavedOrder, modulesInOrder, moduleOrder, moved } from './order';

const slug = (s: string) => s;

describe('bySavedOrder', () => {
  it('applies the saved order', () => {
    expect(bySavedOrder(['a', 'b', 'c'], slug, ['c', 'a', 'b'])).toEqual(['c', 'a', 'b']);
  });
  it('puts courses missing from the saved order last, in original order', () => {
    expect(bySavedOrder(['a', 'b', 'c', 'd'], slug, ['c'])).toEqual(['c', 'a', 'b', 'd']);
  });
  it('ignores saved slugs that no longer exist', () => {
    expect(bySavedOrder(['a', 'b'], slug, ['gone', 'b'])).toEqual(['b', 'a']);
  });
  it('keeps the original order without a saved order', () => {
    expect(bySavedOrder(['b', 'a'], slug, [])).toEqual(['b', 'a']);
  });
});

describe('moduleOrder', () => {
  it('is empty where no device set one', () => {
    expect(moduleOrder([])).toEqual([]);
  });
  it('is the latest set, whatever order the records arrived in', () => {
    const later = { t: '2026-11-10T12:00:00Z', courses: ['b', 'a'] };
    expect(moduleOrder([later, { t: '2026-11-10T11:00:00Z', courses: ['a', 'b'] }])).toEqual(['b', 'a']);
  });
});

describe('moved', () => {
  it('moves one slug and keeps the rest in order', () => {
    expect(moved(['a', 'b', 'c'], 2, 0)).toEqual(['c', 'a', 'b']);
    expect(moved(['a', 'b', 'c'], 0, 1)).toEqual(['b', 'a', 'c']);
  });
});

describe('modulesInOrder', () => {
  it('keeps the admitted modules in the saved order, each with its own board, and drops one with none', () => {
    const courses = ['a', 'b', 'c', 'd'].map((slug) => ({ slug, keep: slug !== 'b' }) as unknown as Course);
    const boards = new Map(['a', 'c'].map((slug) => [slug, { slug } as unknown as Board]));
    const got = modulesInOrder(
      courses,
      ['c', 'a'],
      (s) => boards.get(s),
      (c) => (c as unknown as { keep: boolean }).keep,
    );
    expect(got.map((m) => [m.c.slug, (m.b as unknown as { slug: string }).slug])).toEqual([
      ['c', 'c'],
      ['a', 'a'],
    ]);
  });
});
