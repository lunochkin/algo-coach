import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { crossings, layoutClusters, layoutDag, layoutGraph, lineage, parseGraph, type Course, type RawGraph } from './index';

/** Just enough TOML for course.toml subs and graph.toml (`needs` lists, `[[edge]]` tables). */
function readPython(): { course: Course; raw: RawGraph } | null {
  const base = resolve(__dirname, '../../../content/modules/python');
  if (!existsSync(`${base}/graph.toml`)) return null;
  const strip = (s: string) => s.replace(/#.*$/gm, '');
  const courseToml = strip(readFileSync(`${base}/course.toml`, 'utf8'));
  const topics = [...courseToml.matchAll(/slug = "([^"]+)"[\s\S]*?subs = \[([\s\S]*?)\]/g)].map((m, i) => ({
    slug: m[1],
    tier: i,
    title: m[1],
    subs: [...m[2].matchAll(/"([^"]+)"/g)].map((x) => x[1]),
  }));
  const g = strip(readFileSync(`${base}/graph.toml`, 'utf8'));
  const needsBlock = g.split('[needs]')[1]?.split('[[edge]]')[0] ?? '';
  const needs = Object.fromEntries(
    [...needsBlock.matchAll(/"([^"]+)"\s*=\s*\[([^\]]*)\]/g)].map((m) => [m[1], [...m[2].matchAll(/"([^"]+)"/g)].map((x) => x[1])]),
  );
  const edge = g
    .split('[[edge]]')
    .slice(1)
    .map((b) => ({
      from: /from = "([^"]+)"/.exec(b)![1],
      to: /to = "([^"]+)"/.exec(b)![1],
      offset: Number(/offset = (\d+)/.exec(b)?.[1] ?? 0),
    }));
  const course = { slug: 'python', topics } as unknown as Course;
  return { course, raw: { format: 1, match_up_to: 1, needs, edge } };
}

const tiny = {
  slug: 'c',
  topics: [{ slug: 't', tier: 1, title: 'T', subs: ['d', 'a', 'c', 'b', 'e'] }],
} as unknown as Course;
const tinyGraph = parseGraph({ needs: { c: ['a'], d: ['b', 'a'], e: ['c', 'd'] } }, new Set(['a', 'b', 'c', 'd', 'e'])).graph!;

describe('graph layout', () => {
  it('puts every prerequisite in an earlier layer', () => {
    const l = layoutGraph(tiny, tinyGraph);
    const layer = new Map(l.nodes.map((n) => [n.sub, n.layer]));
    for (const e of l.edges) expect(layer.get(e.from)!).toBeLessThan(layer.get(e.to)!);
    expect(l.layers).toBe(3);
    expect(new Set(l.nodes.map((n) => `${n.layer}/${n.index}`)).size).toBe(l.nodes.length);
  });

  it('is deterministic', () => {
    expect(layoutGraph(tiny, tinyGraph)).toEqual(layoutGraph(tiny, tinyGraph));
  });

  it('places a lesson just left of what it teaches', () => {
    const g = parseGraph(
      {
        format: 2,
        needs: { c: ['a'] },
        lesson: { l: { title: 'L', file: 'l.md', teaches: ['c@0'], needs: ['a@0'] } },
      },
      new Set(['a', 'b', 'c', 'd', 'e']),
    ).graph!;
    const l = layoutGraph(tiny, g, true);
    const col = new Map(l.nodes.map((n) => [n.sub, n.layer]));
    expect(l.nodes.find((n) => n.sub === 'lesson:l')?.kind).toBe('lesson');
    expect(col.get('lesson:l')!).toBeLessThan(col.get('c')!);
    expect(col.get('a')!).toBeLessThan(col.get('lesson:l')!);
    expect(layoutGraph(tiny, g, false).nodes.some((n) => n.kind === 'lesson')).toBe(false);
  });

  it('lays out a certificate DAG with prerequisites to the left', () => {
    const ids = ['c-a-foundation', 'c-a-associate', 'c-b-foundation', 'c-all-foundation'];
    const needs: [string, string][] = [
      ['c-a-associate', 'c-a-foundation'],
      ['c-b-foundation', 'c-a-foundation'],
      ['c-all-foundation', 'c-b-foundation'],
    ];
    const l = layoutDag(ids, needs);
    const col = new Map(l.nodes.map((n) => [n.sub, n.layer]));
    for (const [f, t] of needs) expect(col.get(t)!).toBeLessThan(col.get(f)!);
    expect(l.nodes.every((n) => n.kind === 'cert')).toBe(true);
  });

  it('finds ancestors and descendants', () => {
    const l = layoutGraph(tiny, tinyGraph);
    expect([...lineage(l.edges, 'c')].sort()).toEqual(['a', 'c', 'e']);
  });

  const py = readPython();
  it.skipIf(!py)('reduces crossings on the Python graph', () => {
    const { course, raw } = py!;
    const { graph, errors } = parseGraph(raw, new Set(course.topics.flatMap((t) => t.subs)));
    expect(errors).toEqual([]);
    const l = layoutGraph(course, graph!);
    const layerOf = new Map(l.nodes.map((n) => [n.sub, n.layer]));
    const laid: string[][] = Array.from({ length: l.layers }, () => []);
    for (const n of [...l.nodes].sort((a, b) => a.index - b.index)) laid[n.layer].push(n.sub);
    const listed: string[][] = Array.from({ length: l.layers }, () => []);
    for (const t of course.topics) for (const s of t.subs) listed[layerOf.get(s)!].push(s);
    expect(crossings(laid, l.edges, layerOf)).toBeLessThanOrEqual(crossings(listed, l.edges, layerOf));
    expect(l.nodes).toHaveLength(course.topics.flatMap((t) => t.subs).length);
  });
});

