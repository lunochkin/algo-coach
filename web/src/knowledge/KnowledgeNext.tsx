import { Plus, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import {
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
  NEW_LEFT,
  newRecord,
  RAISE_TODAY,
  STRICT,
  strictLabel,
  waitingOutside,
  continueAct,
  type EmptyAction,
} from '@algo-coach/core'

import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Toggle } from '@/components/ui/toggle'
import { useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { CERTIFICATIONS, EXAM, KNOWLEDGE } from '@/knowledge/paths'

// the focus bar reads in the flame for what is held, mastered then learning.
// What is owed reads neutral, since the flame is progress and a review is not
const PART_TONE: Record<FocusPart, string> = {
  mastered: 'bg-brand',
  learning: 'bg-brand/65',
  review: 'bg-foreground/25',
  unseen: 'bg-muted',
}

// the knowledge study's next step: the focus and how far it has got, then
// Continue, the press starting the next queue. The knowledge home holds it
// with the focus's presses, and the board holds it as a reading whose panel
// opens the home: `pages.md`, Sections
export function KnowledgeNext({ controls }: { controls: boolean }) {
  const k = useKnowledge()
  const { catalog, focus, board, newLimit, certExams, now } = useLearner()
  const navigate = useNavigate()
  const [empty, setEmpty] = useState<EmptyContinue | null>(null)

  const next = useMemo(() => {
    if (!catalog || !board(null)) return undefined
    const plan = continuePlan(board, focus, null, newLimit)
    return {
      counts: plan && continueCounts(plan, focus, now),
      panel: focus && plan ? focusView(plan.b, focus, plan.queue, certExams, now) : null,
    }
  }, [catalog, board, focus, newLimit, certExams, now])
  if (!next) return null
  const { counts, panel } = next

  function setFocus(f: Focus | null) {
    void k.add('focus', newRecord.focus(f))
  }

  // Continue starts the next queue, or says why nothing is ready and offers the one act that changes that
  function start(c: { empty: boolean; blocked: boolean }) {
    if (!c.empty) return navigate('/knowledge/queue?mode=next')
    setEmpty(emptyContinue({ blocked: c.blocked, newLimit, focus }))
  }

  async function act(kind: EmptyAction) {
    setEmpty(null)
    const step = continueAct(kind)
    if (step.raise) await k.add('raise', newRecord.raise())
    if (step.clearFocus) setFocus(null)
    if (step.open === 'queue') navigate('/knowledge/queue?mode=next')
    else if (step.open === 'certs') navigate(CERTIFICATIONS)
  }

  const reading = focus && panel && (
    <>
      <div className="flex flex-wrap items-center gap-stack">
        <p className="flex-1 font-medium">{focusTitle(focusLabel(focus, catalog))}</p>
        {controls && (
          <>
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
          </>
        )}
      </div>
      {panel.total > 0 && (
        <div className="flex h-1 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
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
        {controls && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => void k.add('raise', newRecord.raise())}
          >
            <Plus />
            {RAISE_TODAY}
          </Button>
        )}
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
    </>
  )

  return (
    <>
      {reading &&
        (controls ? (
          <Panel>{reading}</Panel>
        ) : (
          // a reading on the board: the panel opens the home, where its presses are
          <Link to={KNOWLEDGE} className="block rounded-xl transition-colors hover:bg-accent">
            <Panel>{reading}</Panel>
          </Link>
        ))}
      <div className="space-y-1">
        <div className="flex gap-stack">
          <Button disabled={!counts} onClick={() => counts && start(counts)}>
            {CONTINUE}
          </Button>
          {/* the second way in, at a lower weight, on the knowledge home: `pages.md`, The knowledge pages */}
          {controls && (
            <Button variant="outline" asChild>
              <Link to={EXAM}>{EXAM_LINK}</Link>
            </Button>
          )}
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
                  className="font-medium underline-offset-4 hover:underline"
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
              <Button variant="outline" size="sm" onClick={() => void act(empty.action!.kind)}>
                {empty.action.label}
              </Button>
            )}
          </div>
        )}
      </div>
    </>
  )
}
