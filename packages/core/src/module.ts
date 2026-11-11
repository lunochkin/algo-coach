import { levelName, levels, subsByDepth, subTitle } from './courses';
import { drillQueue, type DrillScope, type Queue } from './queue';
import type { Board } from './schedule';
import { counted } from './screens';
import { focusOn, startGroup } from './words/module';
import { startLabel } from './words/pages';
import type { Course, Group } from './types';

/** How one group reads on a module's screens: covered, open, locked, or holding no questions. */
export type CellState = 'covered' | 'open' | 'locked' | 'empty';

export interface GroupCell {
  state: CellState;
  passed: number;
  total: number;
  count: string; // "4/9", or "·" where the group holds no questions
  needs: string; // what a locked group waits for; '' where it waits for nothing
  line: string; // the count and the state in words, as the Map's panel reads them
}

export function groupCell(b: Board, g: Group): GroupCell {
  const total = b.groupQuestions(g).length;
  const passed = b.nPassed(g);
  const state: CellState = !total ? 'empty' : b.done(g) ? 'covered' : b.unlocked(g) ? 'open' : 'locked';
  const needs = state === 'locked' ? b.needsLabel(g) : '';
  const count = total ? `${passed}/${total}` : '·';
  const word = state === 'empty' ? 'no questions' : state === 'locked' ? needs || 'locked' : state;
  return { state, passed, total, count, needs, line: state === 'empty' ? word : `${count} · ${word}` };
}

export interface LevelCount {
  level: number;
  name: string;
  passed: number;
  total: number;
}

/** The passed questions of each level over the questions it holds, across a module or one topic. */
export function levelCounts(b: Board, c: Course, topic: string | null = null): LevelCount[] {
  const topics = c.topics.filter((t) => !topic || t.slug === topic);
  return levels(b.rules).map((level) => {
    const gs = topics.flatMap((t) => t.subs.map((sub) => ({ course: c.slug, topic: t.slug, sub, level })));
    return {
      level,
      name: levelName(b.rules, level),
      passed: gs.reduce((n, g) => n + b.nPassed(g), 0),
      total: gs.reduce((n, g) => n + b.groupQuestions(g).length, 0),
    };
  });
}

/** The level counts in one line, leaving out a level that holds no questions. */
export function levelCountsLine(b: Board, c: Course, topic: string | null = null): string {
  return levelCounts(b, c, topic)
    .filter((x) => x.total)
    .map((x) => `${x.name} ${x.passed}/${x.total}`)
    .join(' · ');
}

/** One cell of a module's grid: the group at one level, and the words its press is named by. */
export interface GridCell {
  level: number;
  cell: GroupCell;
  label: string;
}

/** One subtopic's row: the name that starts it at every level, its focus press, and a cell per level. */
export interface GridRow {
  sub: string;
  title: string;
  start: string;
  focus: string;
  cells: GridCell[];
}

export interface GridTopic {
  slug: string;
  title: string;
  count: number;
  rows: GridRow[];
}

/** A module's groups, as both clients draw them: a table of subtopics by level per topic. */
export function moduleGrid(b: Board, c: Course): { levels: { level: number; name: string }[]; topics: GridTopic[] } {
  const lv = levels(b.rules);
  return {
    levels: lv.map((level) => ({ level, name: levelName(b.rules, level, true) })),
    topics: c.topics.map((t) => ({
      slug: t.slug,
      title: t.title,
      count: t.subs.length,
      // the shallowest subtopic first, as the map draws them
      rows: subsByDepth(c, t).map((sub) => {
        const title = subTitle(c, sub);
        return {
          sub,
          title,
          start: startLabel(title),
          focus: focusOn(title),
          cells: lv.map((level) => {
            const cell = groupCell(b, { course: c.slug, topic: t.slug, sub, level });
            return { level, cell, label: startGroup(title, levelName(b.rules, level), cell.line) };
          }),
        };
      }),
    })),
  };
}

/** What the start sheet's press would open, and its label. */
export interface StartPreview {
  queue: Queue;
  reviews: number;
  newLeft: number;
  empty: boolean;
  label: string;
}

export function startPreview(b: Board, scope: DrillScope, limit: number, now: number): StartPreview {
  const queue = drillQueue(b, scope, limit);
  const reviews = queue.reviews(b, now).length;
  const newLeft = queue.newLeft(b, now);
  const empty = queue.isEmpty(b, now);
  const label = empty ? 'Nothing ready here' : `Start · ${counted(reviews, 'review')} · ${newLeft} new`;
  return { queue, reviews, newLeft, empty, label };
}

/** The module's questions due for review now. */
export function dueCount(b: Board, now: number): number {
  return b.questions().filter((q) => b.toReview(q, now)).length;
}
