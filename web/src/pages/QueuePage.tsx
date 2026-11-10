import { X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router'

import {
  Board,
  continuePlan,
  drillQueue,
  isLessonItem,
  lessonStopNote,
  makeAttempt,
  NEW_STEP,
  offersRaise,
  queueLine,
  queueSummary,
  queueTitle,
  questionHead,
  reviewQueue,
  type AttemptRecord,
  type Catalog,
  type DrillScope,
  type LessonItem,
  type Queue,
  type Question,
  type Result,
  type Status,
  ASK_NEXT,
  LESSON_STOP_KICKER,
  LESSON_STOP_LATER,
  LESSON_STOP_READ,
  QUEUE_ANSWERED,
  QUEUE_DONE,
  QUEUE_RAISE,
  QUEUE_STOP,
  queueLeft,
  isoNow,
} from '@algo-coach/core'

import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Ask } from '@/knowledge/Ask'
import { linesOf, useKnowledge } from '@/knowledge/context'
import { filteredScope } from '@/knowledge/filtered'
import { useLearner } from '@/knowledge/learner'
import { lessonPath } from '@/knowledge/paths'

// learn's names, which a stint stores: the filtered queue is `drill` on the wire
type Mode = 'next' | 'review' | 'drill'
type Current = { q: Question; tag: Status; fresh: boolean; early: boolean } | { lesson: LessonItem }

const HOME = '/knowledge'

// the query names the queue, and a reload starts one of the same mode again:
// `pages.md`, The knowledge pages
export function QueuePage() {
  const [params] = useSearchParams()
  const named = params.get('mode')
  const mode: Mode = named === 'review' ? 'review' : named === 'filtered' ? 'drill' : 'next'
  const learner = useLearner()
  if (!learner.ready || !learner.catalog)
    return <p className="text-meta text-muted-foreground">Loading the queue…</p>
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
  mode: Mode
  scope: DrillScope | null
  catalog: Catalog
  learner: Learner
}

