import type { Graph } from './graph';
import type { Course } from './types';

export interface MapNode {
  sub: string; // the subtopic slug, or "lesson:<slug>" for a lesson node
  kind: 'quiz' | 'lesson' | 'cert';
  topic: string; // empty for lessons and certificates
  layer: number; // longest prerequisite chain below it: 0 = no prerequisites
  index: number; // position within its layer, top to bottom
}

export interface MapEdge {
  from: string; // the prerequisite (left)
  to: string; // the dependent (right)
  offset: number;
  kind?: 'prereq' | 'teaches' | 'needs';
}

export interface MapLayout {
  nodes: MapNode[];
  edges: MapEdge[];
  layers: number;
  rows: number; // the most nodes in one layer
}

const SWEEPS = 4;

/**
 * Layered DAG layout: columns by longest-path depth, rows ordered by the barycenter heuristic
 * (alternating sweeps, keeping the order with fewest crossings). Deterministic.
 */
export function layoutGraph(course: Course, graph: Graph, withLessons = false): MapLayout {
  const listed: { sub: string; topic: string; kind: 'quiz' | 'lesson' | 'cert' }[] = course.topics.flatMap((t) =>
    t.subs.map((sub) => ({ sub, topic: t.slug, kind: 'quiz' as const })),
  );
  const known = new Set(listed.map((n) => n.sub));
  const edges: MapEdge[] = graph.edges
    .filter(([f, to]) => known.has(f) && known.has(to) && f !== to)
    .map(([f, to, offset]) => ({ from: to, to: f, offset, kind: 'prereq' }));
  const layerOf = new Map(listed.map((n) => [n.sub, graph.depth(n.sub)]));
  if (withLessons) {
    // A lesson sits in its own column just left of the earliest subtopic it teaches.
    for (const x of graph.lessons) {
      const taught = x.teaches.map(([s]) => s).filter((s) => known.has(s));
      if (!taught.length) continue;
      const id = `lesson:${x.slug}`;
      listed.push({ sub: id, topic: '', kind: 'lesson' });
      layerOf.set(id, Math.min(...taught.map((s) => layerOf.get(s)!)) * 2);
      for (const s of new Set(taught)) edges.push({ from: id, to: s, offset: 0, kind: 'teaches' });
      for (const r of x.needs) {
        const from = r.startsWith('lesson:') ? r : r.slice(0, r.lastIndexOf('@'));
        edges.push({ from, to: id, offset: 0, kind: 'needs' });
      }
    }
    for (const n of listed) if (n.kind === 'quiz') layerOf.set(n.sub, layerOf.get(n.sub)! * 2 + 1);
    // Drop empty columns so the map stays compact.
    const used = [...new Set(layerOf.values())].sort((a, b) => a - b);
    for (const [k, v] of layerOf) layerOf.set(k, used.indexOf(v));
    for (let i = edges.length - 1; i >= 0; i--) if (!layerOf.has(edges[i].from)) edges.splice(i, 1);
  }
  return arrange(listed, layerOf, edges);
}

/**
 * Columns from `layerOf`, rows by the barycenter heuristic (alternating sweeps, keeping the order
 * with fewest crossings); `listed` gives the starting order and the tie-break. Deterministic.
 */
