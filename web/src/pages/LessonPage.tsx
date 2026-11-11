import { BookCheck, BookX } from 'lucide-react'
import { useEffect } from 'react'
import { Link, useLocation, useParams } from 'react-router'

import {
  lessonsAround,
  minutesOf,
  LESSON_MARK_READ,
  LESSON_MARK_UNREAD,
  LESSON_MISSING,
  LESSON_NEXT,
  LESSON_NO_TEXT,
  LESSON_RELATED,
  lessonNote,
  newRecord,
  type Course,
  type Lesson,
} from '@algo-coach/core'

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
  const { hash } = useLocation()
  const k = useKnowledge()
  const { catalog } = useLearner()
  const c = catalog?.courses.find((x) => x.slug === module)
  const x = c?.graph?.lesson(lesson)
  const body = c?.lessonBodies[lesson] ?? ''
  const read = !!catalog?.lessonsDone?.has(`${module}:${lesson}`)

  // opened at a section: scroll to it once the text is laid out
  useEffect(() => {
    if (hash) document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [hash, body])

  const page = catalog ? { c: c ?? null, x: x ?? null } : undefined
  return (
    <Loaded
      of="the lesson"
      state={loadedFrom(k, page)}
      blank={LESSON_MISSING}
      blankWhen={(p) => !p.x}
    >
      {({ c, x }) => {
        if (!c || !x) return null
        return (
          <article className="space-y-section">
            <PageHeader
              back={{ to: LESSONS, label: 'Lessons' }}
              title={x.title}
              note={lessonNote(c.title, body ? minutesOf(x, body) : null, read)}
            />
            <LessonBody c={c} x={x} body={body} read={read} />
          </article>
        )
      }}
    </Loaded>
  )
}

// the lesson itself, read on its page and over a running queue alike: its text,
// the lessons around it and Mark read. `onLesson` keeps a linked lesson in place
export function LessonBody(props: {
  c: Course
  x: Lesson
  body: string
  read: boolean
  onLesson?: (slug: string) => void
}) {
  const { c, x, body, read, onLesson } = props
  const k = useKnowledge()
  const { next, related } = lessonsAround(c, x.slug)
  return (
    <>
      {body ? (
        <LessonText module={c.slug} text={body} onLesson={onLesson} />
      ) : (
        <p className="text-meta text-muted-foreground">{LESSON_NO_TEXT}</p>
      )}
      {[
        [LESSON_NEXT, next],
        [LESSON_RELATED, related],
      ].map(([title, items]) =>
        (items as typeof next).length ? (
          <section key={title as string} className="space-y-1">
            <h2 className="text-meta font-medium text-brand-deep">{title as string}</h2>
            <p className="flex flex-wrap gap-x-4">
              {(items as typeof next).map((y) =>
                onLesson ? (
                  <button
                    key={y.slug}
                    type="button"
                    onClick={() => onLesson(y.slug)}
                    className="underline underline-offset-2"
                  >
                    {y.title}
                  </button>
                ) : (
                  <Link
                    key={y.slug}
                    to={lessonPath(c.slug, y.slug)}
                    className="underline underline-offset-2"
                  >
                    {y.title}
                  </Link>
                ),
              )}
            </p>
          </section>
        ) : null,
      )}
      <div>
        {read ? (
          <Button
            variant="outline"
            onClick={() => void k.add('lesson', newRecord.lesson(c.slug, x.slug, 'undone'))}
          >
            <BookX />
            {LESSON_MARK_UNREAD}
          </Button>
        ) : (
          <Button onClick={() => void k.add('lesson', newRecord.lesson(c.slug, x.slug, 'done'))}>
            <BookCheck />
            {LESSON_MARK_READ}
          </Button>
        )}
      </div>
    </>
  )
}
