import { describe, expect, it } from 'vitest';

import { Board, lessonGroups, lessonRow, lessonsAround, lessonStopNote, loadSnapshot, readyLesson, withLessons } from './index';

const mk = (id: string, sub: string, level: number) => ({
  id, topic: 't', sub, level, kind: 'concept', prompt: id, format: 'choice' as const,
  choices: ['a', 'b', 'c'], answer: ['A'],
});
const lesson = (title: string, teaches: string[], needs: string[] = [], pretest = 0) => ({
  title, file: `lessons/${title}.md`, teaches, needs, pretest,
});
const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'm',
      definition: {
        title: 'M', pass_ratio: 1, kinds: ['concept'],
        topic: [{ slug: 't', tier: 1, title: 'T', subs: ['a', 'b'], sub_titles: { a: 'Ints' } }],
      },
      questions: [mk('q1', 'a', 0), mk('q2', 'b', 0)],
      graph: {
        format: 2,
        needs: { b: ['a'] },
        lesson: { first: lesson('first', ['a@0']), second: lesson('second', ['b@0'], ['lesson:first']) },
      },
      lesson_bodies: { first: 'word '.repeat(450), second: 'text' },
    },
  ],
} as never);
const [c] = catalog.courses;
const T = '2026-11-10T08:00:00.000Z';

describe('the lessons', () => {
  it('splits a module into lessons to read and lessons still locked', () => {
    const groups = lessonGroups(Board.build(catalog, []), c);
    expect(groups.map((g) => [g.key, g.lessons.map((x) => x.title)])).toEqual([
      ['toRead', ['first']],
      ['locked', ['second']],
    ]);
  });

  it("names a lesson's minutes, what it teaches and what it waits for", () => {
    const b = Board.build(catalog, []);
    expect(lessonRow(b, c, c.graph!.lesson('first')!)).toMatchObject({
      state: 'available', minutes: 3, teaches: 'Teaches Ints · Foundation', status: 'Ready to read',
    });
    // the lesson waits for the lesson it needs, and for the group its own group needs done
    expect(lessonRow(b, c, c.graph!.lesson('second')!).status).toBe('Needs first, a · Foundation');
  });

  it('reads a lesson read once its mark says so', () => {
    const marked = withLessons(catalog, [{ t: T, course: 'm', lesson: 'first', status: 'done' }]);
    const b = Board.build(marked, []);
    expect(lessonRow(b, c, c.graph!.lesson('first')!).status).toBe('Read');
  });

  it('offers the lessons that need this one, after its text', () => {
    expect(lessonsAround(c, 'first').next.map((x) => x.title)).toEqual(['second']);
  });

  it('names the first lesson ready to read, with its minutes', () => {
    expect(readyLesson(Board.build(catalog, []), [])?.line).toBe('Ready to read: first · ~3 min');
  });

  it('says why a queue stops on a lesson', () => {
    expect(lessonStopNote(false)).toMatch(/^You have tried a few questions/);
    expect(lessonStopNote(true)).toMatch(/^Read\./);
  });
});
