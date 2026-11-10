import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'

// the fields of learn's snapshot this page reads. The queues arrive with the
// client's store, which reads the snapshot whole through `packages/core`
type Snapshot = { courses: { slug: string; definition: { title: string }; questions: unknown[] }[] }

export function KnowledgePage() {
  const snapshot = useLoaded(
    (signal) =>
      api
        .GET('/api/knowledge/snapshot', { signal })
        .then(({ data, error }) => ({ data: data as Snapshot | undefined, error })),
    'knowledge',
  )

  return (
    <section className="space-y-section">
      <PageHeader title="Knowledge" note="Answer the questions due, then the new ones." />
      <Loaded
        of="the modules"
        state={snapshot}
        blank="No module is seeded yet."
        blankWhen={(one) => one.courses.length === 0}
      >
        {({ courses }) => (
          <section className="space-y-stack">
            <SectionHeading title="Modules" count={courses.length} />
            <ul className="divide-y rounded-xl border bg-card">
              {courses.map((course) => (
                <li key={course.slug} className="flex items-baseline gap-4 px-4 py-3">
                  <span className="flex-1">{course.definition.title}</span>
                  <span className="text-meta text-muted-foreground tabular-nums">
                    {course.questions.length} questions
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
