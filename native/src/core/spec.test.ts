import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  Board,
  buildHistory,
  courseGroups,
  groupKey,
  loadSnapshot,
  matchShort,
  normalize,
  parseTime,
  passed,
  qkey,
  certStates,
  headings,
  minutesOf,
  lessonRefError,
  lessonLinks,
  isLessonItem,
  withLessons,
  visibleCatalog,
  type LessonRecord,
  parseGraph,
  parseQuestion,
  checkDetail,
  selectExam,
  nextQueue,
  focusQueue,
  outsideFocus,
  reviewQueue,
  drillQueue,
  dayStart,
  newToday,
  isoNow,
  type Catalog,
  type FocusRecord,
  type Queue,
  type Status,
  type StatusRecord,
  currentFocus,
  cardFields,
  withStatuses,
  splitGuess,
  status,
  replay,
  ready,
  DEFAULT_FSRS,
  type AttemptRecord,
  type Snapshot,
} from './index';

// Generated from the Python side, which the engine port checks too: `docs/architecture/knowledge.md`.
const FIXTURE = resolve(__dirname, '../../../tests/fixtures/knowledge/scheduling.json');
const data = JSON.parse(readFileSync(FIXTURE, 'utf8'));


const close = (got: number | null, want: number | null, rel: number) =>
  want === null ? got === null : got !== null && Math.abs(got - want) <= rel * Math.abs(want);

describe('scheduling', () => {
  it('uses the parameters and settings the CLI publishes', () => {
    const published = data.gating[0].snapshot.rules.fsrs;
    expect(published).toEqual({ ...DEFAULT_FSRS });
  });
  for (const c of data.scheduling) {
    it(c.name, () => {
      const records = c.records as AttemptRecord[];
      const hist = buildHistory(records);
      const a = records.length ? (hist.get(qkey(records[0])) ?? []) : [];
      const m = replay(a);
      const e = c.expected;
      expect(a.map((x) => x.rating)).toEqual(e.ratings);
      expect(passed(a)).toBe(e.passed);
      expect((c.now as string[]).map((n) => status(a, parseTime(n)))).toEqual(e.status);
      expect((c.now as string[]).map((n) => ready(a, parseTime(n)))).toEqual(e.ready);
      expect(close(m?.stability ?? null, e.stability, 1e-6)).toBe(true);
      expect(close(m?.difficulty ?? null, e.difficulty, 1e-6)).toBe(true);
      if (e.due === null) expect(m).toBeNull();
      else expect(Math.abs((m?.due ?? 0) - parseTime(e.due))).toBeLessThanOrEqual(60_000);
    });
  }
});

describe('short answers', () => {
  for (const c of data.short) {
    it(JSON.stringify(c.raw), () => {
      const [reply, guess] = splitGuess(c.raw);
      const q = { accept: c.accept, caseSensitive: c.case };
      expect({
        reply,
        guess,
        normalized: normalize(reply, c.case),
        ok: matchShort(reply, q),
      }).toEqual(c.expected);
    });
  }
});

describe('gating', () => {
  for (const c of data.gating) {
    it(c.name, () => {
      const cat = withLessons(loadSnapshot(c.snapshot as Snapshot), c.lessons ?? []);
      const b = Board.build(cat, c.records);
      const groups = b.courses.flatMap((course) =>
        courseGroups(course, cat.rules).map((g) => ({
          group: groupKey(g),
          total: b.groupQuestions(g).length,
          passed: b.nPassed(g),
          done: b.done(g),
          unlocked: b.unlocked(g),
          blocker: ((x) => (x ? [x.sub, x.level] : null))(b.blocker(g)),
          lesson_gate: b.groupGate(g)?.slug ?? null,
        })),
      );
      const frontier = Object.fromEntries(
        b.courses.map((course) => [course.slug, b.frontier(course).map(groupKey)]),
      );
      const lessons = Object.fromEntries(
        b.courses.flatMap((course) =>
          b.lessons(course).map((x) => [
            x.slug,
            { state: b.lessonState(course, x), tried: b.tried(course, x), ready: b.lessonReady(course, x) },
          ]),
        ),
      );
      const held = b
        .questions()
        .filter((q) => b.held(q))
        .map(qkey)
        .sort();
      expect({ groups, frontier, lessons, held }).toEqual(c.expected);
    });
  }
});


function mulberry(seed: number): () => number {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}


describe('exam', () => {
  for (const c of data.exam) {
    it(c.name, () => {
      const cat = withStatuses(loadSnapshot({ format: 2, courses: c.courses } as Snapshot), c.statuses ?? []);
      const b = Board.build(cat, c.records, c.course);
      for (let seed = 1; seed <= 20; seed++) {
        const qs = selectExam(b, c.level, c.n, mulberry(seed));
        expect(qs.map(qkey).sort()).toEqual(c.expected.picked);
      }
    });
  }
});


