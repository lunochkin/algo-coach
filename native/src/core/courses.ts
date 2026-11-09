import { DEFAULT_FSRS } from './fsrs';
import { parseCerts, type CertRecord } from './certs';
import { parseGraph, type Graph, type RawGraph } from './graph';
import type { Course, Detail, Group, LessonRecord, Topic, Question, RawDetail, RawQuestion, Rules, Snapshot, StatusRecord } from './types';

export const LETTERS = 'ABCDEFGH';

export const DEFAULT_RULES: Rules = {
  fsrs: DEFAULT_FSRS,
  levels: { '0': 'Foundation', '1': 'Associate', '2': 'Professional', '3': 'Expert' },
};

export function levels(rules: Rules): number[] {
  return Object.keys(rules.levels)
    .map(Number)
    .sort((a, b) => a - b);
}

const SHORT: Record<string, string> = { Foundation: 'Found.', Associate: 'Assoc.', Professional: 'Prof.' };

/** A level's name, e.g. "Associate"; `short` fits a table column ("Assoc."). */
export function levelName(rules: Rules, level: number, short = false): string {
  const name = rules.levels[String(level)] ?? `L${level}`;
  return short ? (SHORT[name] ?? name) : name;
}

export function groupKey(g: Group): string {
  return `${g.course}/${g.topic}/${g.sub}/${g.level}`;
}

export function qkey(q: { course: string; id: string }): string {
  return `${q.course}:${q.id}`;
}

export function asDetail(raw: string | RawDetail | undefined): Detail | null {
  if (!raw) return null;
  if (typeof raw === 'string') return { mechanism: raw, example: '', pitfalls: [], versions: '', diagram: '' };
  return {
    mechanism: raw.mechanism ?? '',
    example: raw.example ?? '',
    pitfalls: raw.pitfalls ?? [],
    versions: raw.versions ?? '',
    diagram: raw.diagram ?? '',
  };
}

export function parseQuestion(raw: RawQuestion, course: string): Question {
  const answer = Array.from(raw.answer ?? []).map((a) => LETTERS.indexOf(a));
  return {
    course,
    id: raw.id,
    topic: raw.topic,
    sub: raw.sub,
    level: raw.level ?? 1,
    kind: raw.kind,
    prompt: raw.prompt,
    format: raw.format ?? 'choice',
    code: raw.code ?? '',
    choices: raw.choices ?? [],
    answer: [...new Set(answer)].sort((a, b) => a - b),
    accept: raw.accept ?? [],
    caseSensitive: raw.case ?? false,
    key: typeof raw.key === 'string' ? [raw.key] : (raw.key ?? []),
    traps: raw.traps ?? [],
    explain: raw.explain ?? '',
    why: raw.why ?? [],
    detail: asDetail(raw.detail),
    keyDetail: raw.key_detail ?? [],
    lesson: raw.lesson ?? '',
    trapsDetail: raw.traps_detail ?? [],
  };
}

export interface Catalog {
  rules: Rules;
  lessonsDone?: Set<string>; // "course:lesson", from lesson records (learner state)
  certExams?: CertRecord[]; // certificate exam results, by time
  courses: Course[]; // sorted by (order, slug)
  questions: Question[]; // curriculum file order: course, topic (by tier), sub
}

export function loadSnapshot(snap: Snapshot): Catalog {
  // Format 2 (Leitner rules) uses the built-in FSRS defaults; format 3 has no graphs.
  if (![2, 3, 4, 5, 6].includes(snap.format)) throw new Error(`unsupported courses.json format ${snap.format}`);
  const entries = snap.courses
    .map((c) => {
      const d = c.definition;
      // Array.prototype.sort is stable, so equal tiers keep their listed order.
      const topics = [...d.topic]
        .sort((a, b) => a.tier - b.tier)
        .map((t) => ({ slug: t.slug, tier: t.tier, title: t.title, subs: [...t.subs] }));
      const course: Course = {
        slug: c.slug,
        title: d.title,
        order: d.order ?? 100,
        paused: false,
        archived: false,
        ...courseGraph(c.graph, topics),
        lessonBodies: c.lesson_bodies ?? {},
        certs: null,
        certsErrors: [],
        passRatio: d.pass_ratio,
        kinds: [...d.kinds],
        codeLang: d.code_lang ?? '',
        topics,
      };
      if (c.certs) {
        // Never throw on bad content: certificates are dropped with their errors kept.
        try {
          const { certs, errors } = parseCerts(c.certs, course);
          course.certs = certs;
          course.certsErrors = errors;
        } catch (e) {
          course.certsErrors = [String(e)];
        }
      }
      return { course, raws: c.questions };
    })
    .sort((a, b) =>
      a.course.order !== b.course.order
        ? a.course.order - b.course.order
        : cmp(a.course.slug, b.course.slug),
    );
  const questions: Question[] = [];
  for (const { course, raws } of entries) {
    // Mirror the CLI, which reads banks topic by topic, sub by sub.
    for (const t of course.topics) {
      for (const s of t.subs) {
        for (const raw of raws) {
          if (raw.topic === t.slug && raw.sub === s) questions.push(parseQuestion(raw, course.slug));
        }
      }
    }
  }
  const rules: Rules = {
    fsrs: (snap.format === 3 && snap.rules?.fsrs) || DEFAULT_RULES.fsrs,
    levels: { ...DEFAULT_RULES.levels, ...snap.rules?.levels },
  };
  return { rules, courses: entries.map((e) => e.course), questions };
}

