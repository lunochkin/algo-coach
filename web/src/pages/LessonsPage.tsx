import { useMemo } from 'react'
import { Link } from 'react-router'

import {
  lessonGroups,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonRowLine,
  modulesInOrder,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { KNOWLEDGE, lessonPath } from '@/knowledge/paths'
import { cn } from '@/lib/utils'

// every module's lessons, by module and in graph order: `pages.md`, The
// knowledge pages. A locked lesson opens too, since reading early skips nothing
export function LessonsPage() {
  const k = useKnowledge()
  const { catalog, board, order } = useLearner()

  const modules = useMemo(() => {
    if (!catalog || !board(null)) return undefined
    return modulesInOrder(catalog.courses, order, board, (c) => !!c.graph?.lessons.length)
  }, [catalog, board, order])

  return (
    <section className="space-y-section">
      <PageHeader back={{ to: KNOWLEDGE, label: 'Knowledge' }} title={LESSONS_TITLE} />
      <Loaded of="the lessons" state={loadedFrom(k, modules)} blank={LESSONS_NONE}>
        {(modules) => (
          <>
            {modules.map(({ c, b }) => (
              <section key={c.slug} className="space-y-stack">
                <h2 className="text-heading font-medium">{c.title}</h2>
                {lessonGroups(b, c).map((g) => (
                  <section key={g.key} className="space-y-stack">
                    <SectionHeading title={g.title} count={g.lessons.length} />
                    <ul className="divide-y rounded-xl border bg-card">
                      {g.lessons.map((x) => {
                        const row = lessonRow(b, c, x)
                        return (
                          <li key={x.slug}>
                            <Link
                              to={lessonPath(c.slug, x.slug)}
                              className={cn(
                                'block space-y-0.5 px-4 py-3 hover:bg-muted/50',
                                row.state === 'locked' && 'opacity-70',
                              )}
                            >
                              <p className="font-medium">{x.title}</p>
                              <p className="text-meta text-muted-foreground">
                                {lessonRowLine(row.minutes, row.teaches)}
                              </p>
                              <p
                                className={cn(
                                  'text-meta',
                                  row.state === 'available'
                                    ? 'text-brand-deep'
                                    : 'text-muted-foreground',
                                )}
                              >
                                {row.status}
                              </p>
                            </Link>
                          </li>
                        )
                      })}
                    </ul>
                  </section>
                ))}
              </section>
            ))}
          </>
        )}
      </Loaded>
    </section>
  )
}
