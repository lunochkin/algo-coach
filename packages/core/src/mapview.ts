import type { CertState, CertStatus } from './certs';
import { levelName, levels } from './courses';
import type { Focus } from './focus';
import { lineage, type ClusterLayout, type PlacedNode } from './layout';
import { groupCell, type CellState } from './module';
import type { Board } from './schedule';
import type { Course } from './types';

/** The sizes a module's map is laid out at, on both clients. */
export const MAP_DIMS = { nodeW: 164, nodeH: 56, col: 200, row: 74, pad: 16, header: 32, gapX: 96, gapY: 40 };

const LETTERS = ['F', 'A', 'P', 'E'];

/** Subtopics upstream (`up`) or downstream of `start` in the real prerequisite graph. */
export function reach(c: Course, start: string[], up: boolean): Set<string> {
  const out = new Set(start);
  const stack = [...start];
  while (stack.length) {
    const s = stack.pop()!;
    for (const [f, t] of c.graph?.edges ?? []) {
      const next = up ? (f === s ? t : null) : t === s ? f : null;
      if (next && !out.has(next)) {
        out.add(next);
        stack.push(next);
      }
    }
  }
  return out;
}

/**
 * What the map lights: the picked node's lineage across clusters, with the
 * clusters and certificate nodes it passes through. With nothing picked, a
 * certification focus lights its scope. Null lights everything.
 */
export function mapLit(
  c: Course,
  layout: ClusterLayout,
  picked: string | null,
  focus: Focus | null,
): Set<string> | null {
  const around = (subs: Set<string>, extra: string[]) => {
    const out = new Set<string>([...subs, ...extra]);
    for (const s of subs) {
      const t = c.topics.find((x) => x.subs.includes(s))?.slug;
      if (t) out.add(`cluster:${t}`).add(`cert:${t}`);
    }
    return out;
  };
  if (picked?.startsWith('lesson:')) return lineage(layout.edges, picked);
  if (picked === 'cert:all') return null;
  if (picked?.startsWith('cert:')) {
    const own = c.topics.find((t) => t.slug === picked.slice(5))?.subs ?? [];
    return around(reach(c, own, true), [picked]);
  }
  if (picked) return around(new Set([...reach(c, [picked], true), ...reach(c, [picked], false)]), []);
  if (focus?.cert && focus.course === c.slug && focus.scope) {
    return around(new Set([...focus.scope].map((g) => g.slice(0, g.lastIndexOf('@')))), [
      `cert:${focus.topic ?? 'all'}`,
    ]);
  }
  return null;
}

/** Each subtopic node's level dots: a group's state, or null where it holds no questions. */
export function levelDots(b: Board, c: Course, nodes: PlacedNode[]): Map<string, (CellState | null)[]> {
  const out = new Map<string, (CellState | null)[]>();
  for (const n of nodes) {
    if (n.kind !== 'quiz') continue;
    out.set(
      n.sub,
      levels(b.rules).map((level) => {
        const s = groupCell(b, { course: c.slug, topic: n.topic, sub: n.sub, level }).state;
        return s === 'empty' ? null : s;
      }),
    );
  }
  return out;
}

export interface CertPip {
  letter: string; // F, A, P, E
  state: CertState;
  filled: boolean; // earned
}

/** A certificate node's pips: one per certified level of its scope, by state. */
export function certPips(c: Course, states: Map<string, CertStatus>, nodes: PlacedNode[]): Map<string, CertPip[]> {
  const out = new Map<string, CertPip[]>();
  for (const n of nodes) {
    if (n.kind !== 'cert') continue;
    out.set(
      n.sub,
      scopeCerts(c, n.topic).map((x) => {
        const state = states.get(x.id)?.state ?? 'locked';
        return { letter: LETTERS[x.level], state, filled: state === 'earned' };
      }),
    );
  }
  return out;
}

/** The certificate a scope's node opens: the next one to earn, else its highest. */
export function certToOpen(c: Course, states: Map<string, CertStatus>, scope: string): string | null {
  const xs = scopeCerts(c, scope);
  const next = xs.find((x) => !['earned', 'empty'].includes(states.get(x.id)?.state ?? ''));
  return (next ?? xs.at(-1))?.id ?? null;
}

function scopeCerts(c: Course, scope: string) {
  return (c.certs?.certs ?? []).filter((x) => x.scope === scope && x.certified);
}

/** A subtopic's prerequisites in other topics, which the map draws only as the edge into its cluster. */
export function alsoNeeds(c: Course, sub: string, topic: string): string[] {
  return (c.graph?.needs(sub) ?? [])
    .map(([to]) => [to, c.topics.find((t) => t.subs.includes(to))?.slug] as const)
    .filter(([, t]) => t && t !== topic)
    .map(([to, t]) => `${to} (${t})`);
}

/** A lesson node's panel: its state, what it teaches and needs, and its pretest so far. */
export interface LessonView {
  title: string;
  state: string;
  teaches: string;
  needs: string | null;
  pretest: string | null;
}

export function lessonView(b: Board, c: Course, slug: string): LessonView | null {
  const x = c.graph?.lesson(slug);
  if (!x) return null;
  const state = b.lessonState(c, x);
  const levelOf = (ref: string) => {
    const at = ref.lastIndexOf('@');
    return `${ref.slice(0, at)} · ${levelName(b.rules, Number(ref.slice(at + 1)))}`;
  };
  const needs = x.needs.map((r) =>
    r.startsWith('lesson:') ? `lesson ${c.graph?.lesson(r.slice(7))?.title ?? r}` : levelOf(r),
  );
  return {
    title: x.title,
    state,
    teaches: `Teaches: ${x.teaches.map(([s, l]) => `${s} · ${levelName(b.rules, l)}`).join(', ')}`,
    needs: needs.length ? `Needs: ${needs.join(', ')}` : null,
    pretest: state === 'done' ? null : `Pretest: ${Math.min(b.tried(c, x), x.pretest)}/${x.pretest} questions tried`,
  };
}
