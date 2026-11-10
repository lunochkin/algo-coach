import { courseGroups, DEFAULT_RULES, groupKey, levelName, qkey, topicOf, type Catalog } from './courses';
import { AGAIN, GOOD, HARD, replay, type Memory } from './fsrs';
import type { Lesson } from './graph';
import type { Attempt, AttemptRecord, Course, Group, Question, Rules, Status } from './types';

export type History = Map<string, Attempt[]>;

export function parseTime(t: string): number {
  const ms = Date.parse(t);
  if (Number.isNaN(ms)) throw new Error(`bad timestamp ${t}`);
  return ms;
}

/** FSRS rating of a record: card grade k/p/n; else correct Good, correct guess Hard, wrong Again. */
export function ratingOf(r: AttemptRecord): number {
  if (r.grade) return { k: GOOD, p: HARD, n: AGAIN }[r.grade];
  if (!r.ok) return AGAIN;
  return r.guess ? HARD : GOOD;
}

/** Records must already be in file order (paths sorted, lines in order); sorting by `t` is stable. */
export function buildHistory(records: AttemptRecord[]): History {
  const sorted = [...records].sort((a, b) => (a.t < b.t ? -1 : a.t > b.t ? 1 : 0));
  const hist: History = new Map();
  for (const r of sorted) {
    const k = qkey(r);
    let list = hist.get(k);
    if (!list) hist.set(k, (list = []));
    list.push({ t: parseTime(r.t), rating: ratingOf(r) });
  }
  return hist;
}

export const isPass = (a: Attempt) => a.rating === GOOD;

export function status(
  attempts: Attempt[],
  now: number,
  rules: Rules = DEFAULT_RULES,
  memory: Memory | null = replay(attempts, rules.fsrs),
): Status {
  if (!attempts.length || !memory) return 'unseen';
  if (!isPass(attempts[attempts.length - 1])) return 'weak';
  if (now >= memory.due) return 'due';
  return memory.stability >= rules.fsrs.mastered_stability_days ? 'mastered' : 'learning';
}

/** Servable now: unseen, or FSRS's due (a weak question's step or interval) has come. */
export function ready(attempts: Attempt[], now: number, memory: Memory | null = replay(attempts)): boolean {
  return !attempts.length || !memory || now >= memory.due;
}

/** Ever passed. Gating uses this, so a failed review does not relock a level. */
export function passed(attempts: Attempt[]): boolean {
  return attempts.some(isPass);
}

export const PRIORITY: Record<Status, number> = {
  weak: 0,
  due: 1,
  unseen: 2,
  learning: 3,
  mastered: 4,
};

const NONE: Attempt[] = [];

/** Per-group question lists plus unlock state, over the selected courses. */
export class Board {
  readonly byGroup = new Map<string, Question[]>();

  readonly catalog: Catalog;
  readonly courses: Course[];
  readonly hist: History;
  readonly explicit: boolean; // one course was selected by the learner
  readonly include: string | null; // served even if paused: the focus course

  constructor(catalog: Catalog, courses: Course[], hist: History, explicit = false, include: string | null = null) {
    this.catalog = catalog;
    this.courses = courses;
    this.hist = hist;
    this.explicit = explicit;
    this.include = include;
    const slugs = new Set(courses.map((c) => c.slug));
    for (const q of catalog.questions) {
      if (!slugs.has(q.course)) continue;
      const k = groupKey(q);
      let list = this.byGroup.get(k);
      if (!list) this.byGroup.set(k, (list = []));
      list.push(q);
    }
  }

  static build(
    catalog: Catalog,
    records: AttemptRecord[],
    only?: string | null,
    include: string | null = null,
  ): Board {
    const courses = only ? catalog.courses.filter((c) => c.slug === only) : catalog.courses;
    return new Board(catalog, courses, buildHistory(records), !!only, include);
  }

  /** Courses served by `next` and `exam`: paused ones only when selected explicitly. */
  get served(): Course[] {
    return this.explicit
      ? this.courses
      : this.courses.filter((c) => !c.paused || c.slug === this.include);
  }

  /** Groups of served courses, in board order. */
  servedGroups(): Question[][] {
    const slugs = new Set(this.served.map((c) => c.slug));
    return [...this.byGroup.values()].filter((qs) => slugs.has(qs[0].course));
  }

  get rules(): Rules {
    return this.catalog.rules;
  }

  attempts(q: Question): Attempt[] {
    return this.hist.get(qkey(q)) ?? NONE;
  }

  private memo = new Map<string, Memory | null>();

