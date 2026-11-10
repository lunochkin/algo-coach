import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

import { bySavedOrder, moduleOrder, moved, type OrderRecord } from '@algo-coach/core/order'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'

// the fields of learn's snapshot this page reads. The queues arrive with the
// client's store, which reads the snapshot whole through `packages/core`
type Course = { slug: string; definition: { title: string }; questions: unknown[] }
type Snapshot = { courses: Course[] }

// a browser carries no stable device name: `knowledge.md`, A client's store
const DEVICE = 'web'

// until the client's store keeps a copy, the page reads the whole log once
async function load(signal: AbortSignal) {
  const [snapshot, log] = await Promise.all([
    api.GET('/api/knowledge/snapshot', { signal }),
    api.POST('/api/knowledge/sync', { body: { device: DEVICE, records: [], since: {} }, signal }),
  ])
  if (snapshot.error !== undefined || log.error !== undefined) {
    return { error: snapshot.error ?? log.error }
  }
  const orders = log.data.records.filter((one) => one.kind === 'order') as unknown as OrderRecord[]
  const courses = (snapshot.data as Snapshot).courses
  return { data: { courses, order: moduleOrder(orders), cursor: log.data.cursor } }
}

function orderLine(courses: string[]) {
  return { kind: 'order', client_id: crypto.randomUUID(), t: new Date().toISOString(), courses }
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

type Shown = { courses: Course[]; saved: string[]; cursor: Record<string, number> }

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
    const { data, error } = await api.POST('/api/knowledge/sync', {
      body: { device: DEVICE, records: [orderLine(next)], since },
    })
    if (error !== undefined) setOrder(before)
    else setSince(data.cursor)
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
