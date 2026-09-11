import { useRef, useState } from 'react'
import { useParams } from 'react-router'

import { api, type Submitted } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { CodeEditor } from '@/components/CodeEditor'
import { Markdown } from '@/components/Markdown'
import { Button } from '@/components/ui/button'
import { Verdict } from '@/components/Verdict'

export function SittingPage() {
  const { sittingId = '' } = useParams()
  const { data: served, error } = useLoaded(
    (signal) =>
      api.GET('/api/sittings/{sitting_id}', {
        params: { path: { sitting_id: sittingId } },
        signal,
      }),
    `sitting:${sittingId}`,
  )
  const code = useRef<string | null>(null)
  const [running, setRunning] = useState(false)
  const [submitted, setSubmitted] = useState<Submitted | null>(null)
  const [refused, setRefused] = useState<string | null>(null)

  if (error) return <p className="text-destructive">The sitting did not load: {error}</p>
  if (!served) return <p className="text-muted-foreground">Loading the sitting…</p>

  const draft = `algo-coach:sitting:${sittingId}:code`
  const initial = stored(draft) ?? (served.signature ? `${served.signature}\n    ` : '')

  async function submit() {
    if (running) return
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
    <div className="grid gap-6 lg:grid-cols-2">
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
          <Button onClick={submit} disabled={running}>
            {running ? 'Running…' : 'Submit'}
          </Button>
          <span className="text-sm text-muted-foreground">⌘/Ctrl + Enter</span>
        </div>
        {refused && <p className="text-destructive">The submission was refused: {refused}</p>}
        {submitted && (
          <div className="max-h-[45%] overflow-auto">
            <Verdict submitted={submitted} />
          </div>
        )}
      </section>
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
