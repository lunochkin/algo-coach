import { levels, type Catalog, type DrillScope } from '@algo-coach/core'

// a filtered queue's choices, carried in its URL: `pages.md`, The knowledge pages

export function filteredQuery(scope: DrillScope): string {
  const q = new URLSearchParams({ mode: 'filtered', module: scope.course })
  if (scope.topic) q.set('topic', scope.topic)
  if (scope.sub) q.set('sub', scope.sub)
  if (scope.level != null) q.set('level', String(scope.level))
  if (scope.kind) q.set('kind', scope.kind)
  if (scope.due) q.set('due', '1')
  return `/knowledge/queue?${q}`
}

/**
 * The choices a URL carries, degraded as a focus is: an unknown topic keeps
 * the module, an unknown subtopic keeps the topic. Null where the module is
 * not one the user reads.
 */
export function filteredScope(q: URLSearchParams, catalog: Catalog): DrillScope | null {
  const c = catalog.courses.find((x) => x.slug === q.get('module'))
  if (!c) return null
  const t = c.topics.find((x) => x.slug === q.get('topic'))
  const sub = t && t.subs.includes(q.get('sub') ?? '') ? q.get('sub') : null
  const level = Number(q.get('level'))
  const known = q.get('level') !== null && Number.isInteger(level) && levels(catalog.rules).includes(level)
  const kind = q.get('kind')
  return {
    course: c.slug,
    topic: t?.slug ?? null,
    sub,
    level: known ? level : null,
    kind: kind && c.kinds.includes(kind) ? kind : null,
    due: q.get('due') === '1',
  }
}
