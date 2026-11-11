import { useMemo } from 'react'

import {
  lessonGroups,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonStats,
  modulesInOrder,
  BACK_KNOWLEDGE,
  OF,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PageSection } from '@/components/PageSection'
import { PickList, PickRow } from '@/components/PickRow'
import { SectionBar } from '@/components/SectionBar'
import { SectionHeading } from '@/components/SectionHeading'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { KNOWLEDGE, lessonPath } from '@/knowledge/paths'
import { useSections } from '@/lib/sections'

// every module's lessons, by module and in graph order: `pages.md`, The
// knowledge pages. A locked lesson opens too, since reading early skips nothing
export function LessonsPage() {
  const k = useKnowledge()
  const { catalog, board, order } = useLearner()

  const modules = useMemo(() => {
    if (!catalog || !board(null)) return undefined
    return modulesInOrder(catalog.courses, order, board, (c) => !!c.graph?.lessons.length)
  }, [catalog, board, order])
  // a group of one module's lessons is a section: the bar names the module
  // beside it only where several modules hold lessons
  const sections = useSections(
    (modules ?? []).flatMap(({ c, b }) =>
      lessonGroups(b, c).map((g) => ({
        id: `${c.slug}-${g.key}`,
        label: (modules ?? []).length > 1 ? `${c.title} · ${g.title}` : g.title,
      })),
    ),
  )

  return (
    <section className="space-y-section">
      <PageHeader back={{ to: KNOWLEDGE, label: BACK_KNOWLEDGE }} title={LESSONS_TITLE} />
      <Loaded of={OF.lessons} state={loadedFrom(k, modules)} blank={LESSONS_NONE}>
        {(modules) => (
          <>
            <SectionBar items={sections.items} current={sections.current} onJump={sections.jump} />
            {modules.map(({ c, b }) => (
              <section key={c.slug} className="space-y-stack">
                <SectionHeading
                  title={c.title}
                  count={lessonGroups(b, c).reduce((n, g) => n + g.lessons.length, 0)}
                />
                {lessonGroups(b, c).map((g) => (
                  <PageSection
                    key={g.key}
                    id={`${c.slug}-${g.key}`}
                    sub
                    title={g.title}
                    count={g.lessons.length}
                    body="rows"
                    closed={sections.closed(`${c.slug}-${g.key}`)}
                    onToggle={sections.toggle}
                  >
                    <PickList>
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
                    </PickList>
                  </PageSection>
                ))}
              </section>
            ))}
          </>
        )}
      </Loaded>
    </section>
  )
}
