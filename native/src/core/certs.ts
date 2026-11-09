/** Certifications (`docs/architecture/knowledge.md`, Certifications). Mirrors the CLI; same error wording. */
import type { Graph } from './graph';
import type { Board } from './schedule';
import type { Course, Question } from './types';

export const LEVEL_SLUGS = ['foundation', 'associate', 'professional', 'expert'];
const LEVEL_NAMES = ['Foundation', 'Associate', 'Professional', 'Expert'];
export const COURSE_SCOPE = 'all';

export interface CertRule {
  size: number;
  passShare: number;
  stabilityDays: number;
  share: number;
  coverageRatio: number | null; // null: the course pass_ratio
  requireExam: boolean;
  lapse: boolean;
  minPoolRatio: number; // exam pool (non-card questions) must be >= ratio x size
}

export interface Cert {
  id: string;
  scope: string; // topic slug, or "all"
  level: number;
  title: string;
  rule: CertRule;
  certified: boolean; // false: practice only, outside the DAG
}

export class Certs {
  constructor(
    readonly certs: Cert[],
    readonly edges: [from: string, to: string][], // from needs to
  ) {}

  get(id: string): Cert | undefined {
    return this.certs.find((x) => x.id === id);
  }

  needs(id: string): string[] {
    return this.edges.filter(([f]) => f === id).map(([, t]) => t);
  }
}

export interface RawCerts {
  format?: number;
  defaults?: RawRule;
  scope?: Record<string, RawRule & Record<string, unknown>>;
  edge?: { from?: string; to?: string }[];
  unedge?: { from?: string; to?: string }[];
}

interface RawRule {
  exam?: { size?: number; pass?: number };
  retention?: { stability_days?: number; share?: number };
  coverage_ratio?: number;
  require_exam?: boolean;
  lapse?: boolean;
  min_pool_ratio?: number;
  levels?: number[];
}

export interface CertRecord {
  t: string;
  course: string;
  cert: string;
  score: number;
  n: number;
  passed: boolean;
}

const BASE: CertRule = {
  size: 30,
  passShare: 0.8,
  stabilityDays: 7,
  share: 0.8,
  coverageRatio: null,
  requireExam: true,
  lapse: true,
  minPoolRatio: 0,
};

function merge(rule: CertRule, t: RawRule | undefined): CertRule {
  if (!t) return rule;
  return {
    size: t.exam?.size ?? rule.size,
    passShare: t.exam?.pass ?? rule.passShare,
    stabilityDays: t.retention?.stability_days ?? rule.stabilityDays,
    share: t.retention?.share ?? rule.share,
    coverageRatio: t.coverage_ratio ?? rule.coverageRatio,
    requireExam: t.require_exam ?? rule.requireExam,
    lapse: t.lapse ?? rule.lapse,
    minPoolRatio: t.min_pool_ratio ?? rule.minPoolRatio,
  };
}

/** A `levels` list: certified levels of a scope (default: all). */
function certLevels(t: RawRule | undefined, fallback: number[], where: string, errors: string[]): number[] {
  if (!t || !('levels' in t)) return fallback;
  const v = t.levels;
  if (!Array.isArray(v) || v.some((x) => !Number.isInteger(x) || x < 0 || x >= LEVEL_SLUGS.length)) {
    errors.push(`${where}: levels must be a list of levels 0-${LEVEL_SLUGS.length - 1}`);
    return fallback;
  }
  return [...new Set(v)].sort((a, b) => a - b);
}

export const certId = (course: string, scope: string, level: number) => `${course}-${scope}-${LEVEL_SLUGS[level]}`;

/** Transitive reduction of a DAG: drop u -> v when v is reachable from u another way. */
export function reduceEdges(nodes: string[], edges: [string, string][]): [string, string][] {
  const out = new Map(nodes.map((n) => [n, [] as string[]]));
  for (const [f, t] of edges) if (!out.get(f)!.includes(t)) out.get(f)!.push(t);
  const reach = (start: string, skip: string): Set<string> => {
    const seen = new Set<string>();
    const stack = out.get(start)!.filter((t) => t !== skip);
    while (stack.length) {
      const n = stack.pop()!;
      if (!seen.has(n)) {
        seen.add(n);
        stack.push(...out.get(n)!);
      }
    }
    return seen;
  };
  return nodes.flatMap((f) => out.get(f)!.filter((t) => !reach(f, t).has(t)).map((t) => [f, t] as [string, string]));
}

export function dagCycle(nodes: string[], edges: [string, string][]): string[] | null {
  const out = new Map(nodes.map((n) => [n, [] as string[]]));
  for (const [f, t] of edges) out.get(f)!.push(t);
  const state = new Map<string, 1 | 2>();
  const visit = (n: string, path: string[]): string[] | null => {
    state.set(n, 1);
    for (const d of out.get(n)!) {
      if (state.get(d) === 1) return path.includes(d) ? [...path.slice(path.indexOf(d)), d] : [n, d];
      if (state.get(d) === undefined) {
        const found = visit(d, [...path, d]);
        if (found) return found;
      }
    }
    state.set(n, 2);
    return null;
  };
  for (const n of nodes) {
    if (state.get(n) === undefined) {
      const found = visit(n, [n]);
      if (found) return found;
    }
  }
  return null;
}

