import { BookCheck, BookX } from 'lucide-react'
import { useEffect } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router'

import { lessonsAround, minutesOf } from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { LessonText } from '@/knowledge/LessonText'
import { LESSONS, lessonPath } from '@/knowledge/paths'

// a lesson read in one place, on both clients: `pages.md`, The knowledge pages
export function LessonPage() {
  const { module = '', lesson = '' } = useParams()
  const [params] = useSearchParams()
  const { hash } = useLocation()
  const k = useKnowledge()
  const { catalog } = useLearner()
  const c = catalog?.courses.find((x) => x.slug === module)
  const x = c?.graph?.lesson(lesson)
  const body = c?.lessonBodies[lesson] ?? ''
  const read = !!catalog?.lessonsDone?.has(`${module}:${lesson}`)
  // a lesson opened from a queue returns to it
  const back = params.get('back')

  // opened at a section: scroll to it once the text is laid out
  useEffect(() => {
    if (hash) document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [hash, body])

  const page = catalog ? { c: c ?? null, x: x ?? null } : undefined
  return (
    <Loaded of="the lesson" state={loadedFrom(k, page)} blank="This lesson is not in the current modules." blankWhen={(p) => !p.x}>
      {({ c, x }) => {
        if (!c || !x) return null
        const { next, related } = lessonsAround(c, x.slug)
        return (
          <article className="space-y-section">
            <PageHeader
              back={back ? { to: back, label: 'Back to the queue' } : { to: LESSONS, label: 'Lessons' }}
              title={x.title}
              note={`${c.title}${body ? ` · ~${minutesOf(x, body)} min` : ''}${read ? ' · read' : ''}`}
            />
            {body ? (
              <LessonText module={c.slug} text={body} />
            ) : (
              <p className="text-meta text-muted-foreground">This lesson's text is not in the snapshot yet.</p>
            )}
            {[
              ['Next', next],
              ['Related', related],
            ].map(([title, items]) =>
              (items as typeof next).length ? (
                <section key={title as string} className="space-y-1">
                  <h2 className="text-meta font-medium text-brand-deep">{title as string}</h2>
                  <p className="flex flex-wrap gap-x-4">
                    {(items as typeof next).map((y) => (
                      <Link key={y.slug} to={lessonPath(c.slug, y.slug)} className="underline underline-offset-2">
                        {y.title}
                      </Link>
                    ))}
                  </p>
                </section>
              ) : null,
            )}
            <div>
              {read ? (
                <Button variant="outline" onClick={() => void k.add('lesson', { course: c.slug, lesson: x.slug, status: 'undone' })}>
                  <BookX />
                  Mark unread
                </Button>
              ) : (
                <Button onClick={() => void k.add('lesson', { course: c.slug, lesson: x.slug, status: 'done' })}>
                  <BookCheck />
                  Mark read
                </Button>
              )}
            </div>
          </article>
        )
      }}
    </Loaded>
  )
}
