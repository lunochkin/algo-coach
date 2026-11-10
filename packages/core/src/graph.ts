/** Prerequisite graph over subtopics (`docs/architecture/knowledge.md`, Gating). Mirrors the CLI. */

const MAX_LEVEL = 3;

export interface RawLesson {
  title?: string;
  file?: string;
  teaches?: string[];
  needs?: string[];
  pretest?: number;
  minutes?: number;
}

export interface RawGraph {
  format?: number;
  lesson?: Record<string, RawLesson>;
  exercise?: Record<string, unknown>; // reserved
  match_up_to?: number;
  needs?: Record<string, string[]>;
  edge?: { from: string; to: string; offset?: number }[];
  [future: string]: unknown; // unknown keys are ignored
}

export type Edge = [from: string, to: string, offset: number];

/** A reading node: teaches quiz levels, needs quiz levels or other lessons. */
export interface Lesson {
  slug: string;
  title: string;
  file: string;
  teaches: [sub: string, level: number][];
  needs: string[]; // "subtopic@level" or "lesson:<slug>"
  pretest: number;
  minutes: number | null; // reading time; else words / 200, rounded up
}

export class Graph {
  private memo = new Map<string, number>();

  readonly matchUpTo: number;
  readonly edges: Edge[];
  readonly lessons: Lesson[];

  constructor(matchUpTo: number, edges: Edge[], lessons: Lesson[] = []) {
    this.matchUpTo = matchUpTo;
    this.edges = edges;
    this.lessons = lessons;
  }

  lesson(slug: string): Lesson | undefined {
    return this.lessons.find((x) => x.slug === slug);
  }

  teaching(sub: string, level: number): Lesson[] {
    return this.lessons.filter((x) => x.teaches.some(([s, l]) => s === sub && l === level));
  }

  needs(sub: string): [string, number][] {
    return this.edges.filter(([f]) => f === sub).map(([, to, k]) => [to, k]);
  }

  /** Longest prerequisite chain below `sub`. */
  depth(sub: string, seen: Set<string> = new Set()): number {
    if (seen.has(sub)) return 0;
    const cached = this.memo.get(sub);
    if (cached !== undefined && !seen.size) return cached;
    const next = new Set(seen).add(sub);
    const d = Math.max(0, ...this.needs(sub).map(([to]) => 1 + this.depth(to, next)));
    if (!seen.size) this.memo.set(sub, d);
    return d;
  }

  /** Subtopics that list `sub` as a prerequisite. */
  unlocks(sub: string): string[] {
    return [...new Set(this.edges.filter(([, to]) => to === sub).map(([f]) => f))];
  }
}

const isInt = (x: unknown): x is number => typeof x === 'number' && Number.isInteger(x);
const repr = (x: unknown) => (typeof x === 'string' ? `'${x}'` : String(x));

/** "subtopic@level" -> [subtopic, level], or null when malformed or unknown. */
export function parseRef(ref: unknown, subs: Set<string>): [string, number] | null {
  if (typeof ref !== 'string' || !ref.includes('@')) return null;
  const at = ref.lastIndexOf('@');
  const s = ref.slice(0, at);
  const lv = ref.slice(at + 1);
  return subs.has(s) && /^\d+$/.test(lv) && Number(lv) <= MAX_LEVEL ? [s, Number(lv)] : null;
}

function parseLessons(raw: RawGraph, subs: Set<string>, errors: string[]): Lesson[] {
  const table = raw.lesson ?? {};
  if (typeof table !== 'object' || Array.isArray(table)) {
    errors.push('lesson must be a table of lessons');
    return [];
  }
  const out: Lesson[] = [];
  for (const [slug, t] of Object.entries(table)) {
    const at = `lesson ${slug}`;
    if (!t || typeof t !== 'object') {
      errors.push(`${at}: must be a table`);
      continue;
    }
    for (const f of ['title', 'file'] as const) {
      const v = t[f];
      if (!(typeof v === 'string' && v.trim())) errors.push(`${at}: ${f} is required`);
    }
    const teaches: [string, number][] = [];
    for (const r of t.teaches ?? []) {
      const ref = parseRef(r, subs);
      if (ref) teaches.push(ref);
      else errors.push(`${at}: bad ref ${repr(r)}`);
    }
    if (!teaches.length) errors.push(`${at}: teaches nothing`);
    const needs: string[] = [];
    for (const r of t.needs ?? []) {
      const ok = typeof r === 'string' && r.startsWith('lesson:') ? r.slice(7) in table : parseRef(r, subs) !== null;
      if (ok) needs.push(r);
      else errors.push(`${at}: bad ref ${repr(r)}`);
    }
    let pretest = t.pretest ?? 2;
    if (!isInt(pretest) || pretest < 0 || pretest > 5) {
      errors.push(`${at}: pretest must be 0-5`);
      pretest = 2;
    }
    let minutes: number | null = t.minutes ?? null;
    if (minutes !== null && (!isInt(minutes) || minutes < 1)) {
      errors.push(`${at}: minutes must be a whole number >= 1`);
      minutes = null;
    }
    out.push({ slug, title: t.title ?? '', file: t.file ?? '', teaches, needs, pretest, minutes });
  }
  return out;
}

