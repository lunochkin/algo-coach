import { ChevronDown, ChevronUp } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router'

import {
  bySavedOrder,
  CERTIFICATIONS_LINK,
  LESSONS_LINK,
  MODULES_HEADING,
  type ModuleRow as ModuleRowView,
  moduleRows,
  MODULES_OF,
  moved,
  NO_MODULES,
  readyCert,
  readyLesson,
  syncErrorSummary,
  newRecord,
  SECTION_KNOWLEDGE,
  KNOWLEDGE_NOTE,
  moveUp,
  moveDown,
} from '@algo-coach/core'

import { ErrorLine } from '@/components/ErrorLine'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { PickPanel, PickRow } from '@/components/PickRow'
import { KnowledgeNext } from '@/knowledge/KnowledgeNext'
import { ModuleRow } from '@/knowledge/ModuleRow'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { CERTIFICATIONS, LESSONS, lessonPath } from '@/knowledge/paths'

export function KnowledgePage() {
  const k = useKnowledge()
  const { catalog, board, order, certExams, now } = useLearner()

  const home = useMemo(() => {
    const all = board(null)
    if (!catalog || !all) return undefined
    return {
      rows: bySavedOrder(moduleRows(all, now), (row) => row.c.slug, order),
      toRead: readyLesson(all, order),
      toTake: readyCert(all, order, certExams),
    }
  }, [catalog, board, order, certExams, now])

  function move(rows: ModuleRowView[], from: number, to: number) {
    const slugs = rows.map((row) => row.c.slug)
    void k.add('order', newRecord.order(moved(slugs, from, to)))
  }

  return (
    <section className="space-y-section">
      <PageHeader title={SECTION_KNOWLEDGE} note={KNOWLEDGE_NOTE} />
      {/* a failed sync changes what the next queue serves, so the home says so */}
      {k.sync.error && !k.sync.running && (
        <ErrorLine title={k.sync.error}>{syncErrorSummary(k.sync.error)}</ErrorLine>
      )}
      {/* the lessons are a step down from the home: `pages.md`, The structure */}
      <p className="flex gap-4 text-meta">
        <Link to={LESSONS} className="font-medium underline-offset-4 hover:underline">
          {LESSONS_LINK}
        </Link>
        <Link to={CERTIFICATIONS} className="font-medium underline-offset-4 hover:underline">
          {CERTIFICATIONS_LINK}
        </Link>
      </p>
      <Loaded
        of={MODULES_OF}
        state={loadedFrom(k, home)}
        blank={NO_MODULES}
        blankWhen={(h) => h.rows.length === 0}
      >
        {({ rows, toRead, toTake }) => (
          <>
            {/* the next steps the rules would take, for a reader who never opens
                the lessons or the certifications: rows, since each opens a page */}
            {(toTake || toRead) && (
              <PickPanel>
                {toTake && (
                  <PickRow
                    to={`${CERTIFICATIONS}?${new URLSearchParams({ open: toTake.id })}`}
                    title={toTake.line}
                    stats={[]}
                  />
                )}
                {toRead && (
                  <PickRow
                    to={lessonPath(toRead.c.slug, toRead.lesson.slug)}
                    title={toRead.line}
                    stats={[]}
                  />
                )}
              </PickPanel>
            )}
            <KnowledgeNext controls />

            <section className="space-y-stack">
              <SectionHeading title={MODULES_HEADING} count={rows.length} />
              <PickPanel>
                {rows.map((row, i) => (
                  <ModuleRow
                    key={row.c.slug}
                    row={row}
                    aside={
                      <>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={moveUp(row.c.title)}
                          disabled={i === 0}
                          onClick={() => move(rows, i, i - 1)}
                        >
                          <ChevronUp />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={moveDown(row.c.title)}
                          disabled={i === rows.length - 1}
                          onClick={() => move(rows, i, i + 1)}
                        >
                          <ChevronDown />
                        </Button>
                      </>
                    }
                  />
                ))}
              </PickPanel>
            </section>
          </>
        )}
      </Loaded>
    </section>
  )
}
