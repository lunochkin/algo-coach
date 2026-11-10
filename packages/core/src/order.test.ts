import { describe, expect, it } from 'vitest';

import { bySavedOrder, moduleOrder, moved, withFirst } from './order';

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

describe('withFirst', () => {
  it('moves the opened course to the front and keeps the saved order for the rest', () => {
    expect(withFirst(bySavedOrder(['a', 'b', 'c'], slug, ['c', 'a', 'b']), slug, 'b')).toEqual(['b', 'c', 'a']);
  });
  it('leaves the order unchanged when the slug is absent', () => {
    expect(withFirst(['a', 'b'], slug, 'x')).toEqual(['a', 'b']);
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
