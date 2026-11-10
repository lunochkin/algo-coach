import { courseGroups, groupKey, qkey } from './courses';
import { inFocus, type Focus } from './focus';
import type { Board } from './schedule';
import { ranked, type Rng } from './select';
import type { Lesson } from './graph';
import type { Course, Question, Status } from './types';

const DAY = 86_400_000;
export const NEW_PER_DAY = 10;
export const NEW_STEP = 5; // "+5 new": a raise of today's limit, from Home or a queue
const ROLLOVER_HOUR = 4; // local time, as Anki
const LEARN_AHEAD = 20 * 60_000;

/** Start of the learning day containing `now`: 04:00 local time (offset in minutes east of UTC). */
export function dayStart(now: number, offsetMinutes = -new Date(now).getTimezoneOffset()): number {
  const off = offsetMinutes * 60_000;
  const local = new Date(now + off);
  const start =
    Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate(), ROLLOVER_HOUR) - off;
  return now >= start ? start : start - DAY;
}

/** Today's raise of the new-question limit, kept per device until the rollover. */
export interface Raise {
  day: number; // the dayStart it was made in
  extra: number;
}

/** The new-question limit today: the daily setting plus today's raise, if any. */
export function todayLimit(base: number, raise: Raise | null, now: number, offsetMinutes?: number): number {
  return base + (raise && raise.day === dayStart(now, offsetMinutes) ? raise.extra : 0);
}

/** Today's raise after one more step. A raise from an earlier day counts for nothing. */
export function raised(raise: Raise | null, now: number, offsetMinutes?: number): Raise {
  const day = dayStart(now, offsetMinutes);
  return { day, extra: (raise?.day === day ? raise.extra : 0) + NEW_STEP };
}

/** Questions whose first-ever attempt, on any device, falls in today. */
export function newToday(b: Board, now: number, offsetMinutes?: number): number {
  const start = dayStart(now, offsetMinutes);
  let n = 0;
  for (const h of b.hist.values()) if (h.length && h[0].t >= start && h[0].t <= now) n++;
  return n;
}

/** A lesson served by a queue in place of a new question. */
export interface LessonItem {
  kind: 'lesson';
  course: Course;
  lesson: Lesson;
}

export const isLessonItem = (x: unknown): x is LessonItem =>
  typeof x === 'object' && x !== null && (x as LessonItem).kind === 'lesson';

export type QueueKind = 'mix' | 'focus' | 'review' | 'drill';

/**
 * Picks the next question on demand from what is ready now (spec/learn.md, Queues). The board
 * is passed on every pick, so answers recorded since the last pick are taken into account.
 */
export class Queue {
  asked = new Set<string>();
  offered = new Set<string>(); // lessons served this queue: "course:lesson"
  private lastCourse = -1;

  constructor(
    readonly kind: QueueKind,
    readonly scope: Question[], // reviews and learn-ahead come from here
    readonly want: Status[] | null = null,
    public limit = NEW_PER_DAY,
    readonly newScope: Question[] | null = null, // unseen, in order; null: frontiers round-robin
    readonly offsetMinutes?: number,
  ) {}

  newLeft(b: Board, now: number): number {
    return Math.max(0, this.limit - newToday(b, now, this.offsetMinutes));
  }

  private wanted(b: Board, q: Question, now: number): boolean {
    return this.want === null || this.want.includes(b.status(q, now));
  }

  reviews(b: Board, now: number): Question[] {
    return this.scope.filter((q) => b.toReview(q, now) && this.wanted(b, q, now));
  }

  /**
   * Questions in a (re)learning step that is not due yet. `reviews` leaves them out, and
   * learn ahead serves them when nothing else is ready, so a count shows them apart.
   */
  stepping(b: Board, now: number): { count: number; nextAt: number | null } {
    let count = 0;
    let nextAt = Infinity;
    for (const q of this.scope) {
      if (this.early(b, q, now) && this.wanted(b, q, now)) {
        count++;
        nextAt = Math.min(nextAt, b.memory(q)!.due);
      }
    }
    return { count, nextAt: count ? nextAt : null };
  }

  /** Whether `q` would be served before its step is due: learn ahead. */
  early(b: Board, q: Question, now: number): boolean {
    const m = b.memory(q);
    return !!m?.learning && m.due > now;
  }

  /** The next unseen question, if today's limit allows one. */
  private fresh(b: Board, now: number, rng: Rng, take: boolean): Question | null {
    if (this.kind === 'review' || this.want || !this.newLeft(b, now)) return null;
    if (this.kind !== 'mix') {
      // A focus's new questions follow the ladder; a drill is explicit and may go past it.
      const ladder = this.kind === 'focus';
      return (
        (this.newScope ?? this.scope).find(
          (q) => !b.attempts(q).length && (!ladder || (b.unlocked(q) && !b.held(q))),
        ) ?? null
      );
    }
    // Frontier order per course, courses round-robin so none starves the others.
    const cs = b.served;
    for (let i = 1; i <= cs.length; i++) {
      const k = (this.lastCourse + i) % cs.length;
      // the same group a module card names as next up: one rule for both
      const g = b.nextNew(cs[k]);
      if (g) {
        const unseen = (b.byGroup.get(groupKey(g)) ?? []).filter((q) => !b.attempts(q).length && !b.held(q));
        if (take) this.lastCourse = k;
        return unseen[Math.floor(rng() * unseen.length)];
      }
    }
    return null;
  }