  /** FSRS state of a question, replayed once per board. */
  memory(q: Question): Memory | null {
    const k = qkey(q);
    if (!this.memo.has(k)) this.memo.set(k, replay(this.attempts(q), this.rules.fsrs));
    return this.memo.get(k) ?? null;
  }

  status(q: Question, now: number): Status {
    return status(this.attempts(q), now, this.rules, this.memory(q));
  }

  ready(q: Question, now: number): boolean {
    return ready(this.attempts(q), now, this.memory(q));
  }

  /** Weak or due, and ready: what review pools serve. */
  toReview(q: Question, now: number): boolean {
    const s = this.status(q, now);
    return (s === 'weak' || s === 'due') && this.ready(q, now);
  }

  questions(): Question[] {
    return [...this.byGroup.values()].flat();
  }

  groupQuestions(g: Group): Question[] {
    return this.byGroup.get(groupKey(g)) ?? NONE_Q;
  }

  ratio(g: Group): number {
    return (this.courses.find((c) => c.slug === g.course) as Course).passRatio;
  }

  nPassed(g: Group): number {
    return this.groupQuestions(g).filter((q) => passed(this.attempts(q))).length;
  }

  done(g: Group): boolean {
    const qs = this.groupQuestions(g);
    return qs.length > 0 && this.nPassed(g) / qs.length >= this.ratio(g);
  }

  course(slug: string): Course | undefined {
    return this.courses.find((c) => c.slug === slug) ?? this.catalog.courses.find((c) => c.slug === slug);
  }

  /** The lowest level 0..upTo of a subtopic that is written and not done; null when all reached. */
  private unfinished(course: string, topic: string, sub: string, upTo: number): number | null {
    for (let level = 0; level <= upTo; level++) {
      const g = { course, topic, sub, level };
      if (!this.done(g) && this.groupQuestions(g).length) return level;
    }
    return null;
  }

  /** What keeps a group's new questions locked: the subtopic and level to finish, or null. */
  blocker(g: Group): { sub: string; level: number } | null {
    if (g.level > 0) {
      const low = this.unfinished(g.course, g.topic, g.sub, g.level - 1);
      if (low !== null) return { sub: g.sub, level: low };
    }
    const c = this.course(g.course);
    const graph = c?.graph;
    if (!c || !graph) return null;
    for (const [to, k] of graph.needs(g.sub)) {
      const topic = topicOf(c, to);
      if (!topic) continue;
      const low = this.unfinished(g.course, topic, to, Math.min(g.level, graph.matchUpTo) + k);
      if (low !== null) return { sub: to, level: low };
    }
    return null;
  }

  /** The ladder and the prerequisite graph, from history alone. Gates new questions only. */
  unlocked(g: Group): boolean {
    return this.blocker(g) === null;
  }

  /** Unlocked groups with new work, shallow prerequisites first, then listing order. */
  frontier(c: Course): Group[] {
    const open = courseGroups(c, this.rules).filter(
      (g) => this.groupQuestions(g).length > 0 && this.unlocked(g) && !this.done(g) && !this.groupGate(g),
    );
    const depth = (g: Group) => c.graph?.depth(g.sub) ?? 0;
    return open.map((g, i) => ({ g, i, d: depth(g) })).sort((a, b) => a.d - b.d || a.i - b.i).map((x) => x.g);
  }

  /** The first frontier group with a new question to serve: where Continue introduces next. */
  nextNew(c: Course): Group | null {
    return this.frontier(c).find((g) => this.groupQuestions(g).some((q) => !this.attempts(q).length && !this.held(q))) ?? null;
  }

  /**
   * What a module's next step is: the group Continue introduces from, or, where every open
   * group's new questions wait for a lesson, that lesson. `null` once every open group is done.
   */
  nextUp(c: Course): { group: Group; lesson: null } | { group: Group; lesson: Lesson } | null {
    const group = this.nextNew(c);
    if (group) return { group, lesson: null };
    for (const g of courseGroups(c, this.rules)) {
      if (!this.groupQuestions(g).length || !this.unlocked(g) || this.done(g)) continue;
      const lesson = this.groupGate(g);
      if (lesson) return { group: g, lesson };
    }
    return null;
  }

  // --- lessons

  lessons(c: Course): Lesson[] {
    return c.graph?.lessons ?? [];
  }

  lessonDone(c: Course, x: Lesson): boolean {
    return !!this.catalog.lessonsDone?.has(`${c.slug}:${x.slug}`);
  }

