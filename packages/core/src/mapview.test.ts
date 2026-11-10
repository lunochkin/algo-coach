import { describe, expect, it } from 'vitest';

import { alsoNeeds, Board, layoutClusters, levelDots, loadSnapshot, MAP_DIMS, mapLit, reach } from './index';

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
});
