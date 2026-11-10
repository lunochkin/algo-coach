import { ChevronDown, ChevronUp, Plus, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import {
  bySavedOrder,
  continueCounts,
  continueLine,
  continuePlan,
  emptyContinue,
  type EmptyContinue,
  focusLabel,
  focusView,
  moduleRows,
  moved,
  NEW_STEP,
  type Focus,
  type FocusPart,
  type ModuleRow,
} from '@algo-coach/core'

import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { SectionHeading } from '@/components/SectionHeading'
import { Button } from '@/components/ui/button'
import { Toggle } from '@/components/ui/toggle'
import { loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'

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
      counts: plan && continueCounts(plan, focus, now),
      panel: focus && plan ? focusView(plan.b, focus, plan.queue, certExams, now) : null,
    }
  }, [catalog, board, focus, newLimit, order, certExams, now])

  function setFocus(f: Focus | null) {
    const line = { course: f?.course ?? null, topic: f?.topic ?? null, sub: f?.sub ?? null, strict: !!f?.strict }
    void k.add('focus', f?.cert ? { ...line, cert: f.cert } : line)
  }

  // Continue starts the next queue, or says why nothing is ready and offers the one act that changes that
  function start(counts: { empty: boolean; blocked: boolean }) {
    if (!counts.empty) return navigate('/knowledge/queue?mode=next')
    setEmpty(emptyContinue({ blocked: counts.blocked, newLimit, focus }))
  }

  async function act(kind: string) {
    setEmpty(null)
    if (kind === 'raise') {
      await k.add('raise', { n: NEW_STEP })
      navigate('/knowledge/queue?mode=next')
    } else if (kind === 'clear-focus') setFocus(null)
  }

  function move(rows: ModuleRow[], from: number, to: number) {
    const slugs = rows.map((row) => row.c.slug)
    void k.add('order', { courses: moved(slugs, from, to) })
  }

  return (
    <section className="space-y-section">
      <PageHeader title="Knowledge" note="Answer the questions due, then the new ones." />
      <Loaded
        of="the modules"
        state={loadedFrom(k, home)}
        blank="No module is seeded yet."
        blankWhen={(h) => h.rows.length === 0}
      >
        {({ rows, counts, panel }) => (
          <>
            {focus && panel && (
              <Panel>
                <div className="flex flex-wrap items-center gap-stack">
                  <p className="flex-1 font-medium">Focus: {focusLabel(focus, catalog)}</p>
                  <Toggle
                    size="sm"
                    variant="outline"
                    pressed={!!focus.strict}
                    onPressedChange={(strict) => setFocus({ ...focus, strict })}
                    aria-label={
                      focus.strict ? 'Strict: reviews from the focus alone' : 'Relaxed: reviews from everywhere'
                    }
                  >
                    Strict
                  </Toggle>
                  <Button variant="ghost" size="sm" onClick={() => setFocus(null)}>
                    <X />
                    Clear
                  </Button>
                </div>
                {panel.total > 0 && (
                  <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
                    {panel.parts.map((part) =>
                      part.v ? <div key={part.k} className={PART_TONE[part.k]} style={{ flex: part.v }} /> : null,
                    )}
                  </div>
                )}
                <p className="text-meta text-muted-foreground">{panel.summary}</p>
                <div className="flex flex-wrap items-center gap-stack text-meta">
                  <span>
                    <span className="tabular-nums">{panel.due}</span> to review now
                  </span>
                  {panel.learning > 0 && (
                    <span>
                      <span className="tabular-nums">{panel.learning}</span> learning
                    </span>
                  )}
                  <span>
                    <span className="tabular-nums">{panel.newLeft}</span> new left today
                  </span>
                  <Button variant="outline" size="sm" onClick={() => void k.add('raise', { n: NEW_STEP })}>
                    <Plus />
                    {NEW_STEP} more new today
                  </Button>
                </div>
                {panel.next && <p className="text-meta">Next: {panel.next}</p>}
                {panel.cert && <p className="text-meta">Certificate: {panel.cert}</p>}
              </Panel>
            )}

            <div className="space-y-1">
              <Button disabled={!counts} onClick={() => counts && start(counts)}>
                Continue
              </Button>
              {counts && (
                <p className="text-meta text-muted-foreground">
                  {continueLine(counts, !!focus?.strict)}
                  {counts.outside > 0 && (
                    <>
                      {' · '}
                      {/* a press serves the reviews a strict focus leaves out */}
                      <Link to="/knowledge/queue?mode=review" className="underline underline-offset-2">
                        {counts.outside} waiting outside
                      </Link>
                    </>
                  )}
                </p>
              )}
              {empty && (
                <div className="flex flex-wrap items-center gap-stack text-meta" role="status">
                  <span>{empty.notice}</span>
                  {/* the certifications page arrives with its own item */}
                  {empty.action && empty.action.kind !== 'certs' && (
                    <Button variant="outline" size="sm" onClick={() => void act(empty.action!.kind)}>
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
                    <div className="flex-1 space-y-0.5">
                      <p>
                        {row.c.title}
                        {row.c.paused && <span className="text-meta text-muted-foreground"> · paused</span>}
                      </p>
                      <p className="text-meta">{row.view.title}</p>
                      {row.view.detail && <p className="text-meta text-muted-foreground">{row.view.detail}</p>}
                    </div>
                    <span className="text-meta text-muted-foreground tabular-nums">
                      {row.toReview} due · {row.total} questions
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
