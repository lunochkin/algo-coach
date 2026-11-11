import { levelName, subTitle } from './courses';
import type { Lesson } from './graph';
import { minutesOf } from './lessontext';
import { bySavedOrder } from './order';
import type { Board } from './schedule';
import type { Course } from './types';

/**
 * A group of one module's lessons, as a long page's section. The bar names
 * the module beside the group only where several modules hold lessons.
 */
export interface LessonSection {
  id: string;
  label: string;
  c: Course;
  b: Board;
  module: string | null; // the module's heading, on its first group alone
  inModule: number; // the lessons the module holds, which its heading counts
  title: string;
  lessons: Lesson[];
}

export function lessonSections(modules: readonly { c: Course; b: Board }[]): LessonSection[] {
  return modules.flatMap(({ c, b }) => {
    const groups = lessonGroups(b, c);
    const inModule = groups.reduce((n, g) => n + g.lessons.length, 0);
    return groups.map((g, i) => ({
      id: `${c.slug}-${g.key}`,
      label: modules.length > 1 ? `${c.title} · ${g.title}` : g.title,
      c,
      b,
      module: i === 0 ? c.title : null,
      inModule,
      title: g.title,
      lessons: g.lessons,
    }));
  });
}

/** Lessons in graph order: the shallowest subtopic taught and the lowest level first, then listing order. */
export function inGraphOrder(c: Course, lessons: Lesson[]): Lesson[] {
  const key = (x: Lesson) =>
    Math.min(...x.teaches.map(([s, l]) => (c.graph?.depth(s) ?? 0) * 10 + l), Number.MAX_SAFE_INTEGER);
  return lessons
    .map((x, i) => ({ x, i, k: key(x) }))
    .sort((a, b) => a.k - b.k || a.i - b.i)
    .map((e) => e.x);
}

export type LessonGroup = 'toRead' | 'read' | 'locked';

/** A module's lessons in graph order, split into those to read, those read and those still locked. */
export function lessonGroups(b: Board, c: Course): { key: LessonGroup; title: string; lessons: Lesson[] }[] {
  const all = inGraphOrder(c, c.graph?.lessons ?? []);
  const by = (state: string) => all.filter((x) => b.lessonState(c, x) === state);
  return [
    { key: 'toRead' as const, title: 'To read', lessons: by('available') },
    { key: 'read' as const, title: 'Read', lessons: by('done') },
    { key: 'locked' as const, title: 'Locked', lessons: by('locked') },
  ].filter((g) => g.lessons.length);
}

/** One lesson's row: its state, its minutes, the first group it teaches, and its status in words. */
export interface LessonRow {
  state: 'done' | 'available' | 'locked';
  minutes: number; // 0 where the snapshot holds no text yet
  teaches: string;
  status: string;
}

export function lessonRow(b: Board, c: Course, x: Lesson): LessonRow {
  const state = b.lessonState(c, x);
  const body = c.lessonBodies[x.slug] ?? '';
  const [sub, level] = x.teaches[0] ?? ['', 0];
  const more = x.teaches.length > 1 ? ` +${x.teaches.length - 1}` : '';
  const need = (r: string) =>
    r.startsWith('lesson:')
      ? (c.graph?.lesson(r.slice(7))?.title ?? r)
      : `${r.slice(0, r.lastIndexOf('@'))} · ${levelName(b.rules, Number(r.slice(r.lastIndexOf('@') + 1)))}`;
  const status =
    state === 'done'
      ? 'Read'
      : state === 'locked'
        ? `Needs ${b.unmetNeeds(c, x).map(need).join(', ')}`
        : b.lessonReady(c, x)
          ? 'Ready to read'
          : `Pretest ${Math.min(b.tried(c, x), x.pretest)}/${x.pretest}`;
  return {
    state,
    minutes: body ? minutesOf(x, body) : 0,
    teaches: `Teaches ${subTitle(c, sub)} · ${levelName(b.rules, level)}${more}`,
    status,
  };
}

/** What a lesson page offers after its text: the lessons that need it, and others on the same subtopics. */
export function lessonsAround(c: Course, slug: string): { next: Lesson[]; related: Lesson[] } {
  const all = c.graph?.lessons ?? [];
  const me = all.find((x) => x.slug === slug);
  if (!me) return { next: [], related: [] };
  const next = all.filter((x) => x.needs.includes(`lesson:${slug}`));
  const subs = new Set(me.teaches.map(([s]) => s));
  const related = all.filter((x) => x.slug !== slug && !next.includes(x) && x.teaches.some(([s]) => subs.has(s)));
  return { next, related };
}

/** The first lesson ready to read, in the user's module order, and the home's line naming it. */
export function readyLesson(b: Board, order: string[]): { c: Course; lesson: Lesson; line: string } | null {
  for (const c of bySavedOrder(b.courses, (x) => x.slug, order)) {
    for (const x of b.lessons(c)) {
      if (!b.lessonReady(c, x)) continue;
      const body = c.lessonBodies[x.slug];
      const minutes = body ? minutesOf(x, body) : 0;
      return { c, lesson: x, line: `Ready to read: ${x.title}${minutes ? ` · ~${minutes} min` : ''}` };
    }
  }
  return null;
}

/** Why a queue stops on a lesson, before and after it is read. */
export function lessonStopNote(read: boolean): string {
  return read
    ? 'Read. New questions on it are open again.'
    : 'You have tried a few questions on this. Read it before more new ones; reviews are not affected.';
}
