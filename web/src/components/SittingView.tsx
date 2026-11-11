import {
  CLAIM_NOTE,
  CLAIM_TITLE,
  CLOCK_PAUSED,
  CLOCK_RUNNING,
  clockState,
  editorOpening,
  END_KEEP,
  END_NOTE,
  END_TITLE,
  RESTORE_SOLVE,
  SITTING_END,
  SITTING_ENDED,
  sittingBack,
  type ProblemFrom,
  sittingRefused,
  submitLabel,
  visibilityMove,
  OF,
  SUBMIT_HINT,
  type ClockMove,
  type Moved,
  moveSitting,
  sittingControls,
  submitToSitting,
  TOUCH_MS,
  touchSitting,
} from '@algo-coach/core'
import { ChevronLeft } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { api, type Submitted } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { ErrorLine } from '@/components/ErrorLine'
import { BackLink } from '@/components/BackLink'
import { ClaimPrompt } from '@/components/ClaimPrompt'
import { CodeEditor, type EditorHandle } from '@/components/CodeEditor'
import { ElapsedClock } from '@/components/ElapsedClock'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { ProblemFacts } from '@/components/ProblemFacts'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Verdict } from '@/components/Verdict'
import { autoStarts, pressed } from '@/lib/clock'
import { DEVICE } from '@/knowledge/copy'
import { draftOf, keepDraft } from '@/lib/draft'
import { fromPath } from '@/lib/paths'
import { useKnowledge } from '@/knowledge/context'

type Props = {
  problemId: string
  // the technique the claim answers for: the card's own, or the pick's
  drilled: string | null
  card: string | null
  from: ProblemFrom
}

// the problem's page once its statement is served. No sitting exists until the
// first clock press or submission mints one, and `?sitting=` then names it, so
// a reload reads that sitting, ended or not: `pages.md`
// the platform's monotonic clock, which a reading's arrival is stamped with
const now = () => performance.now()

