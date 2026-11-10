import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

import { bySavedOrder, moduleOrder, moved, type OrderRecord } from '@algo-coach/core/order'

import { api } from '@/api/client'
import { linesOf, readLog, sendLines, type Cursor } from '@/api/log'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'

// the fields of learn's snapshot this page reads. The queues arrive with the
// client's store, which reads the snapshot whole through `packages/core`
type Course = { slug: string; definition: { title: string }; questions: unknown[] }
type Snapshot = { courses: Course[] }

async function load(signal: AbortSignal) {
  const [snapshot, log] = await Promise.all([
    api.GET('/api/knowledge/snapshot', { signal }),
    readLog(signal),
  ])
  if (snapshot.data === undefined || log.data === undefined) {
    return { error: snapshot.error ?? log.error }
  }
  const order = moduleOrder(linesOf<OrderRecord>(log.data.records, 'order'))
  const courses = (snapshot.data as Snapshot).courses
  return { data: { courses, order, cursor: log.data.cursor } }
}

export function KnowledgePage() {
  const loaded = useLoaded(load, 'knowledge')

  return (
    <section className="space-y-section">
      <PageHeader title="Knowledge" note="Answer the questions due, then the new ones." />
      <Loaded
        of="the modules"
        state={loaded}
        blank="No module is seeded yet."
        blankWhen={(one) => one.courses.length === 0}
      >
        {({ courses, order, cursor }) => <Modules courses={courses} saved={order} cursor={cursor} />}
      </Loaded>
    </section>
  )
}

type Shown = { courses: Course[]; saved: string[]; cursor: Cursor }

function Modules({ courses, saved, cursor }: Shown) {
  const [order, setOrder] = useState(saved)
  // the reply then carries only what was written since the page loaded
  const [since, setSince] = useState(cursor)
  const rows = bySavedOrder(courses, (course) => course.slug, order)

  async function move(from: number, to: number) {
    const before = order
    const next = moved(
      rows.map((course) => course.slug),
      from,
      to,
    )
    setOrder(next)
    const cursor = await sendLines([{ kind: 'order', courses: next }], since)
    if (cursor === null) setOrder(before)
    else setSince(cursor)
  }

  return (
    <section className="space-y-stack">
      <SectionHeading title="Modules" count={courses.length} />
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
                onClick={() => void move(i, i - 1)}
              >
                <ChevronUp />
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label={`Move ${course.definition.title} down`}
                disabled={i === rows.length - 1}
                onClick={() => void move(i, i + 1)}
              >
                <ChevronDown />
              </Button>
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
