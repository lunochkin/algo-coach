import { describe, expect, it } from 'vitest';

import { Board, loadSnapshot, nextQueue } from './index';

const mk = (id: string, sub: string) => ({
  id, topic: 't', sub, level: 0, kind: 'k', prompt: id, format: 'choice' as const,
  choices: ['a', 'b', 'c'], answer: ['A'],
});
const course = (extra: object = {}) =>
  loadSnapshot({
    format: 6,
    courses: [
      {
        slug: 'c',
        definition: { title: 'C', pass_ratio: 1, kinds: ['k'], topic: [{ slug: 't', tier: 1, title: 'T', subs: ['s1', 's2'] }] },
        questions: [mk('a', 's1'), mk('b', 's2')],
        ...extra,
      },
    ],
  } as never);
const T = new Date(Date.UTC(2026, 10, 10, 12)).toISOString();

describe('next up', () => {
  it('passes over a group whose questions are all seen but not passed', () => {
    // `a` missed: s1 is still on the frontier, and it has nothing new to introduce
    const b = Board.build(course(), [{ t: T, course: 'c', id: 'a', ok: false }]);
    const [c] = b.courses;
    expect(b.frontier(c)[0].sub).toBe('s1');
    expect(b.nextNew(c)?.sub).toBe('s2');
    expect(b.nextUp(c)).toMatchObject({ group: { sub: 's2' }, lesson: null });
  });

  it('is the group Continue introduces its new question from', () => {
    const b = Board.build(course(), [{ t: T, course: 'c', id: 'a', ok: false }]);
    // half a minute after the miss, `a` waits on its step, so Continue's pick is a new question
    const q = nextQueue(b, 10).pick(b, Date.parse(T) + 30_000);
    expect(q && 'id' in q ? q.sub : null).toBe(b.nextNew(b.courses[0])?.sub);
  });

  it('names the lesson where every open group waits for one', () => {
    const lesson = { title: 'Names', file: 'lessons/names.md', teaches: ['s1@0', 's2@0'], needs: [], pretest: 0 };
    const b = Board.build(course({ graph: { format: 2, lesson: { names: lesson } }, lesson_bodies: { names: '# Names' } }), []);
    expect(b.nextUp(b.courses[0])).toMatchObject({ lesson: { slug: 'names' } });
  });

  it('is nothing once every open group is done', () => {
    const b = Board.build(course(), [
      { t: T, course: 'c', id: 'a', ok: true },
      { t: T, course: 'c', id: 'b', ok: true },
    ]);
    expect(b.nextUp(b.courses[0])).toBeNull();
  });
});