const repr = (x: unknown) => (typeof x === 'string' ? `'${x}'` : String(x));

/** Certificates for every scope and level with their derived, reduced and overridden DAG. */
export function parseCerts(raw: RawCerts, c: Pick<Course, 'slug' | 'title' | 'topics'> & { graph: Graph | null }) {
  const errors: string[] = [];
  if ((raw.format ?? 1) !== 1) return { certs: null, errors: [`certs format ${repr(raw.format)} not supported`] };
  const scopes = [...c.topics.map((t) => t.slug), COURSE_SCOPE];
  const base = merge(BASE, raw.defaults);
  const baseLevels = certLevels(raw.defaults, [0, 1, 2, 3], 'defaults', errors);
  const tables = raw.scope ?? {};
  for (const s of Object.keys(tables)) if (!scopes.includes(s)) errors.push(`unknown scope ${repr(s)}`);
  const certs: Cert[] = [];
  for (const s of scopes) {
    const st = tables[s];
    const on = certLevels(st, baseLevels, `scope.${s}`, errors);
    for (let lv = 0; lv < LEVEL_SLUGS.length; lv++) {
      const rule = merge(merge(base, st), st?.[LEVEL_SLUGS[lv]] as RawRule | undefined);
      const title = s === COURSE_SCOPE ? c.title : c.topics.find((t) => t.slug === s)!.title;
      certs.push({
        id: certId(c.slug, s, lv),
        scope: s,
        level: lv,
        title: `${title} ${LEVEL_NAMES[lv]}`,
        rule,
        certified: on.includes(lv),
      });
    }
  }
  const ids = certs.map((x) => x.id);
  const certified = new Set(certs.filter((x) => x.certified).map((x) => x.id));
  const match = c.graph?.matchUpTo ?? 1;
  const topicOf = (sub: string) => c.topics.find((t) => t.subs.includes(sub))?.slug;
  const topicNeeds = new Map(c.topics.map((t) => [t.slug, new Set<string>()]));
  for (const [f, to] of c.graph?.edges ?? []) {
    const a = topicOf(f);
    const b = topicOf(to);
    if (a && b && a !== b) topicNeeds.get(a)!.add(b);
  }
  let edges: [string, string][] = [];
  for (const s of scopes) {
    for (let lv = 0; lv < LEVEL_SLUGS.length; lv++) {
      const me = certId(c.slug, s, lv);
      if (lv) edges.push([me, certId(c.slug, s, lv - 1)]);
      if (s === COURSE_SCOPE) edges.push(...c.topics.map((t) => [me, certId(c.slug, t.slug, lv)] as [string, string]));
      else
        edges.push(
          ...[...topicNeeds.get(s)!].sort().map((b) => [me, certId(c.slug, b, Math.min(lv, match))] as [string, string]),
        );
    }
  }
  // Uncertified levels are not part of the DAG: their edges go, nothing needs them.
  edges = edges.filter(([f, t]) => certified.has(f) && certified.has(t));
  const derivedCycle = dagCycle(ids, edges);
  if (derivedCycle) return { certs: null, errors: [...errors, `derived certificate cycle: ${derivedCycle.join(' -> ')}`] };
  edges = reduceEdges(ids, edges);
  for (const [key, add] of [
    ['edge', true],
    ['unedge', false],
  ] as const) {
    for (const e of raw[key] ?? []) {
      const f = e?.from;
      const t = e?.to;
      const bad = [f, t].filter((x) => !ids.includes(x as string));
      const uncertified = [f, t].filter((x) => !certified.has(x as string));
      if (bad.length) errors.push(...bad.map((x) => `${key}: unknown certificate ${repr(x)}`));
      else if (uncertified.length) errors.push(...uncertified.map((x) => `${key}: ${x} is not certified`));
      else if (add && !edges.some(([a, b]) => a === f && b === t)) edges.push([f!, t!]);
      else if (!add) edges = edges.filter(([a, b]) => !(a === f && b === t));
    }
  }
  const cycle = dagCycle(ids, edges);
  if (cycle) errors.push(`certificate cycle: ${cycle.join(' -> ')}`);
  return { certs: errors.length ? null : new Certs(certs, edges), errors };
}

export type CertState =
  | 'not_certified'
  | 'empty'
  | 'insufficient_pool'
  | 'locked'
  | 'in_progress'
  | 'ready'
  | 'earned'
  | 'needs_refresh';

export interface CertStatus {
  state: CertState;
  coverage: number; // passed share of the level's questions
  retention: number; // share with stability >= the rule's days
  questions: number;
  passed: number; // questions ever passed
  pool: number; // exam pool: non-card questions
  blockers: string[];
  short: { sub: string; topic: string; passed: number; total: number }[]; // subtopics below coverage
  lastExam: CertRecord | null;
}

