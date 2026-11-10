import { ChevronDown, ChevronUp, Plus, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import {
  bySavedOrder,
  CERTIFICATIONS_LINK,
  CLEAR_FOCUS,
  CONTINUE,
  continueCounts,
  continueLine,
  continuePlan,
  DUE_NOW,
  emptyContinue,
  type EmptyContinue,
  EXAM_LINK,
  type Focus,
  FOCUS_CERT,
  FOCUS_NEXT,
  focusLabel,
  type FocusPart,
  focusTitle,
  focusView,
  LEARNING,
  LESSONS_LINK,
  moduleCounts,
  type ModuleRow,
  moduleRows,
  MODULES_OF,
  moved,
  NEW_LEFT,
  NO_MODULES,
  PAUSED,
  RAISE_TODAY,
  readyCert,
  readyLesson,
  STRICT,
  strictLabel,
  waitingOutside,
  syncErrorSummary,
  newRecord,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'
import { Toggle } from '@/components/ui/toggle'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { CERTIFICATIONS, EXAM, LESSONS, lessonPath } from '@/knowledge/paths'

// the focus bar reads in the flame, as progress does, from what is held to
// what is not yet met
const PART_TONE: Record<FocusPart, string> = {
  mastered: 'bg-brand',
  learning: 'bg-brand/60',
  review: 'bg-brand-wash',
  unseen: 'bg-muted',
}

export function KnowledgePage() {
  const k = useKnowledge()
  const { catalog, focus, board, newLimit, order, certExams, now } = useLearner()
  const navigate = useNavigate()
  const [empty, setEmpty] = useState<EmptyContinue | null>(null)

  const home = useMemo(() => {
    const all = board(null)
    if (!catalog || !all) return undefined
    const plan = continuePlan(board, focus, null, newLimit)
    return {
      rows: bySavedOrder(moduleRows(all, now), (row) => row.c.slug, order),
      toRead: readyLesson(all, order),
      toTake: readyCert(all, order, certExams),
      counts: plan && continueCounts(plan, focus, now),
      panel: focus && plan ? focusView(plan.b, focus, plan.queue, certExams, now) : null,
    }
  }, [catalog, board, focus, newLimit, order, certExams, now])

  function setFocus(f: Focus | null) {
    void k.add('focus', newRecord.focus(f))
  }

  // Continue starts the next queue, or says why nothing is ready and offers the one act that changes that
  function start(counts: { empty: boolean; blocked: boolean }) {
    if (!counts.empty) return navigate('/knowledge/queue?mode=next')
    setEmpty(emptyContinue({ blocked: counts.blocked, newLimit, focus }))
  }

  async function act(kind: string) {
    setEmpty(null)
    if (kind === 'raise') {
      await k.add('raise', newRecord.raise())
      navigate('/knowledge/queue?mode=next')
    } else if (kind === 'clear-focus') setFocus(null)
    else if (kind === 'certs') navigate(CERTIFICATIONS)
  }

  function move(rows: ModuleRow[], from: number, to: number) {
    const slugs = rows.map((row) => row.c.slug)
    void k.add('order', newRecord.order(moved(slugs, from, to)))
  }

  return (
    <section className="space-y-section">
      <PageHeader title="Knowledge" note="Answer the questions due, then the new ones." />
      {/* a failed sync changes what the next queue serves, so the home says so */}
      {k.sync.error && !k.sync.running && (
        <p
          className="rounded-xl bg-destructive/10 px-4 py-3 text-meta text-verdict-wrong"
          title={k.sync.error}
        >
          {syncErrorSummary(k.sync.error)}
        </p>
      )}
      {/* the lessons are a step down from the home: `pages.md`, The structure */}
      <p className="flex gap-4 text-meta">
        <Link to={LESSONS} className="underline underline-offset-2">
          {LESSONS_LINK}
        </Link>
        <Link to={CERTIFICATIONS} className="underline underline-offset-2">
          {CERTIFICATIONS_LINK}
        </Link>
      </p>
      <Loaded
        of={MODULES_OF}
        state={loadedFrom(k, home)}
        blank={NO_MODULES}
        blankWhen={(h) => h.rows.length === 0}
      >
        {({ rows, counts, panel, toRead, toTake }) => (
          <>
            {toTake && (
              <Link
                to={`${CERTIFICATIONS}?${new URLSearchParams({ open: toTake.id })}`}
                className="block rounded-xl border bg-brand-wash px-4 py-3 text-meta hover:bg-brand-wash/70"
              >
                {toTake.line}
              </Link>
            )}
            {/* the next step the rules would take, for a reader who never opens the lessons */}
            {toRead && (
              <Link
                to={lessonPath(toRead.c.slug, toRead.lesson.slug)}
                className="block rounded-xl border bg-brand-wash/40 px-4 py-3 text-meta hover:bg-brand-wash"
              >
                {toRead.line}
              </Link>
            )}
            {focus && panel && (
              <Panel>
                <div className="flex flex-wrap items-center gap-stack">
                  <p className="flex-1 font-medium">{focusTitle(focusLabel(focus, catalog))}</p>
                  <Toggle
                    size="sm"
                    variant="outline"
                    pressed={!!focus.strict}
                    onPressedChange={(strict) => setFocus({ ...focus, strict })}
                    aria-label={strictLabel(!!focus.strict)}
                  >
                    {STRICT}
                  </Toggle>
                  <Button variant="ghost" size="sm" onClick={() => setFocus(null)}>
                    <X />
                    {CLEAR_FOCUS}
                  </Button>
                </div>
                {panel.total > 0 && (
                  <div
                    className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted"
                    aria-hidden
                  >
                    {panel.parts.map((part) =>
                      part.v ? (
                        <div key={part.k} className={PART_TONE[part.k]} style={{ flex: part.v }} />
                      ) : null,
                    )}
                  </div>
                )}
                <p className="text-meta text-muted-foreground">{panel.summary}</p>
                <div className="flex flex-wrap items-center gap-stack text-meta">
                  <span>
                    <span className="tabular-nums">{panel.due}</span> {DUE_NOW}
                  </span>
                  {panel.learning > 0 && (
                    <span>
                      <span className="tabular-nums">{panel.learning}</span> {LEARNING}
                    </span>
                  )}
                  <span>
                    <span className="tabular-nums">{panel.newLeft}</span> {NEW_LEFT}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void k.add('raise', newRecord.raise())}
                  >
                    <Plus />
                    {RAISE_TODAY}
                  </Button>
                </div>
                {panel.next && (
                  <p className="text-meta">
                    {FOCUS_NEXT} {panel.next}
                  </p>
                )}
                {panel.cert && (
                  <p className="text-meta">
                    {FOCUS_CERT} {panel.cert}
                  </p>
                )}
              </Panel>
            )}

            <div className="space-y-1">
              <div className="flex gap-stack">
                <Button disabled={!counts} onClick={() => counts && start(counts)}>
                  {CONTINUE}
                </Button>
                {/* the second way in, at a lower weight: `pages.md`, The knowledge pages */}
                <Button variant="outline" asChild>
                  <Link to={EXAM}>{EXAM_LINK}</Link>
                </Button>
              </div>
              {counts && (
                <p className="text-meta text-muted-foreground">
                  {continueLine(counts, !!focus?.strict)}
                  {counts.outside > 0 && (
                    <>
                      {' · '}
                      {/* a press serves the reviews a strict focus leaves out */}
                      <Link
                        to="/knowledge/queue?mode=review"
                        className="underline underline-offset-2"
                      >
                        {waitingOutside(counts.outside)}
                      </Link>
                    </>
                  )}
                </p>
              )}
              {empty && (
                <div className="flex flex-wrap items-center gap-stack text-meta" role="status">
                  <span>{empty.notice}</span>
                  {empty.action && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void act(empty.action!.kind)}
                    >
                      {empty.action.label}
                    </Button>
                  )}
                </div>
              )}
            </div>

            <section className="space-y-stack">
              <SectionHeading title="Modules" count={rows.length} />
              <ul className="divide-y rounded-xl border bg-card">
                {rows.map((row, i) => (
                  <li key={row.c.slug} className="flex items-center gap-4 px-4 py-3">
                    {/* the row opens the module's page; the order presses sit beside it */}
                    <Link
                      to={`/knowledge/modules/${row.c.slug}`}
                      className="group flex-1 space-y-0.5"
                    >
                      <p className="group-hover:underline">
                        {row.c.title}
                        {row.c.paused && (
                          <span className="text-meta text-muted-foreground"> · {PAUSED}</span>
                        )}
                      </p>
                      <p className="text-meta">{row.view.title}</p>
                      {row.view.detail && (
                        <p className="text-meta text-muted-foreground">{row.view.detail}</p>
                      )}
                    </Link>
                    <span className="text-meta text-muted-foreground tabular-nums">
                      {moduleCounts(row.toReview, row.total)}
                    </span>
                    <span className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Move ${row.c.title} up`}
                        disabled={i === 0}
                        onClick={() => move(rows, i, i - 1)}
                      >
                        <ChevronUp />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Move ${row.c.title} down`}
                        disabled={i === rows.length - 1}
                        onClick={() => move(rows, i, i + 1)}
                      >
                        <ChevronDown />
                      </Button>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </Loaded>
    </section>
  )
}
