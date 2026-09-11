import { useParams } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CodeEditor } from '@/components/CodeEditor'
import { Markdown } from '@/components/Markdown'

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

  if (error) return <p className="text-destructive">The sitting did not load: {error}</p>
  if (!served) return <p className="text-muted-foreground">Loading the sitting…</p>

  const draft = `algo-coach:sitting:${sittingId}:code`

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
      <section className="lg:sticky lg:top-6 lg:h-[calc(100vh-8rem)]">
        <CodeEditor
          // what was typed survives a reload; a first visit starts on the
          // signature
          initial={stored(draft) ?? (served.signature ? `${served.signature}\n    ` : '')}
          onChange={(code) => store(draft, code)}
        />
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
