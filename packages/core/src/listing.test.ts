import { describe, expect, it } from 'vitest';

import { clearFilters, listingView, NO_FILTER, toggled, type components } from './index';

type Listed = components['schemas']['Listed'];

const problem = (id: string, techniques: string[], difficulty: Listed['difficulty'] = 'easy'): Listed =>
  ({
    problem_id: id,
    title: id,
    difficulty,
    techniques,
    attempt_count: 0,
    solved_count: 0,
    last_attempt_at: null,
  }) as Listed;

const listed = [problem('a', ['dp', 'greedy'], 'easy'), problem('b', ['dp'], 'hard'), problem('c', ['bfs'], 'hard')];

describe('the problem listing', () => {
  it('shows a problem carrying any tag picked, at any difficulty asked for', () => {
    const view = listingView(listed, { techniques: ['dp', 'bfs'], difficulties: ['hard'], page: 1 });
    expect(view.rows.map((one) => one.problem_id)).toEqual(['b', 'c']);
  });

  it('counts on each chip what pressing it would leave', () => {
    const view = listingView(listed, { techniques: ['dp'], difficulties: ['hard'], page: 1 });
    expect(view.difficulties.map((one) => [one.name, one.count])).toEqual([
      ['easy', 1],
      ['medium', 0],
      ['hard', 1],
    ]);
    expect(view.tags.map((one) => [one.name, one.count])).toEqual([
      ['dp', 1],
      ['bfs', 1],
      ['greedy', 0],
    ]);
  });

  it('keeps the tags in the whole listing order, so no chip moves', () => {
    const view = listingView(listed, { techniques: [], difficulties: ['hard'], page: 1 });
    expect(view.tags.map((one) => one.name)).toEqual(['dp', 'bfs', 'greedy']);
  });

  it('pages twenty rows at a time, and holds a page past the end to the last', () => {
    const many = Array.from({ length: 45 }, (_, i) => problem(`p${i}`, ['dp']));
    const view = listingView(many, { ...NO_FILTER, page: 9 });
    expect([view.page, view.pages, view.rows.length]).toEqual([3, 3, 5]);
  });

  it('drills the one tag picked, and none where several are', () => {
    expect(listingView(listed, { ...NO_FILTER, techniques: ['dp'] }).drilled).toBe('dp');
    expect(listingView(listed, { ...NO_FILTER, techniques: ['dp', 'bfs'] }).drilled).toBeNull();
  });

  it('returns to the first page when a filter is pressed', () => {
    const filter = toggled({ ...NO_FILTER, page: 3 }, 'difficulties', 'easy');
    expect(filter).toEqual({ techniques: [], difficulties: ['easy'], page: 1 });
    expect(toggled(filter, 'difficulties', 'easy').difficulties).toEqual([]);
    expect(clearFilters(filter)).toBe('Clear the filter');
  });
});
