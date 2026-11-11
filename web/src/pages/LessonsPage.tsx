import { useMemo } from 'react'

import {
  lessonGroups,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonStats,
  modulesInOrder,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickPanel, PickRow } from '@/components/PickRow'
import { SectionHeading } from '@/components/SectionHeading'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { KNOWLEDGE, lessonPath } from '@/knowledge/paths'

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
                <SectionHeading
                  title={c.title}
                  count={lessonGroups(b, c).reduce((n, g) => n + g.lessons.length, 0)}
                />
                {lessonGroups(b, c).map((g) => (
                  <section key={g.key} className="space-y-stack">
                    <SectionHeading sub title={g.title} count={g.lessons.length} />
                    <PickPanel>
                      {g.lessons.map((x) => {
                        const row = lessonRow(b, c, x)
                        return (
                          <PickRow
                            key={x.slug}
                            to={lessonPath(c.slug, x.slug)}
                            title={x.title}
                            note={row.teaches}
                            stats={lessonStats(row.status, row.minutes)}
                            dim={row.state === 'locked'}
                          />
                        )
                      })}
                    </PickPanel>
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
