import { describe, expect, it } from 'vitest';

import {
  alsoNeeds,
  Board,
  cut,
  edgePaths,
  layoutClusters,
  lessonSlug,
  levelDots,
  loadSnapshot,
  MAP_DIMS,
  mapLit,
  mapOpening,
  mapTitles,
  nodeView,
  reach,
} from './index';

const mk = (id: string, sub: string, level: number) => ({
  id,
  topic: sub === 'x' ? 'u' : 't',
  sub,
  level,
  kind: 'concept',
  prompt: id,
  format: 'choice' as const,
  choices: ['a', 'b', 'c'],
  answer: ['A'],
});
// a needs nothing, b needs a, c needs b; x sits in another topic and needs c
const catalog = loadSnapshot({
  format: 6,
  courses: [
    {
      slug: 'm',
      definition: {
        title: 'M',
        pass_ratio: 1,
        kinds: ['concept'],
        topic: [
          { slug: 't', tier: 1, title: 'T', subs: ['a', 'b', 'c'] },
          { slug: 'u', tier: 2, title: 'U', subs: ['x'] },
        ],
      },
      questions: [mk('q1', 'a', 0), mk('q2', 'b', 0), mk('q3', 'c', 0), mk('q4', 'x', 0)],
      graph: { format: 2, needs: { b: ['a'], c: ['b'], x: ['c'] } },
    },
  ],
} as never);
const [c] = catalog.courses;

describe("the map's opening", () => {
  it('centres the first group with new work across the view, a third down it', () => {
    const layout = layoutClusters(c, c.graph!, MAP_DIMS);
    const a = layout.nodes.find((n) => n.sub === 'a')!;
    const at = mapOpening(Board.build(catalog, []), c, layout.nodes, { w: 300, h: 600 }, 1)!;
    expect(at).toEqual({ left: a.x + MAP_DIMS.nodeW / 2 - 150, top: a.y + MAP_DIMS.nodeH / 2 - 200 });
  });
});

describe('the map', () => {
  it("reaches a subtopic's prerequisites upstream and its dependents downstream", () => {
    expect([...reach(c, ['b'], true)].sort()).toEqual(['a', 'b']);
    expect([...reach(c, ['b'], false)].sort()).toEqual(['b', 'c', 'x']);
  });

  it("lights a picked subtopic's whole lineage, with the clusters it passes through", () => {
    const layout = layoutClusters(c, c.graph!, MAP_DIMS);
    const lit = mapLit(c, layout, 'b', null)!;
    expect(['a', 'b', 'c', 'x', 'cluster:t', 'cluster:u'].every((k) => lit.has(k))).toBe(true);
  });

  it('lights everything where nothing is picked and no certification is the focus', () => {
    expect(mapLit(c, layoutClusters(c, c.graph!, MAP_DIMS), null, null)).toBeNull();
  });

  it('dots each level of a subtopic by its group, and skips a level holding no questions', () => {
    const board = Board.build(catalog, []);
    const dots = levelDots(board, c, layoutClusters(c, c.graph!, MAP_DIMS).nodes);
    expect(dots.get('a')?.slice(0, 2)).toEqual(['open', null]);
  });

  it("names a subtopic's prerequisites in other topics", () => {
    expect(alsoNeeds(c, 'x', 'u')).toEqual(['c (t)']);
    expect(alsoNeeds(c, 'b', 't')).toEqual([]);
  });

  it('draws an edge from the right side of its prerequisite to the left side of its dependent', () => {
    const layout = layoutClusters(c, c.graph!, MAP_DIMS);
    const e = edgePaths(layout).find((p) => p.edge.from === 'a' && p.edge.to === 'b')!;
    const [a, b] = ['a', 'b'].map((s) => layout.nodes.find((n) => n.sub === s)!);
    expect(e.d.startsWith(`M${a.x + MAP_DIMS.nodeW},${a.y + MAP_DIMS.nodeH / 2} `)).toBe(true);
    expect(e.d.endsWith(` ${b.x},${b.y + MAP_DIMS.nodeH / 2}`)).toBe(true);
    expect(e.dash).toBeNull();
  });

  it("ends an edge into a cluster at the middle of the cluster's left side, dashed from a certificate", () => {
    const layout = layoutClusters(c, c.graph!, MAP_DIMS);
    const e = edgePaths(layout).find((p) => p.edge.to === 'cluster:u')!;
    const box = layout.clusters.find((k) => k.topic === 'u')!;
    expect(e.d.endsWith(` ${box.x},${box.y + box.h / 2}`)).toBe(true);
    expect(e.dash).toEqual([6, 4]);
  });

  it('cuts a long label to its length, ending on an ellipsis', () => {
    expect(cut('abcdef', 4)).toBe('abc…');
    expect(cut('abc', 4)).toBe('abc');
  });

  it("reads a lesson node's slug, and none from a subtopic", () => {
    expect(lessonSlug('lesson:intro')).toBe('intro');
    expect(lessonSlug('a')).toBeNull();
  });

  it("titles each cluster by its topic, and the module's certificate by the module", () => {
    expect(mapTitles(c).get('u')).toBe('U');
    expect(mapTitles(c).get('all')).toBe('M');
  });

  it("reads a subtopic's panel as aimed only where the focus names that subtopic", () => {
    const board = Board.build(catalog, []);
    const v = nodeView(board, c, { topic: 'u', sub: 'x' }, { course: 'm', topic: 'u', sub: 'x' });
    expect(v.aimed).toBe(true);
    expect(v.alsoNeeds).toBe('Also needs: c (t)');
    expect(v.levels[0]).toEqual({ line: expect.stringMatching(/^Foundation: /), empty: false });
    expect(nodeView(board, c, { topic: 'u', sub: 'x' }, { course: 'm', topic: 'u', sub: null }).aimed).toBe(false);
  });
});
