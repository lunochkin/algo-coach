import { describe, expect, it } from 'vitest';

import { learnerLog, learnerView, loadSnapshot, type LearnerLog } from './index';

const mk = (id: string) => ({
  id,
  topic: 't',
  sub: 's1',
  level: 0,
  kind: 'concept',
  prompt: id,
  format: 'choice' as const,
  choices: ['a', 'b', 'c'],
  answer: ['A'],
});
const module = (slug: string) => ({
  slug,
  definition: {
    title: slug.toUpperCase(),
    pass_ratio: 1,
    kinds: ['concept'],
    topic: [{ slug: 't', tier: 1, title: 'Types', subs: ['s1'] }],
  },
  questions: [mk(`${slug}1`), mk(`${slug}2`)],
});
const snapshot = loadSnapshot({ format: 6, courses: [module('a'), module('b')] } as never);
const T = '2026-11-10T08:00:00.000Z';
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const empty = learnerLog([]);
const log = (part: Partial<LearnerLog>): LearnerLog => ({ ...empty, ...part });

describe("the learner's view", () => {
  it('hides an archived module and lists it for restoring', () => {
    const v = learnerView(snapshot, log({ statuses: [{ t: T, course: 'b', status: 'archived' }] }));
    expect(v.catalog!.courses.map((c) => c.slug)).toEqual(['a']);
    expect(v.archived.map((c) => c.slug)).toEqual(['b']);
  });

  it('reads the latest focus against the visible catalog', () => {
    const v = learnerView(
      snapshot,
      log({
        focuses: [{ t: T, course: 'a', topic: null, sub: null }],
        statuses: [{ t: T, course: 'a', status: 'archived' }],
      }),
    );
    expect(v.focus).toBeNull();
  });

  it('builds a board over one module or every one', () => {
    const v = learnerView(snapshot, empty);
    expect(v.board('a')!.courses.map((c) => c.slug)).toEqual(['a']);
    expect(v.board(null)!.courses.map((c) => c.slug)).toEqual(['a', 'b']);
  });

  it("adds today's raises to the daily limit, read at the moment given", () => {
    const v = learnerView(snapshot, log({ settings: [{ t: T, name: 'new_per_day', n: 3 }], raises: [{ t: T, n: 5 }] }));
    expect(v.newPerDay).toBe(3);
    expect(v.limitAt(NOW)).toBe(8);
    expect(v.limitAt(NOW + 24 * 3600_000)).toBe(3);
  });

  it('reads the settings and the order from their latest records', () => {
    const v = learnerView(
      snapshot,
      log({
        settings: [{ t: T, name: 'exam_size', n: 12 }],
        orders: [
          { t: T, courses: ['a', 'b'] },
          { t: '2026-11-10T09:00:00.000Z', courses: ['b', 'a'] },
        ],
      }),
    );
    expect(v.examSize).toBe(12);
    expect(v.order).toEqual(['b', 'a']);
  });
});

describe('the learner before the snapshot', () => {
  it('reads the limit and the order with no catalog', () => {
    const v = learnerView(null, log({ raises: [{ t: T, n: 5 }], orders: [{ t: T, courses: ['b'] }] }));
    expect(v.catalog).toBeNull();
    expect(v.board(null)).toBeNull();
    expect(v.limitAt(NOW)).toBe(15);
    expect(v.order).toEqual(['b']);
  });
});

describe('the log from tagged lines', () => {
  it('sorts each line into its kind and drops a kind the learner reads nothing from', () => {
    const l = learnerLog([
      { kind: 'raise', line: { t: T, n: 5 } },
      { kind: 'session', line: { t: T } },
      { kind: 'order', line: { t: T, courses: ['b'] } },
    ]);
    expect(l.raises).toEqual([{ t: T, n: 5 }]);
    expect(l.orders).toEqual([{ t: T, courses: ['b'] }]);
    expect(l.attempts).toEqual([]);
  });
});