  private refOk(c: Course, ref: string): boolean {
    if (ref.startsWith('lesson:')) return !!this.catalog.lessonsDone?.has(`${c.slug}:${ref.slice(7)}`);
    const at = ref.lastIndexOf('@');
    const sub = ref.slice(0, at);
    const g = { course: c.slug, topic: topicOf(c, sub) ?? '', sub, level: Number(ref.slice(at + 1)) };
    return this.done(g) || !this.groupQuestions(g).length;
  }

  /** Unmet `needs`, then what blocks the levels the lesson teaches (as "sub@level"). */
  unmetNeeds(c: Course, x: Lesson): string[] {
    const out = x.needs.filter((r) => !this.refOk(c, r));
    for (const [sub, level] of x.teaches) {
      const b = this.blocker({ course: c.slug, topic: topicOf(c, sub) ?? '', sub, level });
      const r = b && `${b.sub}@${b.level}`;
      if (r && !out.includes(r)) out.push(r);
    }
    return out;
  }

  lessonUnlocked(c: Course, x: Lesson): boolean {
    return this.unmetNeeds(c, x).length === 0;
  }

  /** The question's own lesson if it names one, else the lessons teaching its level. */
  lessonsOf(c: Course, q: Question): Lesson[] {
    const g = c.graph;
    if (!g) return [];
    const own = q.lesson ? g.lesson(q.lesson.split('#')[0]) : undefined;
    return own ? [own] : g.teaching(q.sub, q.level);
  }

  private memberCache = new Map<string, Question[]>();

  /** Questions whose lessons include `x` (cached: a board's questions never change). */
  members(c: Course, x: Lesson): Question[] {
    const k = `${c.slug}:${x.slug}`;
    let m = this.memberCache.get(k);
    if (!m) {
      m = courseGroups(c, this.rules)
        .flatMap((g) => this.groupQuestions(g))
        .filter((q) => this.lessonsOf(c, q).some((y) => y.slug === x.slug));
      this.memberCache.set(k, m);
    }
    return m;
  }

  /** The lesson's questions with any attempt: its pretest so far. */
  tried(c: Course, x: Lesson): number {
    return this.members(c, x).filter((q) => this.attempts(q).length).length;
  }

  /** Unlocked, not-done lessons of `q` whose pretest is used: they hold `q` while unseen. */
  holders(q: Question): Lesson[] {
    const c = this.course(q.course);
    if (!c) return [];
    return this.lessonsOf(c, q).filter(
      (x) => !this.lessonDone(c, x) && this.lessonUnlocked(c, x) && this.tried(c, x) >= x.pretest,
    );
  }

  held(q: Question): boolean {
    return !this.attempts(q).length && this.holders(q).length > 0;
  }

  /** When every unseen question of `g` is held: the first lesson holding them. */
  groupGate(g: Group): Lesson | null {
    const unseen = this.groupQuestions(g).filter((q) => !this.attempts(q).length);
    if (!unseen.length || !unseen.every((q) => this.held(q))) return null;
    return this.holders(unseen[0])[0] ?? null;
  }

  /** Due to be read: some unseen question in an open group is held by this lesson alone. */
  lessonReady(c: Course, x: Lesson): boolean {
    if (this.lessonDone(c, x) || !this.lessonUnlocked(c, x) || this.tried(c, x) < x.pretest) return false;
    return this.members(c, x).some((q) => {
      if (this.attempts(q).length || !this.unlocked(q) || this.done(q)) return false;
      const h = this.holders(q);
      return h.length === 1 && h[0].slug === x.slug;
    });
  }

  lessonState(c: Course, x: Lesson): 'done' | 'available' | 'locked' {
    return this.lessonDone(c, x) ? 'done' : this.lessonUnlocked(c, x) ? 'available' : 'locked';
  }

  /** For a locked group with questions: "needs generators · Associate 3/8", else "". */
  needsLabel(g: Group): string {
    if (!this.groupQuestions(g).length || this.done(g)) return '';
    const b = this.blocker(g);
    const c = this.course(g.course);
    if (!b) {
      const x = this.groupGate(g);
      return x ? `needs lesson: ${x.title}` : '';
    }
    if (!c) return '';
    const pg = { course: g.course, topic: topicOf(c, b.sub) ?? g.topic, sub: b.sub, level: b.level };
    const name = levelName(this.rules, b.level);
    const what = b.sub === g.sub ? name : `${b.sub} · ${name}`;
    return `needs ${what} ${this.nPassed(pg)}/${this.groupQuestions(pg).length}`;
  }
}

const NONE_Q: Question[] = [];