export function arrange(
  listed: { sub: string; topic: string; kind: 'quiz' | 'lesson' | 'cert' }[],
  layerOf: Map<string, number>,
  edges: MapEdge[],
): MapLayout {
  const layers = Math.max(0, ...layerOf.values()) + 1;
  // Listing order is the starting point and the tie-break.
  let order: string[][] = Array.from({ length: layers }, () => []);
  for (const n of listed) order[layerOf.get(n.sub)!].push(n.sub);

  const prereqs = new Map<string, string[]>();
  const dependents = new Map<string, string[]>();
  for (const e of edges) {
    prereqs.set(e.to, [...(prereqs.get(e.to) ?? []), e.from]);
    dependents.set(e.from, [...(dependents.get(e.from) ?? []), e.to]);
  }

  let best = order.map((l) => [...l]);
  let bestCross = crossings(best, edges, layerOf);
  for (let sweep = 0; sweep < SWEEPS; sweep++) {
    const down = sweep % 2 === 0;
    const pos = positions(order);
    const range = down ? [...Array(layers).keys()].slice(1) : [...Array(layers).keys()].reverse().slice(1);
    for (const l of range) {
      const neighbours = down ? prereqs : dependents;
      const score = (s: string, i: number) => {
        const ns = (neighbours.get(s) ?? []).filter((n) => pos.has(n));
        return ns.length ? ns.reduce((a, n) => a + pos.get(n)!, 0) / ns.length : i;
      };
      order[l] = order[l]
        .map((s, i) => ({ s, i, b: score(s, i) }))
        .sort((a, b) => a.b - b.b || a.i - b.i)
        .map((x) => x.s);
      order[l].forEach((s, i) => pos.set(s, i));
    }
    const c = crossings(order, edges, layerOf);
    if (c < bestCross) {
      best = order.map((l) => [...l]);
      bestCross = c;
    }
    order = order.map((l) => [...l]);
  }

  const meta = new Map(listed.map((n) => [n.sub, n]));
  const nodes = best.flatMap((col, layer) =>
    col.map((sub, index) => ({ sub, kind: meta.get(sub)!.kind, topic: meta.get(sub)!.topic, layer, index })),
  );
  return { nodes, edges, layers, rows: Math.max(1, ...best.map((l) => l.length)) };
}

function positions(order: string[][]): Map<string, number> {
  const pos = new Map<string, number>();
  order.forEach((col) => col.forEach((s, i) => pos.set(s, i)));
  return pos;
}

/** Edge pairs that cross, between edges joining the same two layers. */
export function crossings(order: string[][], edges: MapEdge[], layerOf: Map<string, number>): number {
  const pos = positions(order);
  let n = 0;
  for (let i = 0; i < edges.length; i++) {
    for (let j = i + 1; j < edges.length; j++) {
      const a = edges[i];
      const b = edges[j];
      if (layerOf.get(a.from) !== layerOf.get(b.from) || layerOf.get(a.to) !== layerOf.get(b.to)) continue;
      if ((pos.get(a.from)! - pos.get(b.from)!) * (pos.get(a.to)! - pos.get(b.to)!) < 0) n++;
    }
  }
  return n;
}

/** All prerequisites of `sub`, transitively, and all subtopics that depend on it. */
export function lineage(edges: MapEdge[], sub: string): Set<string> {
  const out = new Set([sub]);
  const walk = (s: string, dir: 'up' | 'down') => {
    for (const e of edges) {
      const next = dir === 'up' ? (e.to === s ? e.from : null) : e.from === s ? e.to : null;
      if (next && !out.has(next)) {
        out.add(next);
        walk(next, dir);
      }
    }
  };
  walk(sub, 'up');
  walk(sub, 'down');
  return out;
}

/** A DAG of certificates: nodes in listing order, `needs` as (dependent, prerequisite) pairs. */
export function layoutDag(ids: string[], needs: [string, string][]): MapLayout {
  const edges: MapEdge[] = needs.map(([f, t]) => ({ from: t, to: f, offset: 0, kind: 'prereq' }));
  const layerOf = new Map<string, number>();
  const depth = (id: string, seen: Set<string> = new Set()): number => {
    const known = layerOf.get(id);
    if (known !== undefined) return known;
    if (seen.has(id)) return 0;
    const below = needs.filter(([f]) => f === id).map(([, t]) => 1 + depth(t, new Set(seen).add(id)));
    const d = Math.max(0, ...below);
    layerOf.set(id, d);
    return d;
  };
  for (const id of ids) depth(id);
  return arrange(
    ids.map((id) => ({ sub: id, topic: '', kind: 'cert' as const })),
    layerOf,
    edges,
  );
}

/** Box sizes for `layoutClusters` (the UI's node and spacing sizes). */
export interface ClusterDims {
  nodeW: number;
  nodeH: number;
  col: number; // column pitch inside a cluster
  row: number; // row pitch inside a cluster
  pad: number; // inside a cluster box
  header: number; // title band at the top of a cluster
  gapX: number; // between cluster columns
  gapY: number; // between clusters in one column
}