const DIMS = { nodeW: 164, nodeH: 56, col: 200, row: 74, pad: 16, header: 28, gapX: 80, gapY: 32 };

describe('cluster layout', () => {
  const two = {
    slug: 'c',
    topics: [
      { slug: 'base', tier: 1, title: 'Base', subs: ['a', 'b'] },
      { slug: 'top', tier: 2, title: 'Top', subs: ['x', 'y'] },
    ],
  } as unknown as Course;
  const g = parseGraph({ needs: { b: ['a'], x: ['a'], y: ['x', 'b'] } }, new Set(['a', 'b', 'x', 'y'])).graph!;

  it('keeps cross-topic edges out of clusters and summarises them through certificate nodes', () => {
    const l = layoutClusters(two, g, DIMS);
    expect(l.edges.filter((e) => e.kind === 'prereq').map((e) => `${e.from}>${e.to}`).sort()).toEqual(['a>b', 'x>y']);
    expect(l.edges.filter((e) => e.kind === 'needs').map((e) => `${e.from}>${e.to}`)).toEqual([
      'cert:base>cluster:top',
      'cert:top>cert:all',
    ]);
    expect(l.outside.get('x')).toEqual(['a']);
    expect(l.outside.get('y')).toEqual(['b']);
  });

  it('puts a dependent cluster right of its prerequisite and nodes inside their boxes', () => {
    const l = layoutClusters(two, g, DIMS);
    const box = new Map(l.clusters.map((c) => [c.topic, c]));
    expect(box.get('top')!.x).toBeGreaterThan(box.get('base')!.x + box.get('base')!.w);
    for (const n of l.nodes.filter((n) => n.topic !== 'all')) {
      const b = box.get(n.topic)!;
      expect(n.x).toBeGreaterThanOrEqual(b.x);
      expect(n.x + DIMS.nodeW).toBeLessThanOrEqual(b.x + b.w);
      expect(n.y).toBeGreaterThanOrEqual(b.y);
      expect(n.y + DIMS.nodeH).toBeLessThanOrEqual(b.y + b.h);
    }
  });

  const python = readPython();
  it.skipIf(!python)('lays out the Python graph without overlapping clusters', () => {
    const { course, raw } = python!;
    const { graph } = parseGraph(raw, new Set(course.topics.flatMap((t) => t.subs)));
    const l = layoutClusters(course, graph!, DIMS);
    expect(l.clusters).toHaveLength(course.topics.filter((t) => t.subs.length).length);
    for (const a of l.clusters)
      for (const b of l.clusters)
        if (a !== b) expect(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y).toBe(true);
    expect(l.edges.filter((e) => e.from.startsWith('cert:')).length).toBeLessThan(24);
  });
});