  /** Learn ahead: the earliest (re)learning step due within 20 minutes. */
  private ahead(b: Board, now: number): Question | null {
    let best: Question | null = null;
    let bestDue = Infinity;
    for (const q of this.scope) {
      const m = b.memory(q);
      if (m?.learning && m.due <= now + LEARN_AHEAD && m.due < bestDue && this.wanted(b, q, now)) {
        best = q;
        bestDue = m.due;
      }
    }
    return best;
  }

  /** A lesson due to be read whose levels are in scope, at the slot of a new question. */
  private lessonItem(b: Board): LessonItem | null {
    if (this.kind !== 'mix' && this.kind !== 'focus') return null;
    const subs = new Set(this.scope.map((q) => q.sub));
    for (const c of b.courses) {
      for (const x of b.lessons(c)) {
        const key = `${c.slug}:${x.slug}`;
        if (!this.offered.has(key) && x.teaches.some(([s]) => subs.has(s)) && b.lessonReady(c, x)) {
          return { kind: 'lesson', course: c, lesson: x };
        }
      }
    }
    return null;
  }

  pick(b: Board, now: number, rng: Rng = Math.random): Question | LessonItem | null {
    const reviews = ranked(this.reviews(b, now), b, now, rng);
    let q: Question | null = null;
    if (this.kind === 'drill') {
      const fresh = this.fresh(b, now, rng, true);
      const pool = fresh ? [...reviews, fresh] : reviews;
      q = ranked(pool, b, now, rng)[0] ?? null;
      if (!q && this.want === null) {
        const rest = this.scope.filter(
          (x) => ['learning', 'mastered'].includes(b.status(x, now)) && !this.asked.has(qkey(x)),
        );
        q = ranked(rest, b, now, rng)[0] ?? null;
      }
    } else {
      if (!reviews.length) {
        const item = this.lessonItem(b);
        if (item) {
          this.offered.add(`${item.course.slug}:${item.lesson.slug}`);
          return item;
        }
      }
      q = reviews[0] ?? this.fresh(b, now, rng, true);
    }
    q ??= this.ahead(b, now);
    if (q) {
      this.asked.add(qkey(q));
    }
    return q;
  }

  /** Whether today's limit alone empties the queue: five more would let a new question in. */
  blockedByLimit(b: Board, now: number): boolean {
    if (this.newLeft(b, now) || !this.isEmpty(b, now)) return false;
    const probe = new Queue(this.kind, this.scope, this.want, this.limit + NEW_STEP, this.newScope, this.offsetMinutes);
    return !probe.isEmpty(b, now);
  }

  /** Whether a fresh queue over this scope would serve anything now. */
  isEmpty(b: Board, now: number): boolean {
    const probe = new Queue(this.kind, this.scope, this.want, this.limit, this.newScope, this.offsetMinutes);
    return probe.pick(b, now, () => 0) === null;
  }
}

/** `next`: reviews from every group of the served courses, new ones from their frontiers. */
export function nextQueue(b: Board, limit: number): Queue {
  return new Queue('mix', b.servedGroups().flat(), null, limit);
}

/** The focus's questions in curriculum order, all levels. */
export function focusScope(b: Board, f: Focus): Question[] {
  const c = b.courses.find((x) => x.slug === f.course);
  return c
    ? courseGroups(c, b.rules).flatMap((g) => (b.byGroup.get(groupKey(g)) ?? []).filter((q) => inFocus(q, f)))
    : [];
}

/**
 * `next` with a focus. Strict: reviews and new from the focus only. Relaxed (default): reviews
 * from all served courses as in `next`, new from the focus. Build the board with
 * `Board.build(catalog, records, null, focus.course)` so a paused focus course still counts.
 */
export function focusQueue(b: Board, f: Focus, limit: number): Queue {
  const mine = focusScope(b, f);
  if (f.strict) return new Queue('focus', mine, null, limit, mine);
  const keys = new Set(mine.map(qkey));
  // Reviews come from every group, locked or not; only new questions follow the ladder.
  const all = b.servedGroups().flat().filter((q) => !keys.has(qkey(q)));
  return new Queue('focus', [...mine, ...all], null, limit, mine);
}

/** Ready reviews outside a strict focus, which a plain review queue would serve. */
export function outsideFocus(b: Board, f: Focus, now: number): number {
  return b.servedGroups().flat().filter((q) => !inFocus(q, f) && b.toReview(q, now)).length;
}

export function reviewQueue(b: Board, want: Status[]): Queue {
  return new Queue('review', b.servedGroups().flat(), want);
}

export interface DrillScope {
  course: string;
  topic?: string | null;
  sub?: string | null;
  level?: number | null;
  kind?: string | null;
  weak?: boolean; // only weak
  due?: boolean; // only weak or due
}

export function drillQueue(b: Board, f: DrillScope, limit: number): Queue {
  const scope = b.questions().filter(
    (q) =>
      q.course === f.course &&
      (f.topic == null || q.topic === f.topic) &&
      (f.sub == null || q.sub === f.sub) &&
      (f.level == null || q.level === f.level) &&
      (f.kind == null || q.kind === f.kind),
  );
  const want: Status[] | null = f.weak ? ['weak'] : f.due ? ['weak', 'due'] : null;
  return new Queue('drill', scope, want, limit);
}
