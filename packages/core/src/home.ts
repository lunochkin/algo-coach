import { certStates, STATE_LABEL, type CertRecord } from './certs';
import { visibleCatalog, withCertExams, withLessons, withStatuses, type Catalog } from './courses';
import type { Focus } from './focus';
import { focusQueue, focusScope, nextQueue, outsideFocus, type Queue } from './queue';
import type { Board } from './schedule';
import { counted, groupLabel, nextUpView, type NextUpView, type QueueCounts } from './screens';
import type { Course, LessonRecord, StatusRecord } from './types';

export interface LearnerRecords {
  statuses: StatusRecord[];
  lessons: LessonRecord[];
  certs: CertRecord[];
}

/**
 * The catalog as one user reads it: the snapshot with the user's module
 * statuses, lesson marks and certification exams applied. `catalog` hides the
 * archived modules, which `archived` lists for restoring.
 */
export function learnerCatalog(raw: Catalog, r: LearnerRecords): { catalog: Catalog; archived: Course[] } {
  const full = withCertExams(withLessons(withStatuses(raw, r.statuses), r.lessons), r.certs);
  return { catalog: visibleCatalog(full), archived: full.courses.filter((c) => c.archived) };
}

/** Builds a board over one module, or over every one, serving `include` even where it is paused. */
export type BoardOf = (only: string | null, include?: string | null) => Board | null;

/** The queue Continue would open, and the board its picks read. */
export interface ContinuePlan {
  b: Board;
  queue: Queue;
  course: string | null;
  include: string | null; // the focus's module, served while paused
}

/** A module picked on the home sets the focus aside, as `learn next --course` does. */
export function continuePlan(board: BoardOf, focus: Focus | null, only: string | null, limit: number): ContinuePlan | null {
  if (!only && focus) {
    const b = board(null, focus.course);
    return b ? { b, queue: focusQueue(b, focus, limit), course: null, include: focus.course } : null;
  }
  const b = board(only);
  return b ? { b, queue: nextQueue(b, limit), course: only, include: null } : null;
}

export interface ContinueCounts extends QueueCounts {
  outside: number; // reviews a strict focus leaves out, which a press serves
  empty: boolean;
  blocked: boolean; // the day's limit alone empties the queue
}

export function continueCounts(p: ContinuePlan, focus: Focus | null, now: number): ContinueCounts {
  return {
    reviews: p.queue.reviews(p.b, now).length,
    learning: p.queue.stepping(p.b, now).count,
    newLeft: p.queue.newLeft(p.b, now),
    outside: focus?.strict ? outsideFocus(p.b, focus, now) : 0,
    empty: p.queue.isEmpty(p.b, now),
    blocked: p.queue.blockedByLimit(p.b, now),
  };
}

/** A module's row on the home: what comes next in it, and how much it holds and owes. */
export interface ModuleRow {
  c: Course;
  view: NextUpView;
  total: number;
  toReview: number; // weak and due, anywhere in the module
}

export function moduleRows(b: Board, now: number): ModuleRow[] {
  const all = b.questions();
  return b.courses.map((c) => {
    const qs = all.filter((q) => q.course === c.slug);
    return { c, view: nextUpView(b, c), total: qs.length, toReview: qs.filter((q) => b.toReview(q, now)).length };
  });
}

export type FocusPart = 'mastered' | 'learning' | 'review' | 'unseen';

/** The focus panel: how far the focus is along, what is owed now, and what comes next. */
export interface FocusView {
  total: number;
  parts: { k: FocusPart; v: number; label: string }[]; // in the bar's order
  locked: number;
  summary: string;
  due: number;
  learning: number;
  newLeft: number;
  next: string | null; // the first open group with new work inside the focus
  cert: string | null; // a certification focus's state, coverage and retention
}

const PART_LABEL: Record<FocusPart, string> = {
  mastered: 'mastered',
  learning: 'learning',
  review: 'to review',
  unseen: 'unseen',
};

export function focusView(b: Board, focus: Focus, queue: Queue, exams: CertRecord[], now: number): FocusView {
  const qs = focusScope(b, focus);
  const inScope = new Set(qs);
  const n: Record<FocusPart, number> = { mastered: 0, learning: 0, review: 0, unseen: 0 };
  let locked = 0;
  for (const q of qs) {
    const s = b.status(q, now);
    if (s === 'mastered' || s === 'learning' || s === 'unseen') n[s]++;
    else n.review++;
    if (s === 'unseen' && !b.unlocked(q)) locked++;
  }
  const parts = (Object.keys(PART_LABEL) as FocusPart[]).map((k) => ({ k, v: n[k], label: PART_LABEL[k] }));
  const shown = parts.filter((p) => p.v).map((p) => `${p.v} ${p.label}`);
  const c = b.course(focus.course);
  const group = c ? b.frontier(c).find((g) => b.groupQuestions(g).some((q) => inScope.has(q))) : undefined;
  const cert = focus.cert && c ? certStates(b, c, exams).get(focus.cert) : undefined;
  const pct = (x: number) => `${Math.round(x * 100)}%`;
  return {
    total: qs.length,
    parts,
    locked,
    summary: `${counted(qs.length, 'question')} · ${shown.join(' · ')}${locked ? ` (${locked} locked)` : ''}`,
    due: queue.reviews(b, now).length,
    learning: queue.stepping(b, now).count,
    newLeft: queue.newLeft(b, now),
    // a topic focus names its topic already
    next: c && group ? `${groupLabel(c, b.rules, group, !focus.topic)} · ${b.nPassed(group)}/${b.groupQuestions(group).length}` : null,
    cert: cert
      ? `${STATE_LABEL[cert.state]} · coverage ${pct(cert.coverage)} · retention ${pct(cert.retention)}`
      : null,
  };
}