export function SittingView({ problemId, drilled, card, from }: Props) {
  const [search, setSearch] = useSearchParams()
  const { user } = useKnowledge()
  // read once: the page names the sitting it minted without reading it again
  const [named] = useState(() => search.get('sitting'))
  // the way back: the page the problem came from. An ended sitting stays on
  // the page, so the solve reads back
  const back = { to: fromPath(from), label: sittingBack(from) }
  // the claim is asked once the sitting ends, and answering it closes the
  // dialog over the page rather than leaving it
  const [answered, setAnswered] = useState(false)
  const loaded = useLoaded(
    async (signal) => {
      // without `?sitting=` the statement comes with the sitting running on
      // the problem, where one runs
      const answer =
        named === null
          ? await api.GET('/api/problems/{problem_id}/statement', {
              params: { path: { problem_id: problemId } },
              signal,
            })
          : await api.GET('/api/sittings/{sitting_id}', {
              params: { path: { sitting_id: named } },
              signal,
            })
      // stamped on arrival: the clock counts on from the moment this reading
      // reached the page
      return { ...answer, data: answer.data && { ...answer.data, receivedAt: performance.now() } }
    },
    `statement:${problemId}:${named ?? ''}`,
  )
  // what a new sitting on the problem may open on, bounded by the card's run
  // where the problem came from a card
  const carried = useLoaded(
    (signal) =>
      api.GET('/api/problems/{problem_id}/carry', {
        params: { path: { problem_id: problemId }, query: { card } },
        signal,
      }),
    `carry:${problemId}:${card ?? ''}`,
  )
  const code = useRef<string | null>(null)
  const editor = useRef<EditorHandle>(null)
  // set by the restore press, and kept with the draft so a reload keeps it
  const restored = useRef<boolean | null>(null)
  const [running, setRunning] = useState(false)
  const [submitted, setSubmitted] = useState<Submitted | null>(null)
  const [refused, setRefused] = useState<string | null>(null)
  // the sitting as the last pause or resume left it, over the one first loaded,
  // with the engine's elapsed time and when the page received it
  const [moved, setMoved] = useState<Moved | null>(null)
  const [moving, setMoving] = useState(false)
  // true where hiding the page paused the sitting, so a pause the user pressed
  // is not resumed on return
  const byHiding = useRef(false)

  const current = moved?.sitting ?? loaded.data?.sitting ?? null
  const sittingId = current?.id ?? null
  const clockNow = clockState(current)
  const { paused, ended, unstarted } = clockNow
  const controls = sittingControls(clockNow, sittingId)

  // the address names the sitting once one exists, replacing itself so the
  // way back leaves the problem rather than returning to it
  useEffect(() => {
    if (sittingId === null || search.get('sitting') === sittingId) return
    setSearch(
      (was) => {
        const next = new URLSearchParams(was)
        next.set('sitting', sittingId)
        return next
      },
      { replace: true },
    )
  }, [sittingId, search, setSearch])

  // the engine ends a sitting nothing has touched, and a solver thinking is
  // practising, so a visible page reads the sitting again and that read
  // touches it. A hidden page touches nothing, and the bound then ends the
  // sitting where the page was left. An ended sitting is touched no more
  useEffect(() => {
    if (sittingId === null || !controls.touch) return
    const tick = setInterval(() => {
      if (document.hidden) return
      void touchSitting(api, sittingId, now).then((read) => read.ok && setMoved(read.value))
    }, TOUCH_MS)
    return () => clearInterval(tick)
  }, [sittingId, controls.touch])

  // a move the page took by itself says nothing to the user, so it reports no
  // refusal: the next reading of the sitting carries whatever happened. The
  // first clock press mints the sitting it runs in
  async function move(to: ClockMove, { quiet = false } = {}) {
    setMoving(true)
    if (!quiet) setRefused(null)
    const out = await moveSitting(api, problemId, DEVICE, sittingId, to, now)
    if (out.minted) setMoved(out.minted)
    if (out.ok) setMoved(out.value)
    else if (!quiet) setRefused(out.refused)
    setMoving(false)
  }

  // the user's own press on the clock, which alone sets the clock preference
  function press(to: 'start' | 'pause' | 'resume') {
    pressed(to)
    void move(to)
  }

  // the preference starts a clock the user has not, once per page
  const autoStarted = useRef(false)
  const statementIn = loaded.data !== undefined
  useEffect(() => {
    if (!statementIn || !unstarted || ended || autoStarted.current || !autoStarts()) return
    autoStarted.current = true
    void move('start', { quiet: true })
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statementIn, unstarted, ended])

  // the clock counts the time on the problem, and a hidden page is time away
  // from it. A sitting the user paused is left alone: returning resumes what
  // hiding paused and nothing else
  useEffect(() => {
    function hid() {
      const next = visibilityMove(clockNow, document.hidden, byHiding.current)
      byHiding.current = next.pausedByHiding
      if (next.move) void move(next.move, { quiet: true })
    }
    document.addEventListener('visibilitychange', hid)
    return () => document.removeEventListener('visibilitychange', hid)
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, paused, ended, unstarted, sittingId])

  // the three readings; the page starts once the statement has loaded
  if (loaded.data === undefined)
    return (
      <Loaded of={OF.problem} state={loaded}>
        {() => null}
      </Loaded>
    )
  // the editor seeds once, so it waits for the carry. A carry that failed
  // opens the editor on the signature rather than holding the sitting
  // a draft is keyed to its user, so the editor waits for the session to name one
  if ((carried.data === undefined && carried.error === undefined) || user === null)
    return (
      <Loaded of={OF.problem} state={{ ...carried, data: undefined }}>
        {() => null}
      </Loaded>
    )

  const served = loaded.data
  const clock = moved ?? { elapsedSec: served.elapsed_sec, at: served.receivedAt }
  // a reload during the sitting restores what was typed in it, and a new
  // sitting opens on the work in progress `flows.md` carries
  const opened = editorOpening(
    draftOf(user, problemId),
    sittingId,
    carried.data ?? null,
    served.signature ?? null,
  )
  const initial = opened.code
  const keptRestored = opened.restored
  const solve = carried.data?.solved_code ?? null

  // the user's own act: the solve is never carried, so it returns only here
  function restore() {
    if (solve === null) return
    restored.current = true
    editor.current?.replace(solve)
  }

  async function submit() {
    // the shortcut reaches here with the press disabled: an ended sitting
    // takes no submission, as on the phone
    if (running || ended) return
    setRunning(true)
    setRefused(null)
    const sent = await submitToSitting(
      api,
      problemId,
      DEVICE,
      sittingId,
      { code: code.current ?? initial, restored: restored.current ?? keptRestored },
      now,
    )
    if (sent.minted) setMoved(sent.minted)
    if (sent.ok) {
      setSubmitted(sent.value.submitted)
      // a solve ends the sitting, and the ended sitting asks for the claims
      setMoved(sent.value.moved)
    } else setRefused(sent.refused)
    setRunning(false)
  }

  return (
    <div className="space-y-stack">
      {/* the sitting is run from one row, and it stays in view while the
          statement scrolls: the clock is what the solver is watched by */}
      <div className="sticky top-0 z-10 -mx-gutter border-b bg-background px-gutter">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 py-2">
          {/* the page's one title: it stays in view while the statement
              scrolls, so the statement column repeats none */}
          {/* the way back, at any point: leaving a sitting ends nothing, and an
              ended one has nothing left to do here */}
          {ended ? (
            <Button asChild>
              <Link to={back.to}>
                <ChevronLeft />
                {back.label}
              </Link>
            </Button>
          ) : (
            <BackLink to={back.to} label={back.label} />
          )}
          <h1 className="min-w-0 truncate text-heading font-semibold">{served.title}</h1>
          {/* pushed right only where it shares the title's row: wrapped under
              a narrow title, it starts where the title does */}
          <div className="flex items-center gap-3 sm:ml-auto">
            {/* a dot while the clock runs: the label on the press alone left
                running and stopped looking alike */}
            {clockNow.running && (
              <span
                role="img"
                aria-label={CLOCK_RUNNING}
                className="size-2 rounded-full bg-clock-running"
              />
            )}
            <ElapsedClock
              elapsedSec={clock.elapsedSec}
              receivedAt={clock.at}
              running={clockNow.running}
            />
            {paused && !ended && (
              <span className="text-meta text-muted-foreground">{CLOCK_PAUSED}</span>
            )}
            {ended ? (
              <>
                <span className="text-meta text-muted-foreground">{SITTING_ENDED}</span>
              </>
            ) : (
              <>
                {/* one press for the clock, as core picks it: a control
                    rather than the page's act */}
                {controls.clock && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => controls.clock && press(controls.clock.to)}
                    disabled={moving}
                  >
                    {controls.clock.label}
                  </Button>
                )}
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm" disabled={moving || !controls.end}>
                      {SITTING_END}
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>{END_TITLE}</AlertDialogTitle>
                      <AlertDialogDescription>{END_NOTE}</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{END_KEEP}</AlertDialogCancel>
                      <AlertDialogAction onClick={() => move('end')}>
                        {SITTING_END}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </>
            )}
          </div>
        </div>
      </div>
      {refused && <ErrorLine>{sittingRefused(refused)}</ErrorLine>}
      {/* a paused clock leaves the page as it was: a pause stops the timing,
          not the practice */}
      {/* explicit columns: an implicit one grows to the editor's longest line,
          and a narrow window then scrolls sideways */}
      <div className="grid grid-cols-1 gap-gutter lg:grid-cols-2">
        <section className="space-y-stack">
          <ProblemFacts problemId={problemId} technique={drilled} />
          <Markdown>{served.statement}</Markdown>
        </section>
        {/* the verdict sits under the editor: one page is the whole sitting */}
        <section className="flex flex-col gap-stack lg:sticky lg:top-6 lg:h-[calc(100vh-10rem)]">
          <div className="min-h-96 flex-1 lg:min-h-0">
            <CodeEditor
              // what was typed survives a reload; a first visit starts on the
              // signature
              initial={initial}
              onChange={(typed) => {
                code.current = typed
                keepDraft(user, problemId, sittingId, typed, restored.current ?? keptRestored)
              }}
              onSubmit={submit}
              handle={editor}
              // a solve ends the sitting, and its code is read back, not
              // carried into a new sitting: `flows.md`, Drill loop
              readOnly={ended}
            />
          </div>
          <div className="flex flex-wrap items-center gap-stack">
            <Button onClick={submit} disabled={running || ended}>
              {submitLabel(running)}
            </Button>
            {/* a keyboard's shortcut, so a narrow window leaves it out and the
                restore press keeps the submit press's row */}
            <span className="hidden text-meta text-muted-foreground sm:inline">{SUBMIT_HINT}</span>
            {/* quiet, and marked on the attempt: a solve typed over a restored
                one is not an independent solve */}
            {solve !== null && !ended && (
              <Button variant="ghost" size="sm" className="ml-auto" onClick={restore}>
                {RESTORE_SOLVE}
              </Button>
            )}
          </div>
          {/* the verdict sits under the editor: a failing case is read beside
              the code that failed it */}
          {submitted && (
            <div className="max-h-[45%] overflow-auto rounded-xl border bg-card px-4 py-3">
              <Verdict submitted={submitted} />
            </div>
          )}
        </section>
      </div>
      {/* the claim the sitting ends on; closing it leaves the attempts to the
          problem's own techniques, and a reload asks again */}
      <Dialog open={ended && !answered} onOpenChange={(open) => open || setAnswered(true)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{CLAIM_TITLE}</DialogTitle>
            <DialogDescription>{CLAIM_NOTE}</DialogDescription>
          </DialogHeader>
          {ended && sittingId !== null && (
            <ClaimPrompt sittingId={sittingId} drilled={drilled} onDone={() => setAnswered(true)} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
