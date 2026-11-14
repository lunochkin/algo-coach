import { Plus, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router'

import {
  lessonStopNote,
  queueLine,
  queueSummary,
  queueTitle,
  questionHead,
  queueStart,
  type QueueMode,
  type AttemptRecord,
  type Catalog,
  type DrillScope,
  type LessonItem,
  QueueRun,
  type QueueSource,
  type Result,
  ASK_NEXT,
  LESSON_STOP_LATER,
  LESSON_STOP_READ,
  QUEUE_ANSWERED,
  QUEUE_DONE,
  QUEUE_RAISE,
  QUEUE_STOP,
  queueLeft,
  OF,
  lessonStopKicker,
  lessonRead,
} from '@climb/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Ask } from '@/knowledge/Ask'
import { linesOf, loadedFrom, useKnowledge } from '@/knowledge/context'
import { filteredScope } from '@/knowledge/filtered'
import { useLearner } from '@/knowledge/learner'
import { LessonOver, type Reading } from '@/knowledge/LessonOver'

// learn's names, which a stint stores: the filtered queue is `drill` on the wire

const HOME = '/knowledge'

// the query names the queue, and a reload starts one of the same mode again:
// `pages.md`, The knowledge pages
export function QueuePage() {
  const [params] = useSearchParams()
  const named = params.get('mode')
  const mode: QueueMode = named === 'review' ? 'review' : named === 'filtered' ? 'drill' : 'next'
  const learner = useLearner()
  const k = useKnowledge()
  if (!learner.ready || !learner.catalog)
    return (
      <section className="space-y-section">
        <PageHeader title={queueTitle(mode)} />
        <Loaded of={OF.queue} state={loadedFrom(k, undefined)}>
          {() => null}
        </Loaded>
      </section>
    )
  const scope = mode === 'drill' ? filteredScope(params, learner.catalog) : null
  // a module the user no longer reads leaves nothing to filter
  if (mode === 'drill' && !scope) return <Navigate to={HOME} replace />
  return (
    <Running
      key={params.toString()}
      mode={mode}
      scope={scope}
      catalog={learner.catalog}
      learner={learner}
    />
  )
}

type Learner = ReturnType<typeof useLearner>

type RunningProps = {
  mode: QueueMode
  scope: DrillScope | null
  catalog: Catalog
  learner: Learner
}

function Running({ mode, scope, catalog, learner }: RunningProps) {
  const k = useKnowledge()
  const navigate = useNavigate()
  const held = (): QueueSource => ({
    catalog,
    attempts: linesOf<AttemptRecord>(k.records, 'attempt'),
  })
  // fixed when the queue starts: a raise moves its limit, and the picks read the log as it grows
  const [run] = useState(() => {
    const start = queueStart(mode, scope, learner)
    return start && new QueueRun(start.queue, mode, start.course, start.include, held())
  })
  const [, rerender] = useState(0)
  // a lesson read over the queue: the stop's and an answer's lesson links open it
  const [lessonOpen, setLessonOpen] = useState<Reading>(null)
  const changed = () => rerender((n) => n + 1)

  // leaving through the navigation stores the stint too. The cleanup reads
  // the latest `add`, which changes with every record the copy takes
  const store = useRef(k)
  useEffect(() => {
    store.current = k
  })
  useEffect(
    () => () => {
      const stint = run?.end()
      if (stint) void store.current.add('session', stint)
    },
    [run],
  )

  function end() {
    const stint = run?.end()
    if (stint) void k.add('session', stint)
  }

  function onAnswered(r: Result) {
    if (!run) return
    void k.add('attempt', run.answer(r))
    changed()
  }

  function next() {
    run?.next(held())
    if (run?.done) end()
    changed()
  }

  function stop() {
    run?.stop()
    end()
    changed()
  }

  function moreNew() {
    if (!run) return
    // today's limit, so the home and the next queue count the raise too
    void k.add('raise', run.raise(held()))
    changed()
  }

  const reading = run?.reading(held(), learner.now)
  const left = reading?.left ?? queueLine({ reviews: 0, learning: 0, newLeft: 0 })
  const current = run?.current ?? null
  const done = run?.done ?? true
  const results = run?.results ?? []
  const score = run?.score ?? 0
  const course =
    current && 'q' in current ? catalog.courses.find((c) => c.slug === current.q.course) : undefined

  return (
    <section className="space-y-section">
      <PageHeader
        title={done ? QUEUE_DONE : queueTitle(mode)}
        aside={
          <>
            <span className="text-meta tabular-nums">
              {score}/{results.length}
            </span>
            {!done && (
              <Button variant="outline" size="sm" onClick={stop}>
                <X />
                {QUEUE_STOP}
              </Button>
            )}
          </>
        }
      />
      <div className="flex flex-wrap items-center gap-stack text-meta text-muted-foreground">
        <span className="flex-1">{left}</span>
        {/* an ended queue offers it too: the raise starts the queue again, as on the phone */}
        {reading?.raise && (
          <Button variant="outline" size="sm" onClick={moreNew}>
            <Plus />
            {QUEUE_RAISE}
          </Button>
        )}
      </div>

      {!done && current && 'lesson' in current ? (
        <LessonStop
          item={current.lesson}
          read={lessonRead(catalog, current.lesson.course.slug, current.lesson.lesson.slug)}
          onRead={() =>
            setLessonOpen({ course: current.lesson.course.slug, slug: current.lesson.lesson.slug })
          }
          onNext={next}
        />
      ) : !done && current && 'q' in current ? (
        <Ask
          key={run?.shown}
          q={current.q}
          course={course}
          head={questionHead(course, catalog.rules, current.q, current.tag, current.early)}
          onAnswered={onAnswered}
          onNext={next}
          onLesson={(course, slug, anchor) => setLessonOpen({ course, slug, anchor })}
        />
      ) : (
        <Summary
          {...(reading?.summary ?? { answered: 0, correct: 0, introduced: 0, stopped: false })}
          left={left}
          // the way back is the page the queue came from: a filtered queue's module
          onDone={() => navigate(scope ? `/knowledge/modules/${scope.course}` : HOME)}
        />
      )}
      <LessonOver reading={lessonOpen} onRead={setLessonOpen} />
    </section>
  )
}

function Summary(props: {
  answered: number
  correct: number
  introduced: number
  stopped: boolean
  left: string
  onDone: () => void
}) {
  const summary = queueSummary(props)
  return (
    <Panel>
      <p className="text-heading font-medium">{summary.title}</p>
      <p>
        <span className="text-title tabular-nums">{props.answered}</span> {QUEUE_ANSWERED}
      </p>
      <p>{summary.line}</p>
      <p className="text-meta text-muted-foreground">{queueLeft(props.left)}</p>
      <div>
        <Button onClick={props.onDone}>{QUEUE_DONE}</Button>
      </div>
    </Panel>
  )
}

// a lesson the queue offers is a stop: its title, why it is offered, and Read
// opening the lesson page, whose way back returns here. `pages.md`, The
// knowledge pages
function LessonStop(props: {
  item: LessonItem
  read: boolean
  onRead: () => void
  onNext: () => void
}) {
  const { item, read, onRead, onNext } = props
  return (
    <Panel>
      <p className="text-meta font-medium text-muted-foreground">
        {lessonStopKicker(item.course, item.lesson)}
      </p>
      <p className="text-heading font-medium">{item.lesson.title}</p>
      <p className="text-meta text-muted-foreground">{lessonStopNote(read)}</p>
      <div className="flex gap-stack">
        {read ? (
          <Button onClick={onNext}>{ASK_NEXT}</Button>
        ) : (
          <>
            <Button onClick={onRead}>{LESSON_STOP_READ}</Button>
            <Button variant="ghost" onClick={onNext}>
              {LESSON_STOP_LATER}
            </Button>
          </>
        )}
      </div>
    </Panel>
  )
}