describe('course status', () => {
  for (const c of data.status) {
    it(c.name, () => {
      const cat = withStatuses(loadSnapshot({ format: 2, courses: c.courses } as Snapshot), c.statuses);
      const status = Object.fromEntries(
        cat.courses.map((x) => [x.slug, x.archived ? 'archived' : x.paused ? 'paused' : 'active']),
      );
      expect({ status }).toEqual(c.expected);
    });
  }
});

describe('card grade', () => {
  for (const c of data.card) {
    it(c.name, () => {
      expect(cardFields(c.points, new Set(c.recalled), new Set(c.traps), c.wrong)).toEqual(c.expected);
    });
  }
});

describe('focus', () => {
  for (const c of data.focus) {
    it(c.name, () => {
      const cat = visibleCatalog(withStatuses(loadSnapshot({ format: 2, courses: c.courses } as Snapshot), c.statuses ?? []));
      const f = currentFocus(c.focus, cat);
      const out: Record<string, unknown> = { focus: f ? [f.course, f.topic, f.sub] : null };
      if (f?.cert) Object.assign(out, { cert: f.cert, scope: [...(f.scope ?? [])].sort() });
      expect(out).toEqual(c.expected);
    });
  }
});


type Recs = AttemptRecord[];

/** First `n` picks, answering each Good one second apart, rebuilding the board like the app. */
function drain(
  c: { n: number; now: string; records: Recs; courses: unknown; statuses?: StatusRecord[]; focus?: FocusRecord[] },
  make: (cat: Catalog, recs: Recs) => { board: (recs: Recs) => Board; queue: Queue } | null,
  seed: number,
): string[] {
  const cat = visibleCatalog(withStatuses(loadSnapshot({ format: 3, courses: c.courses } as Snapshot), c.statuses ?? []));
  const recs = [...c.records];
  const start = parseTime(c.now);
  const made = make(cat, recs);
  if (!made || made.queue.isEmpty(made.board(recs), start)) return [];
  const rng = mulberry(seed);
  const out: string[] = [];
  for (let i = 0; i < c.n; i++) {
    const at = start + i * 1000;
    const q = made.queue.pick(made.board(recs), at, rng);
    if (!q) break;
    if (isLessonItem(q)) {
      out.push(`lesson:${q.lesson.slug}`);
      continue;
    }
    out.push(qkey(q));
    recs.push({ t: isoNow(at), course: q.course, id: q.id, ok: true });
  }
  return out;
}

const seeds = Array.from({ length: 15 }, (_, i) => i + 1);

describe('next queue', () => {
  for (const c of data.next) {
    it(c.name, () => {
      for (const seed of seeds) {
        const got = drain(c, (cat) => {
          const board = (r: Recs) => Board.build(cat, r, c.course);
          return { board, queue: nextQueue(board(c.records), c.limit ?? 10) };
        }, seed);
        expect({ picked: [...new Set(got)].sort() }).toEqual(c.expected);
      }
    });
  }
});

describe('focused next queue', () => {
  for (const c of data.focused_next) {
    it(c.name, () => {
      for (const seed of seeds) {
        const got = drain(c, (cat) => {
          const f = currentFocus(c.focus, cat);
          if (!f) return null;
          const board = (r: Recs) => Board.build(cat, r, null, f.course);
          return { board, queue: focusQueue(board(c.records), f, c.limit ?? 10) };
        }, seed);
        const ordered = c.ordered ?? true;
        expect({ picked: ordered ? got : [...new Set(got)].sort() }).toEqual(c.expected);
      }
    });
  }
});

describe('review queue', () => {
  for (const c of data.review) {
    it(c.name, () => {
      const f = c.filters;
      const want: Status[] = f.weak ? ['weak'] : f.due ? ['due'] : ['weak', 'due'];
      for (const seed of seeds) {
        const got = drain(c, (cat) => {
          const board = (r: Recs) => Board.build(cat, r, f.course);
          return { board, queue: reviewQueue(board(c.records), want) };
        }, seed);
        expect({ picked: [...new Set(got)].sort() }).toEqual(c.expected);
      }
    });
  }
});

describe('drill queue', () => {
  for (const c of data.drill) {
    it(c.name, () => {
      for (const seed of seeds) {
        const got = drain(c, (cat) => {
          const board = (r: Recs) => Board.build(cat, r, c.filters.course);
          return { board, queue: drillQueue(board(c.records), c.filters, c.limit ?? 10) };
        }, seed);
        expect({ picked: [...new Set(got)].sort() }).toEqual(c.expected);
      }
    });
  }
});

