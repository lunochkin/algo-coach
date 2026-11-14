import { Fragment, useMemo } from 'react'

import {
  lessonSections,
  lessonRow,
  LESSONS_NONE,
  LESSONS_TITLE,
  lessonStats,
  modulesInOrder,
  BACK_KNOWLEDGE,
  OF,
} from '@climb/core'

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
  const groups = useMemo(() => lessonSections(modules ?? []), [modules])
  const sections = useSections(groups)

  return (
    <section className="space-y-section">
      <PageHeader back={{ to: KNOWLEDGE, label: BACK_KNOWLEDGE }} title={LESSONS_TITLE} />
      <Loaded of={OF.lessons} state={loadedFrom(k, modules)} blank={LESSONS_NONE}>
        {(modules) => (
          <>
            <SectionBar items={sections.items} current={sections.current} onJump={sections.jump} />
            {modules.map(({ c }) => (
              <section key={c.slug} className="space-y-stack">
                {groups
                  .filter((g) => g.c === c)
                  .map((g) => (
                    <Fragment key={g.id}>
                      {g.module && <SectionHeading title={g.module} count={g.inModule} />}
                      <PageSection
                        id={g.id}
                        sub
                        title={g.title}
                        count={g.lessons.length}
                        body="rows"
                        closed={sections.closed(g.id)}
                        onToggle={sections.toggle}
                      >
                        <PickList>
                          {g.lessons.map((x) => {
                            const row = lessonRow(g.b, g.c, x)
                            return (
                              <PickRow
                                key={x.slug}
                                to={lessonPath(g.c.slug, x.slug)}
                                title={x.title}
                                note={row.teaches}
                                stats={lessonStats(row.status, row.minutes)}
                                dim={row.state === 'locked'}
                              />
                            )
                          })}
                        </PickList>
                      </PageSection>
                    </Fragment>
                  ))}
              </section>
            ))}
          </>
        )}
      </Loaded>
    </section>
  )
}
