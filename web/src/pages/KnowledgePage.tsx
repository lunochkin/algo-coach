import { ChevronDown, ChevronUp } from 'lucide-react'

import { bySavedOrder, moduleOrder, moved, type OrderRecord } from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'
import { linesOf, loadedFrom, useKnowledge } from '@/knowledge/context'

// the fields of learn's snapshot this page reads. The queues read the snapshot
// whole through `packages/core`
type Course = { slug: string; definition: { title: string }; questions: unknown[] }
type Snapshot = { courses: Course[] }

export function KnowledgePage() {
  const k = useKnowledge()
  const courses = (k.snapshot as Snapshot | null)?.courses
  const order = moduleOrder(linesOf<OrderRecord>(k.records, 'order'))
  const rows = courses && bySavedOrder(courses, (course) => course.slug, order)

  function move(from: number, to: number) {
    if (!rows) return
    const courses = moved(
      rows.map((course) => course.slug),
      from,
      to,
    )
    void k.add('order', { courses })
  }

  return (
    <section className="space-y-section">
      <PageHeader title="Knowledge" note="Answer the questions due, then the new ones." />
      <Loaded of="the modules" state={loadedFrom(k, rows)} blank="No module is seeded yet.">
        {(rows) => (
          <section className="space-y-stack">
            <SectionHeading title="Modules" count={rows.length} />
            <ul className="divide-y rounded-xl border bg-card">
              {rows.map((course, i) => (
                <li key={course.slug} className="flex items-center gap-4 px-4 py-3">
                  <span className="flex-1">{course.definition.title}</span>
                  <span className="text-meta text-muted-foreground tabular-nums">
                    {course.questions.length} questions
                  </span>
                  <span className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Move ${course.definition.title} up`}
                      disabled={i === 0}
                      onClick={() => move(i, i - 1)}
                    >
                      <ChevronUp />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Move ${course.definition.title} down`}
                      disabled={i === rows.length - 1}
                      onClick={() => move(i, i + 1)}
                    >
                      <ChevronDown />
                    </Button>
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </Loaded>
    </section>
  )
}