function Running({ mode, scope, catalog, learner }: RunningProps) {
  const k = useKnowledge()
  const navigate = useNavigate()
  // fixed when the queue starts: a raise moves its limit, and the picks read the log as it grows
  const [start] = useState(() => {
    if (scope) {
      // named explicitly, so a paused module serves too
      const b = learner.board(scope.course)
      return b
        ? {
            queue: drillQueue(b, scope, learner.newLimit),
            course: scope.course,
            include: null,
          }
        : null
    }
    if (mode === 'review') {
      const all = learner.board(null)
      return all
        ? {
            queue: reviewQueue(all, ['weak', 'due']),
            course: null,
            include: null,
          }
        : null
    }
    const plan = continuePlan(learner.board, learner.focus, null, learner.newLimit)
    return plan && { queue: plan.queue, course: plan.course, include: plan.include }
  })
  const queue: Queue | null = start?.queue ?? null

  // the answers of this queue, so a pick never waits for the copy to catch up
  const [mine, setMine] = useState<AttemptRecord[]>([])
  const board = useCallback((): Board | null => {
    if (!start) return null
    const held = linesOf<AttemptRecord>(k.records, 'attempt')
    const known = new Set(held.map((a) => `${a.t}|${a.course}|${a.id}`))
    const extra = mine.filter((a) => !known.has(`${a.t}|${a.course}|${a.id}`))
    return Board.build(catalog, [...held, ...extra], start.course, start.include)
  }, [catalog, k.records, start, mine])

  const pickOne = useCallback((): Current | null => {
    const b = board()
    const now = Date.now()
    const picked = b && queue ? queue.pick(b, now) : null
    if (!picked || !b || !queue) return null
    if (isLessonItem(picked)) return { lesson: picked }
    return {
      q: picked,
      tag: b.status(picked, now),
      fresh: !b.attempts(picked).length,
      early: queue.early(b, picked, now),
    }
  }, [board, queue])

  const [current, setCurrent] = useState<Current | null>(() => pickOne())
  const [shown, setShown] = useState(0) // keys Ask, so each pick starts clean
  const [results, setResults] = useState<Result[]>([])
  const [introduced, setIntroduced] = useState(0)
  const [done, setDone] = useState(!current)
  const ended = useRef(false)
  const answered = useRef<Result[]>([])

  // stopping stores the stint; a queue with no answer stores none
  const end = useCallback(() => {
    if (ended.current) return
    ended.current = true
    const rs = answered.current
    if (rs.length)
      void k.add('session', {
        mode,
        score: rs.filter((r) => r.correct).length,
        n: rs.length,
      })
  }, [k, mode])

  // leaving through the navigation stops the queue the same way. The effect
  // runs at mount and unmount alone: `end` changes with every record the copy
  // takes, and a cleanup run on each change stored a stint per record. The
  // mount reopens the queue, since a development build mounts twice
  const leave = useRef(end)
  useEffect(() => {
    leave.current = end
  })
  useEffect(() => {
    ended.current = false
    return () => leave.current()
  }, [])

  function onAnswered(r: Result) {
    const rec = makeAttempt(isoNow(), r.q.course, r.q.id, r.correct, r.guess, r.grade, r.card)
    setMine((xs) => [...xs, rec])
    void k.add('attempt', { ...rec })
    answered.current = [...answered.current, r]
    setResults(answered.current)
    if (current && 'q' in current && current.fresh) setIntroduced((n) => n + 1)
  }

  function next() {
    const p = pickOne()
    setCurrent(p)
    setShown((n) => n + 1)
    if (!p) {
      end()
      setDone(true)
    }
  }

  function stop() {
    end()
    setDone(true)
  }

  function moreNew() {
    if (!queue) return
    queue.raise(NEW_STEP)
    // today's limit, so the home and the next queue count the raise too
    void k.add('raise', { n: NEW_STEP })
    if (!current) {
      const p = pickOne()
      if (p) {
        ended.current = false
        setDone(false)
        setCurrent(p)
        setShown((n) => n + 1)
      }
    }
  }

  const b = board()
  const now = learner.now
  const counts =
    b && queue
      ? {
          reviews: queue.reviews(b, now).length,
          learning: queue.stepping(b, now).count,
          newLeft: queue.newLeft(b, now),
        }
      : { reviews: 0, learning: 0, newLeft: 0 }
  const unseenLeft = !!b && !!queue && queue.scope.some((q) => !b.attempts(q).length)
  const score = results.filter((r) => r.correct).length
  const course =
    current && 'q' in current ? catalog.courses.find((c) => c.slug === current.q.course) : undefined

  return (
    <section className="space-y-section">
      <header className="flex items-center gap-stack">
        <h1 className="flex-1 text-title font-semibold">{done ? QUEUE_DONE : queueTitle(mode)}</h1>
        <span className="text-meta tabular-nums">
          {score}/{results.length}
        </span>
        {!done && (
          <Button variant="outline" size="sm" onClick={stop}>
            <X />
            {QUEUE_STOP}
          </Button>
        )}
      </header>
      <div className="flex flex-wrap items-center gap-stack text-meta text-muted-foreground">
        <span className="flex-1">{queueLine(counts)}</span>
        {/* an ended queue offers it too: the raise starts the queue again, as on the phone */}
        {offersRaise(mode, counts.newLeft, unseenLeft) && (
          <Button variant="ghost" size="sm" onClick={moreNew}>
            {QUEUE_RAISE}
          </Button>
        )}
      </div>

      {!done && current && 'lesson' in current ? (
        <LessonStop
          item={current.lesson}
          read={
            !!catalog.lessonsDone?.has(
              `${current.lesson.course.slug}:${current.lesson.lesson.slug}`,
            )
          }
          onNext={next}
        />
      ) : !done && current && 'q' in current ? (
        <Ask
          key={shown}
          q={current.q}
          course={course}
          head={questionHead(course, catalog.rules, current.q, current.tag, current.early)}
          onAnswered={onAnswered}
          onNext={next}
        />
      ) : (
        <Summary
          answered={results.length}
          correct={score}
          introduced={introduced}
          stopped={!!current}
          left={queueLine(counts)}
          // the way back is the page the queue came from: a filtered queue's module
          onDone={() => navigate(scope ? `/knowledge/modules/${scope.course}` : HOME)}
        />
      )}
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
function LessonStop(props: { item: LessonItem; read: boolean; onNext: () => void }) {
  const { item, read, onNext } = props
  const { pathname, search } = useLocation()
  return (
    <Panel>
      <p className="text-meta text-brand-deep">{LESSON_STOP_KICKER}</p>
      <p className="text-heading font-medium">{item.lesson.title}</p>
      <p className="text-meta text-muted-foreground">{lessonStopNote(read)}</p>
      <div className="flex gap-stack">
        {read ? (
          <Button onClick={onNext}>{ASK_NEXT}</Button>
        ) : (
          <>
            <Button asChild>
              <Link to={lessonPath(item.course.slug, item.lesson.slug, '', `${pathname}${search}`)}>
                {LESSON_STOP_READ}
              </Link>
            </Button>
            <Button variant="ghost" onClick={onNext}>
              {LESSON_STOP_LATER}
            </Button>
          </>
        )}
      </div>
    </Panel>
  )
}