describe('new today', () => {
  for (const c of data.new_today) {
    it(c.name, () => {
      const cat = loadSnapshot({ format: 3, courses: [] } as unknown as Snapshot);
      const b = Board.build(cat, c.records);
      const now = parseTime(c.now);
      expect(dayStart(now, c.utc_offset_minutes)).toBe(parseTime(c.expected.day_start));
      expect(newToday(b, now, c.utc_offset_minutes)).toBe(c.expected.new_today);
    });
  }
});

describe('scripted queue', () => {
  for (const c of data.queue) {
    it(c.name, () => {
      const cat = loadSnapshot({ format: 5, courses: c.courses } as Snapshot);
      const f = currentFocus(c.focus, cat)!;
      const recs: Recs = [...c.records];
      const read: LessonRecord[] = [];
      const board = () => Board.build(withLessons(cat, read), recs, null, f.course);
      const queue = focusQueue(board(), f, c.limit);
      const picked: (string | null)[] = [];
      for (const step of c.steps) {
        const q = queue.pick(board(), parseTime(step.at));
        if (isLessonItem(q)) {
          picked.push(`lesson:${q.lesson.slug}`);
          if (step.answer.done) read.push({ t: step.at, course: q.course.slug, lesson: q.lesson.slug, status: 'done' });
          continue;
        }
        picked.push(q ? qkey(q) : null);
        if (q) recs.push({ t: step.at, course: q.course, id: q.id, ...step.answer });
      }
      expect({ picked }).toEqual(c.expected);
    });
  }
});

describe('waiting outside a strict focus', () => {
  for (const c of data.outside) {
    it(c.name, () => {
      const cat = withStatuses(loadSnapshot({ format: 3, courses: c.courses } as Snapshot), c.statuses ?? []);
      const f = currentFocus(c.focus, cat)!;
      const b = Board.build(cat, c.records, null, f.course);
      expect({ outside: outsideFocus(b, f, parseTime(c.now)) }).toEqual(c.expected);
    });
  }
});

describe('detail', () => {
  for (const c of data.detail) {
    it(c.name, () => {
      const q = parseQuestion({ topic: 't', sub: 's', ...c.raw }, 'c');
      expect({
        errors: checkDetail(c.raw),
        detail: q.detail,
        key_detail: q.keyDetail,
        traps_detail: q.trapsDetail,
      }).toEqual(c.expected);
    });
  }
});

describe('graph', () => {
  for (const c of data.graph) {
    it(c.name, () => {
      const course = c.courses[0];
      const subs = new Set<string>(course.definition.topic.flatMap((t: { subs: string[] }) => t.subs));
      const { graph, errors, warnings } = parseGraph(course.graph, subs);
      const depth = graph ? Object.fromEntries([...subs].sort().map((s) => [s, graph.depth(s)])) : null;
      expect({ errors, warnings, depth }).toEqual(c.expected);
    });
  }
});

describe('lesson text', () => {
  for (const c of data.lesson_text) {
    it(c.name, () => {
      const bodies: Record<string, string> = c.bodies;
      const mins: Record<string, number> = c.minutes ?? {};
      expect({
        headings: Object.fromEntries(Object.entries(bodies).map(([k, v]) => [k, headings(v)])),
        minutes: Object.fromEntries(Object.entries(bodies).map(([k, v]) => [k, minutesOf({ minutes: mins[k] ?? null }, v)])),
        refs: Object.fromEntries((c.refs as string[]).map((r) => [r, lessonRefError(r, bodies)])),
        links: Object.values(bodies).flatMap((v) => lessonLinks(v)),
      }).toEqual(c.expected);
    });
  }
});

describe('certificate DAG', () => {
  for (const c of data.cert_dag) {
    it(c.name, () => {
      const [course] = loadSnapshot({ format: 6, courses: c.courses } as Snapshot).courses;
      expect({
        errors: course.certsErrors,
        edges: course.certs ? course.certs.edges.map((e) => [...e]).sort() : null,
        titles: course.certs ? Object.fromEntries(course.certs.certs.slice(0, 2).map((x) => [x.id, x.title])) : null,
      }).toEqual(c.expected);
    });
  }
});

describe('certificate states', () => {
  for (const c of data.cert_states) {
    it(c.name, () => {
      const cat = loadSnapshot({ format: 6, courses: c.courses } as Snapshot);
      const b = Board.build(cat, c.records);
      const st = certStates(b, cat.courses[0], c.exams ?? []);
      const round = (x: number) => Math.round(x * 1e6) / 1e6;
      expect({
        states: Object.fromEntries([...st].map(([k, v]) => [k, [v.state, round(v.coverage), round(v.retention), v.pool]])),
      }).toEqual(c.expected);
    });
  }
});
