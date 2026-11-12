import type { CertState, CertStatus } from './certs';
import { levelName, levels, subTitle, topicTitle, unlocksLabel } from './courses';
import { aimedAt, type Focus } from './focus';
import { lineage, type ClusterLayout, type MapEdge, type PlacedNode } from './layout';
import { groupCell, type CellState } from './module';
import type { Board } from './schedule';
import type { Course } from './types';
import { alsoNeedsLine, levelLine, MODULE_FOCUS_HERE, MODULE_FOCUSED } from './words/module';

/**
 * Where a map opens: the focus's subtopic or topic where it aims inside the
 * module, else the first group with new work, centred across the view and a
 * third of the way down it, as a scroll offset at `scale`. Null where no node
 * is found, and the map is then fitted whole.
 */
export function mapOpening(
  b: Board,
  c: Course,
  nodes: readonly PlacedNode[],
  view: { w: number; h: number },
  scale: number,
  focus: Focus | null = null,
): { left: number; top: number } | null {
  const n = nodes.find((one) => one.kind === 'quiz' && one.sub === openingSub(b, c, nodes, focus));
  if (!n) return null;
  return {
    left: (n.x + MAP_DIMS.nodeW / 2) * scale - view.w / 2,
    top: (n.y + MAP_DIMS.nodeH / 2) * scale - view.h / 3,
  };
}

// the focus's subtopic, the first group with new work inside its topic, or the module's first
function openingSub(b: Board, c: Course, nodes: readonly PlacedNode[], focus: Focus | null): string | undefined {
  const frontier = b.frontier(c);
  if (focus?.course === c.slug && !focus.cert) {
    if (focus.sub) return focus.sub;
    if (focus.topic)
      return (
        frontier.find((g) => g.topic === focus.topic)?.sub ??
        nodes.find((n) => n.kind === 'quiz' && n.topic === focus.topic)?.sub
      );
  }
  return frontier[0]?.sub;
}

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
    lessonSlug(r) ? `lesson ${c.graph?.lesson(lessonSlug(r)!)?.title ?? r}` : levelOf(r),
  );
  return {
    title: x.title,
    state,
    teaches: `Teaches: ${x.teaches.map(([s, l]) => `${s} · ${levelName(b.rules, l)}`).join(', ')}`,
    needs: needs.length ? `Needs: ${needs.join(', ')}` : null,
    pretest: state === 'done' ? null : `Pretest: ${Math.min(b.tried(c, x), x.pretest)}/${x.pretest} questions tried`,
  };
}

/** The lesson a `lesson:<slug>` node or reference names; null for any other. */
export function lessonSlug(node: string): string | null {
  return node.startsWith('lesson:') ? node.slice(7) : null;
}

/** A label cut to `n` characters, the last an ellipsis. */
export function cut(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

/** Each topic's title by slug, and the module's under `all`: the clusters' and certificate nodes' labels. */
export function mapTitles(c: Course): Map<string, string> {
  return new Map([...c.topics.map((t) => [t.slug, t.title] as const), ['all', c.title] as const]);
}

export interface EdgePath {
  edge: MapEdge;
  d: string; // an SVG path: a horizontal bezier from the prerequisite's right side
  dash: [number, number] | null; // dotted for a lesson's, dashed for an offset or a certificate's
}

/** Each drawable edge of the map, as a path in the layout's coordinates. */
export function edgePaths(layout: ClusterLayout): EdgePath[] {
  const { nodeW: W, nodeH: H } = MAP_DIMS;
  const at = new Map(layout.nodes.map((n) => [n.sub, n]));
  return layout.edges.flatMap((edge) => {
    const a = at.get(edge.from);
    // an edge into a cluster ends at the middle of the cluster's left side
    const box = edge.to.startsWith('cluster:') ? layout.clusters.find((k) => k.topic === edge.to.slice(8)) : undefined;
    const z = box ? { x: box.x, y: box.y + box.h / 2 - H / 2 } : at.get(edge.to);
    if (!a || !z) return [];
    const [x1, y1, x2, y2] = [a.x + W, a.y + H / 2, z.x, z.y + H / 2];
    const mid = (x1 + x2) / 2;
    const dash: EdgePath['dash'] =
      edge.kind === 'teaches' ? [2, 3] : edge.offset || edge.from.startsWith('cert:') ? [6, 4] : null;
    return [{ edge, d: `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`, dash }];
  });
}

/** The chevron at a subtopic node's left, marking prerequisites in other topics. */
export function entryMark(n: PlacedNode): string {
  const y = n.y + MAP_DIMS.nodeH / 2;
  return `M${n.x - 6},${y - 5} L${n.x},${y} L${n.x - 6},${y + 5}`;
}

/** A subtopic node's panel: its level lines, what else it needs and unlocks, and its two presses. */
export interface NodeView {
  title: string;
  topic: string;
  levels: { line: string; empty: boolean }[];
  alsoNeeds: string | null;
  unlocks: string | null;
  aimed: boolean;
  aimLabel: string;
  scope: { course: string; topic: string; sub: string; level: null };
}

export function nodeView(b: Board, c: Course, n: { topic: string; sub: string }, focus: Focus | null): NodeView {
  const outside = alsoNeeds(c, n.sub, n.topic);
  const aimed = aimedAt(focus, c.slug, n.topic, n.sub);
  return {
    title: subTitle(c, n.sub),
    topic: topicTitle(c, n.topic),
    levels: levels(b.rules).map((level) => {
      const cell = groupCell(b, { course: c.slug, topic: n.topic, sub: n.sub, level });
      return { line: levelLine(levelName(b.rules, level), cell.line), empty: cell.state === 'empty' };
    }),
    alsoNeeds: outside.length ? alsoNeedsLine(outside) : null,
    unlocks: unlocksLabel(c, n.sub) || null,
    aimed,
    aimLabel: aimed ? MODULE_FOCUSED : MODULE_FOCUS_HERE,
    scope: { course: c.slug, topic: n.topic, sub: n.sub, level: null },
  };
}
