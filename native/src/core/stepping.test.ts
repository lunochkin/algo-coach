import { describe, expect, it } from 'vitest';

import { Board, loadSnapshot, nextQueue } from './index';

const mk = (id: string) => ({
  id, topic: 't', sub: 's', level: 0, kind: 'k', prompt: id, format: 'choice' as const,
  choices: ['a', 'b', 'c'], answer: ['A'],
});
const cat = loadSnapshot({
  format: 2,
  courses: [
    {
      slug: 'c',
      definition: { title: 'C', pass_ratio: 1, kinds: ['k'], topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s'] }] },
      questions: [mk('a'), mk('b')],
    },
  ],
});
const T = Date.UTC(2026, 10, 10, 12);
// a miss on `a`, which puts it on a one-minute learning step
const missed = Board.build(cat, [{ t: new Date(T).toISOString(), course: 'c', id: 'a', ok: false }]);
const soon = T + 30_000;

describe('a learning step not due yet', () => {
  it('is counted apart from the due reviews', () => {
    const queue = nextQueue(missed, 0);
    expect(queue.reviews(missed, soon)).toHaveLength(0);
    expect(queue.stepping(missed, soon)).toEqual({ count: 1, nextAt: T + 60_000 });
  });
  it('is served early, and says so', () => {
    const queue = nextQueue(missed, 0);
    const q = queue.pick(missed, soon);
    expect(q && 'id' in q ? q.id : null).toBe('a');
    expect(queue.early(missed, q as never, soon)).toBe(true);
  });
  it('is no longer early once its step is due', () => {
    const queue = nextQueue(missed, 0);
    const later = T + 61_000;
    expect(queue.stepping(missed, later).count).toBe(0);
    expect(queue.reviews(missed, later)).toHaveLength(1);
  });
});
