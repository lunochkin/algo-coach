import { ChevronLeft } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'

import { api, type Sitting, type Submitted } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
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
import { draftOf, keepDraft, opening } from '@/lib/draft'

type Moved = { sitting: Sitting; elapsedSec: number | null; at: number }

export function SittingPage() {
  const { sittingId = '' } = useParams()
  const [search] = useSearchParams()
  // the way back: the card the problem came from, where the next rung is, or
  // the board. An ended sitting stays on the page, so the solve reads back
  const card = search.get('card')
  const back =
    card === null
      ? { to: '/', label: 'Back to the board' }
      : { to: `/cards/${encodeURIComponent(card)}`, label: 'Back to the card' }
  // the claim is asked once the sitting ends, and answering it closes the
  // dialog over the page rather than leaving it
  const [answered, setAnswered] = useState(false)
  const loaded = useLoaded(
    async (signal) => {
      const answer = await api.GET('/api/sittings/{sitting_id}', {
        params: { path: { sitting_id: sittingId } },
        signal,
      })
      // stamped on arrival: the clock counts on from the moment this reading
      // reached the page
      return { ...answer, data: answer.data && { ...answer.data, receivedAt: performance.now() } }
    },
    `sitting:${sittingId}`,
  )
  // what a new sitting on the problem may open on, bounded by the card's run
  // where the problem came from a card
  const problemOf = loaded.data?.sitting.problem_id
  const carried = useLoaded(
    (signal) =>
      problemOf === undefined
        ? Promise.resolve({ data: null })
        : api.GET('/api/problems/{problem_id}/carry', {
            params: { path: { problem_id: problemOf }, query: { card } },
            signal,
          }),
    `carry:${problemOf ?? ''}:${card ?? ''}`,
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

  // the engine ends a sitting nothing has touched, and a solver thinking is
  // practising, so a visible page reads the sitting again and that read
  // touches it. A hidden page touches nothing, and the bound then ends the
  // sitting where the page was left
  useEffect(() => {
    const tick = setInterval(
      () => {
        if (document.hidden) return
        void api
          .GET('/api/sittings/{sitting_id}', { params: { path: { sitting_id: sittingId } } })
          .then(({ data }) => {
            if (data) {
              setMoved({
                sitting: data.sitting,
                elapsedSec: data.elapsed_sec,
                at: performance.now(),
              })
            }
          })
      },
      // well under the 45 minutes an untouched sitting is ended at
      10 * 60 * 1000,
    )
    return () => clearInterval(tick)
  }, [sittingId])

  const current = moved?.sitting ?? loaded.data?.sitting
  const paused = current?.pauses?.at(-1)?.until === null
  const ended = current?.ended_at != null
  const unstarted = current !== undefined && current.clock_started_at == null

  // a move the page took by itself says nothing to the user, so it reports no
  // refusal: the next reading of the sitting carries whatever happened
  async function move(to: 'start' | 'pause' | 'resume' | 'end', { quiet = false } = {}) {
    setMoving(true)
    if (!quiet) setRefused(null)
    try {
      const params = { params: { path: { sitting_id: sittingId } } }
      const { data, error } =
        to === 'start'
          ? await api.POST('/api/sittings/{sitting_id}/start', params)
          : to === 'pause'
            ? await api.POST('/api/sittings/{sitting_id}/pause', params)
            : to === 'resume'
              ? await api.POST('/api/sittings/{sitting_id}/resume', params)
              : await api.POST('/api/sittings/{sitting_id}/end', params)
      if (data)
        setMoved({ sitting: data.sitting, elapsedSec: data.elapsed_sec, at: performance.now() })
      else if (!quiet) setRefused(described(error))
    } catch (reason) {
      if (!quiet) setRefused(String(reason))
    } finally {
      setMoving(false)
    }
  }

  // the user's own press on the clock, which alone sets the clock preference
  function press(to: 'start' | 'pause' | 'resume') {
    pressed(to !== 'pause')
    void move(to)
  }

  // the preference starts a clock the user has not, once per page
  const autoStarted = useRef(false)
  useEffect(() => {
    if (!unstarted || ended || autoStarted.current || !autoStarts()) return
    autoStarted.current = true
    void move('start', { quiet: true })
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unstarted, ended])

  // the clock counts the time on the problem, and a hidden page is time away
  // from it. A sitting the user paused is left alone: returning resumes what
  // hiding paused and nothing else
  useEffect(() => {
    function hid() {
      // nothing to move before the sitting has been read
      if (current === undefined || ended || unstarted) return
      if (document.hidden && !paused) {
        byHiding.current = true
        void move('pause', { quiet: true })
      } else if (!document.hidden && byHiding.current) {
        byHiding.current = false
        void move('resume', { quiet: true })
      }
    }
    document.addEventListener('visibilitychange', hid)
    return () => document.removeEventListener('visibilitychange', hid)
    // `move` is a new closure on every render, and it reads `sittingId` alone
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, paused, ended, unstarted, sittingId])

  // the three readings; the sitting's own page starts once one has loaded
  if (loaded.data === undefined)
    return <Loaded of="the sitting" state={loaded}>{() => null}</Loaded>
  // the editor seeds once, so it waits for the carry. A carry that failed
  // opens the editor on the signature rather than holding the sitting
  if (carried.data === undefined && carried.error === undefined)
    return <Loaded of="the sitting" state={{ ...carried, data: undefined }}>{() => null}</Loaded>

  const served = loaded.data
  const clock = moved ?? { elapsedSec: served.elapsed_sec, at: served.receivedAt }
  const problemId = served.sitting.problem_id
  // a reload during the sitting restores what was typed in it, and a new
  // sitting opens on the work in progress `flows.md` carries
  const kept = draftOf(problemId)
  const blank = served.signature ? `${served.signature}\n    ` : ''
  const initial =
    kept?.sitting === sittingId ? kept.code : (opening(kept, carried.data ?? null) ?? blank)
  const keptRestored = kept?.sitting === sittingId && kept.restored === true
  const solve = carried.data?.solved_code ?? null

  // the user's own act: the solve is never carried, so it returns only here
  function restore() {
    if (solve === null) return
    restored.current = true
    editor.current?.replace(solve)
  }

  async function submit() {
    if (running) return
    setRunning(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/sittings/{sitting_id}/submissions', {
        params: { path: { sitting_id: sittingId } },
        body: { code: code.current ?? initial, restored: restored.current ?? keptRestored },
      })
      if (data) {
        setSubmitted(data)
        // a solve ends the sitting, and the ended sitting asks for the claims
        setMoved({
          sitting: data.sitting,
          elapsedSec: data.attempt.time_to_solve_sec ?? null,
          at: performance.now(),
        })
      } else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setRunning(false)
    }
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
            <Button asChild size="sm">
              <Link to={back.to}>
                <ChevronLeft className="size-4" />
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
            <ElapsedClock
              elapsedSec={clock.elapsedSec}
              receivedAt={clock.at}
              running={!paused && !ended && !unstarted}
            />
            {paused && !ended && <span className="text-meta text-muted-foreground">paused</span>}
            {ended ? (
              <>
                <span className="text-meta text-muted-foreground">This sitting has ended</span>
              </>
            ) : (
              <>
                {/* one press for the clock: it starts a clock that never ran,
                    resumes a paused one, and pauses a running one */}
                {unstarted || paused ? (
                  <Button
                    // a control rather than the page's act
                    variant="outline"
                    size="sm"
                    onClick={() => press(unstarted ? 'start' : 'resume')}
                    disabled={moving}
                  >
                    Start
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => press('pause')}
                    disabled={moving}
                  >
                    Pause
                  </Button>
                )}
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm" disabled={moving}>
                      End
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>End the sitting?</AlertDialogTitle>
                      <AlertDialogDescription>
                        The clock stops for good, and no more submissions are taken. Each attempt
                        is then asked about in turn.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Keep solving</AlertDialogCancel>
                      <AlertDialogAction onClick={() => move('end')}>End</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </>
            )}
          </div>
        </div>
      </div>
      {refused && <p className="text-meta text-destructive">Refused: {refused}</p>}
      {/* a paused clock leaves the page as it was: a pause stops the timing,
          not the practice */}
      {/* explicit columns: an implicit one grows to the editor's longest line,
          and a narrow window then scrolls sideways */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="space-y-stack">
          <ProblemFacts
            problemId={served.sitting.problem_id}
            technique={search.get('technique')}
          />
          <Markdown>{served.statement}</Markdown>
        </section>
        {/* the verdict sits under the editor: one page is the whole sitting */}
        <section className="flex flex-col gap-3 lg:sticky lg:top-6 lg:h-[calc(100vh-10rem)]">
          <div className="min-h-96 flex-1 lg:min-h-0">
            <CodeEditor
              // what was typed survives a reload; a first visit starts on the
              // signature
              initial={initial}
              onChange={(typed) => {
                code.current = typed
                keepDraft(problemId, sittingId, typed, restored.current ?? keptRestored)
              }}
              onSubmit={submit}
              handle={editor}
            />
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <Button onClick={submit} disabled={running || ended}>
              {running ? 'Running…' : 'Submit'}
            </Button>
            {/* a keyboard's shortcut, so a narrow window leaves it out and the
                restore press keeps the submit press's row */}
            <span className="hidden text-meta text-muted-foreground sm:inline">
              ⌘/Ctrl + Enter · judged against the problem&rsquo;s own test cases
            </span>
            {/* quiet, and marked on the attempt: a solve typed over a restored
                one is not an independent solve */}
            {solve !== null && !ended && (
              <Button variant="ghost" size="sm" className="ml-auto" onClick={restore}>
                Restore my last solve
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
            <DialogTitle>The claim</DialogTitle>
            <DialogDescription>
              Asked of each attempt now, while the code is minutes old.
            </DialogDescription>
          </DialogHeader>
          {ended && (
            <ClaimPrompt
              sittingId={sittingId}
              drilled={search.get('technique')}
              onDone={() => setAnswered(true)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
