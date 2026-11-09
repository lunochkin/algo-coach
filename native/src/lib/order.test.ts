import { describe, expect, it } from 'vitest';

import { bySavedOrder, withFirst } from './order';

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