const MAX_LEVEL = LEVEL_SLUGS.length - 1;

/** A certificate's groups ("sub@level"), closed under the ladder and the prerequisite graph (spec). */
export function certScope(c: Pick<Course, 'topics' | 'graph'>, x: Cert): Set<string> {
  const todo: [string, number][] = c.topics
    .filter((t) => x.scope === COURSE_SCOPE || t.slug === x.scope)
    .flatMap((t) => t.subs.flatMap((s) => Array.from({ length: x.level + 1 }, (_, lv) => [s, lv] as [string, number])));
  const out = new Set<string>();
  while (todo.length) {
    const [s, lv] = todo.pop()!;
    const key = `${s}@${lv}`;
    if (out.has(key)) continue;
    out.add(key);
    for (let low = 0; low < lv; low++) todo.push([s, low]);
    for (const [to, k] of c.graph?.needs(s) ?? []) {
      const need = Math.min(Math.min(lv, c.graph!.matchUpTo) + k, MAX_LEVEL);
      for (let low = 0; low <= need; low++) todo.push([to, low]);
    }
  }
  return out;
}

export function certQuestions(b: Board, c: Course, x: Cert): Question[] {
  return c.topics
    .filter((t) => x.scope === COURSE_SCOPE || t.slug === x.scope)
    .flatMap((t) => t.subs.flatMap((sub) => b.groupQuestions({ course: c.slug, topic: t.slug, sub, level: x.level })));
}

const EARNED: CertState[] = ['earned', 'needs_refresh', 'empty'];

/** State and progress of every certificate of `c`, from history and exam records. */
export function certStates(b: Board, c: Course, exams: CertRecord[]): Map<string, CertStatus> {
  const out = new Map<string, CertStatus>();
  const certs = c.certs;
  if (!certs) return out;
  const state = (id: string): CertStatus => {
    const done = out.get(id);
    if (done) return done;
    const x = certs.get(id)!;
    const qs = certQuestions(b, c, x);
    const ratio = x.rule.coverageRatio ?? c.passRatio;
    const short: CertStatus['short'] = [];
    for (const t of c.topics.filter((t) => x.scope === COURSE_SCOPE || t.slug === x.scope)) {
      for (const sub of t.subs) {
        const g = { course: c.slug, topic: t.slug, sub, level: x.level };
        const total = b.groupQuestions(g).length;
        if (total && b.nPassed(g) / total < ratio) short.push({ sub, topic: t.slug, passed: b.nPassed(g), total });
      }
    }
    const stable = qs.filter((q) => (b.memory(q)?.stability ?? 0) >= x.rule.stabilityDays).length;
    const coverage = qs.length ? qs.filter((q) => b.attempts(q).some((a) => a.rating === 3)).length / qs.length : 1;
    const retention = qs.length ? stable / qs.length : 1;
    const prereqs = new Map(certs.needs(id).map((p) => [p, state(p).state]));
    const records = exams.filter((r) => r.course === c.slug && r.cert === id);
    const examOk = records.some((r) => r.passed);
    const covered = short.length === 0;
    const retained = retention >= x.rule.share;
    // A prerequisite that needs a refresh still counts as earned: no cascades.
    const open = [...prereqs.values()].every((s) => EARNED.includes(s));
    const pool = qs.filter((q) => q.format !== 'card').length;
    let st: CertState;
    if (!x.certified) st = 'not_certified';
    else if (!qs.length) st = 'empty';
    else if (pool < x.rule.minPoolRatio * x.rule.size) st = 'insufficient_pool';
    else if (!open) st = 'locked';
    else if (examOk || !x.rule.requireExam) {
      const ok = covered && retained;
      st = ok || (examOk && !x.rule.lapse) ? 'earned' : examOk ? 'needs_refresh' : 'in_progress';
    } else st = covered && retained ? 'ready' : 'in_progress';
    const blockers = [...prereqs].filter(([, s]) => !EARNED.includes(s)).map(([p, s]) => `needs ${p} (${s})`);
    blockers.push(...short.map((g) => `${g.sub}: ${g.passed}/${g.total} passed, needs ${Math.round(ratio * 100)}%`));
    if (!retained)
      blockers.push(`retention ${Math.round(retention * 100)}%, needs ${Math.round(x.rule.share * 100)}% at ${x.rule.stabilityDays} days`);
    if (st === 'insufficient_pool')
      blockers.unshift(`not enough questions yet: ${pool} of ${Math.ceil(x.rule.minPoolRatio * x.rule.size)} for the exam pool`);
    const status: CertStatus = {
      state: st,
      coverage,
      retention,
      questions: qs.length,
      passed: qs.filter((q) => b.attempts(q).some((a) => a.rating === 3)).length,
      pool,
      blockers,
      short,
      lastExam: records.at(-1) ?? null,
    };
    out.set(id, status);
    return status;
  };
  for (const x of certs.certs) state(x.id);
  return out;
}
