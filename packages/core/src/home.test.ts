import { describe, expect, it } from 'vitest';

import {
  Board,
  continueCounts,
  continuePlan,
  focusView,
  learnerCatalog,
  loadSnapshot,
  moduleRows,
  queueStart,
  type AttemptRecord,
  type Catalog,
} from './index';

const mk = (id: string, sub: string) => ({
  id,
  topic: 't',
  sub,
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
    topic: [{ slug: 't', tier: 1, title: 'Types', subs: ['s1', 's2'], sub_titles: { s1: 'Ints' } }],
  },
  questions: [mk(`${slug}1`, 's1'), mk(`${slug}2`, 's1'), mk(`${slug}3`, 's2')],
});
const snapshot = loadSnapshot({ format: 6, courses: [module('a'), module('b')] } as never);
const T = '2026-11-10T08:00:00.000Z';
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const none = { statuses: [], lessons: [], certs: [] };
const boardOf =
  (cat: Catalog, attempts: AttemptRecord[] = []) =>
  (only: string | null, include?: string | null) =>
    Board.build(cat, attempts, only, include ?? null);

describe("the learner's catalog", () => {
  it('hides an archived module, and lists it for restoring', () => {
    const { catalog, archived } = learnerCatalog(snapshot, {
      ...none,
      statuses: [{ t: T, course: 'b', status: 'archived' }],
    });
    expect(catalog.courses.map((c) => c.slug)).toEqual(['a']);
    expect(archived.map((c) => c.slug)).toEqual(['b']);
  });
});

describe('what Continue opens', () => {
  const { catalog } = learnerCatalog(snapshot, none);
  const focus = { course: 'a', topic: null, sub: null };

  it('aims at the focus, serving its module while paused', () => {
    expect(continuePlan(boardOf(catalog), focus, null, 10)).toMatchObject({ queue: { kind: 'focus' }, include: 'a' });
  });

  it('sets the focus aside where a module is picked', () => {
    expect(continuePlan(boardOf(catalog), focus, 'b', 10)).toMatchObject({ queue: { kind: 'mix' }, course: 'b' });
  });

  it('counts the new questions the day allows', () => {
    const plan = continuePlan(boardOf(catalog), null, null, 2)!;
    expect(continueCounts(plan, null, NOW)).toMatchObject({ reviews: 0, newLeft: 2, empty: false, blocked: false });
  });

  it("says the day's limit alone empties it", () => {
    const plan = continuePlan(boardOf(catalog), null, null, 0)!;
    expect(continueCounts(plan, null, NOW)).toMatchObject({ newLeft: 0, empty: true, blocked: true });
  });

  it('counts the reviews a strict focus leaves out', () => {
    const wrong = [{ t: T, course: 'b', id: 'b1', ok: false }];
    const strict = { ...focus, strict: true };
    const plan = continuePlan(boardOf(catalog, wrong), strict, null, 10)!;
    expect(continueCounts(plan, strict, NOW).outside).toBe(1);
  });

  it('counts none outside a relaxed focus, which serves every review already', () => {
    const wrong = [{ t: T, course: 'b', id: 'b1', ok: false }];
    const plan = continuePlan(boardOf(catalog, wrong), focus, null, 10)!;
    expect(continueCounts(plan, focus, NOW).outside).toBe(0);
  });
});

describe("a queue's start by its mode", () => {
  const { catalog } = learnerCatalog(snapshot, none);
  const learner = { board: boardOf(catalog), focus: null, newLimit: 10 };

  it('drills its scope, reviews every module, and otherwise opens what Continue would', () => {
    expect(queueStart('drill', { course: 'b' }, learner)).toMatchObject({
      queue: { kind: 'drill', want: null },
      course: 'b',
    });
    expect(queueStart('review', null, learner)).toMatchObject({
      queue: { kind: 'review', want: ['weak', 'due'] },
      course: null,
    });
    expect(queueStart('next', null, learner)).toMatchObject({ queue: { kind: 'mix' }, course: null });
  });

  it('starts no drill without a scope', () => {
    expect(queueStart('drill', null, learner)).toBeNull();
  });
});

describe('the home', () => {
  const { catalog } = learnerCatalog(snapshot, none);

  it('counts each module and what it owes', () => {
    const b = Board.build(catalog, [{ t: T, course: 'a', id: 'a1', ok: false }]);
    expect(moduleRows(b, NOW).map((r) => [r.c.slug, r.total, r.toReview, r.passed])).toEqual([
      ['a', 3, 1, 0],
      ['b', 3, 0, 0],
    ]);
  });

  it('reads the focus panel: its parts, the group next, and what is owed now', () => {
    const focus = { course: 'a', topic: 't', sub: null };
    const plan = continuePlan(boardOf(catalog, [{ t: T, course: 'a', id: 'a1', ok: false }]), focus, null, 10)!;
    const v = focusView(plan.b, focus, plan.queue, [], NOW);
    expect(v.summary).toBe('3 questions · 1 to review · 2 unseen');
    expect(v.next).toBe('Ints · Foundation · 0/2');
    // the answer this morning met a1 for the first time, so it spent one of today's ten
    expect([v.due, v.newLeft, v.cert]).toEqual([1, 9, null]);
  });
});