export interface PlacedNode {
  sub: string; // subtopic slug, "lesson:<slug>", or "cert:<scope>" (a topic's or the course's certificates)
  kind: 'quiz' | 'lesson' | 'cert';
  topic: string; // the cluster's topic; "all" for the course certificate node
  x: number;
  y: number;
}

export interface ClusterBox {
  topic: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ClusterLayout {
  nodes: PlacedNode[];
  edges: MapEdge[]; // inside clusters, lessons, and cert:<a> -> cluster:<b> / cert:<a> -> cert:all
  clusters: ClusterBox[];
  outside: Map<string, string[]>; // subtopic -> its prerequisites in other topics
  width: number;
  height: number;
}

/**
 * Topics as clusters, each laid out by its own prerequisite edges, with its certificate node as the
 * exit on the right. Cross-topic prerequisites are summarised as one edge from the prerequisite
 * topic's certificate node to the dependent cluster (transitively reduced); clusters sit in columns
 * by that topic graph's depth, and the course certificate node closes the map on the right.
 */
export function layoutClusters(course: Course, graph: Graph, d: ClusterDims, withLessons = false): ClusterLayout {
  const topics = course.topics.filter((t) => t.subs.length);
  const topicOf = new Map(topics.flatMap((t) => t.subs.map((s) => [s, t.slug] as const)));
  const intra: MapEdge[] = [];
  const outside = new Map<string, string[]>();
  const needsTopic = new Map<string, Set<string>>(topics.map((t) => [t.slug, new Set()]));
  for (const [f, to, offset] of graph.edges) {
    const a = topicOf.get(f);
    const b = topicOf.get(to);
    if (!a || !b || f === to) continue;
    if (a === b) intra.push({ from: to, to: f, offset, kind: 'prereq' });
    else {
      outside.set(f, [...(outside.get(f) ?? []), to]);
      needsTopic.get(a)!.add(b);
    }
  }

  // Topic columns by longest prerequisite chain; edges reduced to the direct ones.
  const tdepth = new Map<string, number>();
  const depthOf = (t: string, seen: Set<string> = new Set()): number => {
    if (tdepth.has(t)) return tdepth.get(t)!;
    if (seen.has(t)) return 0;
    seen.add(t);
    const v = Math.max(-1, ...[...needsTopic.get(t)!].map((u) => depthOf(u, seen))) + 1;
    tdepth.set(t, v);
    return v;
  };
  topics.forEach((t) => depthOf(t.slug));
  const reduced = reduceTopicEdges(
    topics.map((t) => t.slug),
    needsTopic,
  );

  // Each cluster's inner layout, relative to its box.
  const inner = new Map<string, { nodes: PlacedNode[]; w: number; h: number }>();
  for (const t of topics) {
    const subs = new Set(t.subs);
    const listed: { sub: string; topic: string; kind: 'quiz' | 'lesson' | 'cert' }[] = t.subs.map((sub) => ({
      sub,
      topic: t.slug,
      kind: 'quiz',
    }));
    const edges = intra.filter((e) => subs.has(e.from));
    const local = new Map<string, number>();
    const depth = (s: string, seen: Set<string> = new Set()): number => {
      if (local.has(s)) return local.get(s)!;
      if (seen.has(s)) return 0;
      seen.add(s);
      const v = Math.max(-1, ...edges.filter((e) => e.to === s).map((e) => depth(e.from, seen))) + 1;
      local.set(s, v);
      return v;
    };
    t.subs.forEach((s) => depth(s));
    const allEdges = [...edges];
    if (withLessons) {
      for (const x of graph.lessons) {
        const taught = x.teaches.map(([s]) => s).filter((s) => subs.has(s));
        if (!taught.length || topicOf.get(x.teaches[0][0]) !== t.slug) continue;
        const id = `lesson:${x.slug}`;
        listed.push({ sub: id, topic: t.slug, kind: 'lesson' });
        local.set(id, Math.min(...taught.map((s) => local.get(s)!)) * 2 - 0.5);
        for (const s of new Set(taught)) allEdges.push({ from: id, to: s, offset: 0, kind: 'teaches' });
        for (const r of x.needs) {
          if (r.startsWith('lesson:')) allEdges.push({ from: r, to: id, offset: 0, kind: 'needs' });
        }
      }
      for (const n of listed) if (n.kind === 'quiz') local.set(n.sub, local.get(n.sub)! * 2);
      const used = [...new Set(local.values())].sort((a, b) => a - b);
      for (const [k, v] of local) local.set(k, used.indexOf(v));
    }
    const lay = arrange(
      listed,
      local,
      allEdges.filter((e) => local.has(e.from) && local.has(e.to)),
    );
    intra.push(...allEdges.filter((e) => e.kind !== 'prereq' && local.has(e.from)));
    const certX = lay.layers * d.col;
    const rowsH = (lay.rows - 1) * d.row + d.nodeH;
    const h = d.header + d.pad * 2 + rowsH;
    const nodes: PlacedNode[] = lay.nodes.map((n) => {
      const inCol = lay.nodes.filter((m) => m.layer === n.layer).length;
      return {
        sub: n.sub,
        kind: n.kind,
        topic: t.slug,
        x: d.pad + n.layer * d.col,
        y: d.header + d.pad + (n.index + (lay.rows - inCol) / 2) * d.row,
      };
    });
    nodes.push({
      sub: `cert:${t.slug}`,
      kind: 'cert',
      topic: t.slug,
      x: d.pad + certX,
      y: d.header + d.pad + (rowsH - d.nodeH) / 2,
    });
    inner.set(t.slug, { nodes, w: d.pad * 2 + certX + d.nodeW, h });
  }

  // Cluster columns, each centred vertically on the tallest.
  const columns: string[][] = [];
  for (const t of topics) (columns[tdepth.get(t.slug)!] ??= []).push(t.slug);
  const colH = columns.map((ts) => ts.reduce((a, t) => a + inner.get(t)!.h, 0) + d.gapY * (ts.length - 1));
  const height = Math.max(d.nodeH, ...colH) + d.gapY * 2;
  const nodes: PlacedNode[] = [];
  const clusters: ClusterBox[] = [];
  let x = d.gapX / 2;
  columns.forEach((ts, i) => {
    let y = (height - colH[i]) / 2;
    const w = Math.max(...ts.map((t) => inner.get(t)!.w));
    for (const t of ts) {
      const box = inner.get(t)!;
      clusters.push({ topic: t, x, y, w: box.w, h: box.h });
      nodes.push(...box.nodes.map((n) => ({ ...n, x: n.x + x, y: n.y + y })));
      y += box.h + d.gapY;
    }
    x += w + d.gapX;
  });
  nodes.push({ sub: 'cert:all', kind: 'cert', topic: 'all', x, y: (height - d.nodeH) / 2 });
  const width = x + d.nodeW + d.gapX / 2;

  const edges: MapEdge[] = [
    ...intra,
    ...reduced.map(([a, b]) => ({ from: `cert:${b}`, to: `cluster:${a}`, offset: 0, kind: 'needs' as const })),
    ...topics
      .filter((t) => !topics.some((u) => reduced.some(([a, b]) => a === u.slug && b === t.slug)))
      .map((t) => ({ from: `cert:${t.slug}`, to: 'cert:all', offset: 0, kind: 'needs' as const })),
  ];
  return { nodes, edges, clusters, outside, width, height };
}

/** Topic prerequisites ([dependent, prerequisite]) without those implied through another topic. */
function reduceTopicEdges(topics: string[], needs: Map<string, Set<string>>): [string, string][] {
  const reach = (from: string, skip: string): boolean => {
    const stack = [...needs.get(from)!].filter((t) => t !== skip);
    const seen = new Set<string>();
    while (stack.length) {
      const t = stack.pop()!;
      if (t === skip) return true;
      if (seen.has(t)) continue;
      seen.add(t);
      stack.push(...needs.get(t)!);
    }
    return false;
  };
  return topics.flatMap((a) => [...needs.get(a)!].filter((b) => !reach(a, b)).map((b) => [a, b] as [string, string]));
}