export function cmp(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Curriculum order: tier, topic, level, subtopic. */
export function courseGroups(c: Course, rules: Rules): Group[] {
  const out: Group[] = [];
  for (const t of c.topics)
    for (const level of levels(rules))
      for (const sub of t.subs) out.push({ course: c.slug, topic: t.slug, sub, level });
  return out;
}

/** Newest status record per course wins (stable by `t`, so file order breaks ties); default active. */
export function courseStatuses(records: StatusRecord[]): Map<string, StatusRecord['status']> {
  const sorted = [...records].sort((a, b) => cmp(a.t, b.t));
  return new Map(sorted.map((r) => [r.course, r.status]));
}

export function withStatuses(cat: Catalog, records: StatusRecord[]): Catalog {
  const latest = courseStatuses(records);
  return {
    ...cat,
    // Archived does everything paused does, so it sets both.
    courses: cat.courses.map((c) => ({
      ...c,
      paused: latest.get(c.slug) === 'paused' || latest.get(c.slug) === 'archived',
      archived: latest.get(c.slug) === 'archived',
    })),
  };
}

/** A course's graph, never throwing: anything malformed is ignored with its errors kept. */
function courseGraph(raw: RawGraph | undefined, topics: Topic[]): { graph: Graph | null; graphErrors: string[] } {
  if (!raw) return { graph: null, graphErrors: [] };
  try {
    const { graph, errors } = parseGraph(raw, new Set(topics.flatMap((t) => t.subs)));
    return { graph, graphErrors: errors };
  } catch (e) {
    return { graph: null, graphErrors: [String(e)] };
  }
}

export function topicOf(c: Course, sub: string): string | null {
  return c.topics.find((t) => t.subs.includes(sub))?.slug ?? null;
}

/** A topic's subtopics, shallow prerequisites first, listing order otherwise. */
export function subsByDepth(c: Course, t: Topic): string[] {
  const d = (s: string) => c.graph?.depth(s) ?? 0;
  return t.subs.map((s, i) => ({ s, i })).sort((a, b) => d(a.s) - d(b.s) || a.i - b.i).map((x) => x.s);
}

/** "unlocks generators, decorators" for a subtopic others list as a prerequisite, else "". */
export function unlocksLabel(c: Course, sub: string): string {
  const next = c.graph?.unlocks(sub) ?? [];
  return next.length ? `unlocks ${next.join(', ')}` : '';
}

/** Lessons done: the newest record per (course, lesson) across devices, stable by `t`. */
export function withLessons(cat: Catalog, records: LessonRecord[]): Catalog {
  const latest = new Map<string, string>();
  for (const r of [...records].sort((a, b) => cmp(a.t, b.t))) latest.set(`${r.course}:${r.lesson}`, r.status);
  return { ...cat, lessonsDone: new Set([...latest].filter(([, v]) => v === 'done').map(([k]) => k)) };
}

/** The catalog the app shows: archived courses removed (their progress stays in the logs). */
export function visibleCatalog(cat: Catalog): Catalog {
  return cat.courses.some((c) => c.archived) ? { ...cat, courses: cat.courses.filter((c) => !c.archived) } : cat;
}

/** Certificate exam results (learner state), sorted by time. */
export function withCertExams(cat: Catalog, records: CertRecord[]): Catalog {
  return { ...cat, certExams: [...records].sort((a, b) => cmp(a.t, b.t)) };
}
