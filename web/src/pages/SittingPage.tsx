import { useCallback, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import { api, type Sitting, type Submitted } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { ClaimPrompt } from '@/components/ClaimPrompt'
import { CodeEditor } from '@/components/CodeEditor'
import { ElapsedClock } from '@/components/ElapsedClock'
import { Markdown } from '@/components/Markdown'
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
import { cn } from '@/lib/utils'

export function SittingPage() {
  const { sittingId = '' } = useParams()
  const [search] = useSearchParams()
  const navigate = useNavigate()
  const toBoard = useCallback(() => navigate('/'), [navigate])
  const { data: served, error } = useLoaded(
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
  const code = useRef<string | null>(null)
  const [running, setRunning] = useState(false)
  const [submitted, setSubmitted] = useState<Submitted | null>(null)
  const [refused, setRefused] = useState<string | null>(null)
  // the sitting as the last pause or resume left it, over the one first loaded,
  // with the engine's elapsed time and when the page received it
  const [moved, setMoved] = useState<{ sitting: Sitting; elapsedSec: number; at: number } | null>(
    null,
  )
  const [moving, setMoving] = useState(false)

  if (error) return <p className="text-destructive">The sitting did not load: {error}</p>
  if (!served) return <p className="text-muted-foreground">Loading the sitting…</p>

  const sitting = moved?.sitting ?? served.sitting
  const clock = moved ?? { elapsedSec: served.elapsed_sec, at: served.receivedAt }
  const paused = sitting.pauses?.at(-1)?.until === null
  const ended = sitting.ended_at != null
  const draft = `algo-coach:sitting:${sittingId}:code`
  const initial = stored(draft) ?? (served.signature ? `${served.signature}\n    ` : '')

  async function move(to: 'pause' | 'resume' | 'end') {
    setMoving(true)
    setRefused(null)
    try {
      const params = { params: { path: { sitting_id: sittingId } } }
      const { data, error } =
        to === 'pause'
          ? await api.POST('/api/sittings/{sitting_id}/pause', params)
          : to === 'resume'
            ? await api.POST('/api/sittings/{sitting_id}/resume', params)
            : await api.POST('/api/sittings/{sitting_id}/end', params)
      if (data) setMoved({ sitting: data.sitting, elapsedSec: data.elapsed_sec, at: performance.now() })
      else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setMoving(false)
    }
  }

  async function submit() {
    if (running || paused) return
    setRunning(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/sittings/{sitting_id}/submissions', {
        params: { path: { sitting_id: sittingId } },
        body: { code: code.current ?? initial },
      })
      if (data) setSubmitted(data)
      else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-4">
      {paused && (
        <div className="flex items-center justify-between rounded-md border border-amber-500/50 bg-amber-500/10 p-3">
          <span className="font-medium">Paused: the clock is stopped</span>
          <div className="flex items-center gap-3">
            {/* the time the pause froze: the clock under the cover is blurred */}
            <ElapsedClock elapsedSec={clock.elapsedSec} receivedAt={clock.at} running={false} />
            <Button onClick={() => move('resume')} disabled={moving}>
              Resume
            </Button>
          </div>
        </div>
      )}
      {refused && <p className="text-destructive">Refused: {refused}</p>}
      {/* inert and covered while paused: the time away is not spent on the
          problem, and no keystroke reaches the editor */}
      <div
        inert={paused}
        className={cn('grid gap-6 lg:grid-cols-2', paused && 'blur-md select-none')}
      >
        <section className="space-y-4">
          <h1 className="text-2xl font-semibold">{served.title}</h1>
          <Markdown>{served.statement}</Markdown>
          {served.signature && (
            <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-sm">
              {served.signature}
            </pre>
          )}
        </section>
        {/* the verdict sits under the editor: one page is the whole sitting */}
        <section className="flex flex-col gap-3 lg:sticky lg:top-6 lg:h-[calc(100vh-8rem)]">
          <div className="min-h-96 flex-1 lg:min-h-0">
            <CodeEditor
              // what was typed survives a reload; a first visit starts on the
              // signature
              initial={initial}
              onChange={(typed) => {
                code.current = typed
                store(draft, typed)
              }}
              onSubmit={submit}
            />
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={submit} disabled={running || paused || ended}>
              {running ? 'Running…' : 'Submit'}
            </Button>
            <span className="text-sm text-muted-foreground">⌘/Ctrl + Enter</span>
            <div className="ml-auto flex items-center gap-3">
              <ElapsedClock
                elapsedSec={clock.elapsedSec}
                receivedAt={clock.at}
                running={!paused && !ended}
              />
              {ended ? (
                <span className="text-sm text-muted-foreground">This sitting has ended</span>
              ) : (
                <>
                  <Button variant="outline" onClick={() => move('pause')} disabled={moving}>
                    Pause
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" disabled={moving}>
                        End
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>End the sitting?</AlertDialogTitle>
                        <AlertDialogDescription>
                          The clock stops for good, and no more submissions are taken. Each
                          attempt is then asked about in turn.
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
          {submitted && (
            <div className="max-h-[45%] overflow-auto">
              <Verdict submitted={submitted} />
            </div>
          )}
        </section>
      </div>
      {/* the claim the sitting ends on; closing it leaves the attempts to the
          problem's own techniques, and a reload asks again */}
      <Dialog open={ended} onOpenChange={(open) => open || toBoard()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>The claim</DialogTitle>
            <DialogDescription>
              Asked of each attempt now, while the code is minutes old.
            </DialogDescription>
          </DialogHeader>
          {ended && (
            <ClaimPrompt sittingId={sittingId} drilled={search.get('technique')} onDone={toBoard} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function stored(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function store(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // a browser refusing storage costs the draft on reload, not the sitting
  }
}