/** A cycle across quiz levels and lessons (see the CLI's node_cycle). */
function nodeCycle(g: Graph): string[] | null {
  const deps = (n: string): string[] => {
    if (n.startsWith('lesson:')) return [...(g.lesson(n.slice(7))?.needs ?? [])];
    const at = n.lastIndexOf('@');
    const s = n.slice(0, at);
    const level = Number(n.slice(at + 1));
    const out = level ? [`${s}@${level - 1}`] : [];
    for (const [to, k] of g.needs(s)) {
      const need = Math.min(level, g.matchUpTo) + k;
      if (need <= MAX_LEVEL) out.push(`${to}@${need}`);
    }
    return [...out, ...g.teaching(s, level).map((x) => `lesson:${x.slug}`)];
  };
  const state = new Map<string, 1 | 2>();
  const visit = (n: string, path: string[]): string[] | null => {
    state.set(n, 1);
    for (const d of deps(n)) {
      if (state.get(d) === 1) return path.includes(d) ? [...path.slice(path.indexOf(d)), d] : [n, d];
      if (state.get(d) === undefined) {
        const found = visit(d, [...path, d]);
        if (found) return found;
      }
    }
    state.set(n, 2);
    return null;
  };
  for (const x of g.lessons) {
    const n = `lesson:${x.slug}`;
    if (state.get(n) === undefined) {
      const found = visit(n, [n]);
      if (found) return found;
    }
  }
  return null;
}

/** A graph, its errors and warnings; any error means the graph is ignored. Same wording as the CLI. */
export function parseGraph(
  raw: RawGraph,
  subs: Set<string>,
): { graph: Graph | null; errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  if (![1, 2].includes(raw.format ?? 1))
    return { graph: null, errors: [`graph format ${repr(raw.format)} not supported`], warnings };
  if (raw.exercise && Object.keys(raw.exercise).length) warnings.push('exercise tables are not supported yet; ignored');
  let match = raw.match_up_to ?? 1;
  if (!isInt(match) || match < 0 || match > MAX_LEVEL) {
    errors.push(`match_up_to must be a level 0-${MAX_LEVEL}`);
    match = 1;
  }
  const edges: Edge[] = [];
  for (const [f, tos] of Object.entries(raw.needs ?? {})) {
    if (!Array.isArray(tos)) {
      errors.push(`needs.${f} must be a list`);
      continue;
    }
    for (const to of tos) edges.push([f, to, 0]);
  }
  for (const e of raw.edge ?? []) {
    if (!e || typeof e !== 'object' || !('from' in e) || !('to' in e)) {
      errors.push(`edge ${JSON.stringify(e)} needs from and to`);
      continue;
    }
    edges.push([e.from, e.to, (e.offset ?? 0) as number]);
  }
  for (const [f, to, k] of edges) {
    for (const s of [f, to]) if (!subs.has(s)) errors.push(`unknown subtopic ${repr(s)}`);
    if (f === to) errors.push(`${f} needs itself`);
    if (!isInt(k) || k < 0) errors.push(`${f} -> ${to}: offset must be a whole number >= 0`);
    else if (Math.min(MAX_LEVEL, match) + k > MAX_LEVEL)
      errors.push(`${f} -> ${to}: offset ${k} needs a level above ${MAX_LEVEL}`);
  }
  const lessons = parseLessons(raw, subs, errors);
  const graph = new Graph(match, edges, lessons);
  // Subtopic cycles first (clearest message); level-and-lesson cycles only when lessons exist.
  const cycle = findCycle(graph) ?? (lessons.length && !errors.length ? nodeCycle(graph) : null);
  if (cycle) errors.push(`cycle: ${cycle.join(' -> ')}`);
  const unique = [...new Set(errors)];
  return { graph: unique.length ? null : graph, errors: unique, warnings };
}

function findCycle(g: Graph): string[] | null {
  const state = new Map<string, 1 | 2>();
  const visit = (s: string, path: string[]): string[] | null => {
    state.set(s, 1);
    for (const [to] of g.needs(s)) {
      if (state.get(to) === 1) return path.includes(to) ? [...path.slice(path.indexOf(to)), to] : [s, to];
      if (state.get(to) === undefined) {
        const found = visit(to, [...path, to]);
        if (found) return found;
      }
    }
    state.set(s, 2);
    return null;
  };
  for (const s of new Set(g.edges.map(([f]) => f))) {
    if (state.get(s) === undefined) {
      const found = visit(s, [s]);
      if (found) return found;
    }
  }
  return null;
}
