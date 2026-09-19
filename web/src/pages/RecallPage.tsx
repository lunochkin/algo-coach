import { useRef, useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Hint, type RecallAttempt } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { CodeEditor } from '@/components/CodeEditor'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { CaseStrip } from '@/components/Verdict'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { failures } from '@/lib/verdicts'

// the order the trainer offers them, and each one answers more of the
// question than the last: `flows.md`
const LADDER: Hint[] = ['title', 'notes', 'form']
const NAMES: Record<Hint, string> = { title: 'the title', notes: 'the notes', form: 'the form' }

export function RecallPage() {
  const { slug = '' } = useParams()
  const [drawn, setDrawn] = useState(0)
  const prompt = useLoaded(
    (signal) => api.GET('/api/cards/{slug}/recall', { params: { path: { slug } }, signal }),
    `recall:${slug}:${drawn}`,
  )

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: `/cards/${encodeURIComponent(slug)}`, label: 'the card' }}
        title="Recall a form"
        note="The title and the form are withheld. Reach for them as hints where memory fails."
      />
      <Loaded of="the form to recall" state={prompt}>
        {(prompt) => (
          <Trainer
            key={prompt.template_id}
            slug={slug}
            templateId={prompt.template_id}
            trigger={prompt.trigger}
            signature={prompt.signature}
            onAnother={() => setDrawn(drawn + 1)}
          />
        )}
      </Loaded>
    </article>
  )
}

type Props = {
  slug: string
  templateId: string
  trigger: string
  signature: string
  onAnother: () => void
}

function Trainer({ slug, templateId, trigger, signature, onAnother }: Props) {
  // the signature, and the file otherwise blank
  const blank = `${signature}\n    `
  const code = useRef(blank)
  const [taken, setTaken] = useState<{ hint: Hint; text: string }[]>([])
  const [running, setRunning] = useState(false)
  const [ran, setRan] = useState<RecallAttempt | null>(null)
  const [refused, setRefused] = useState<string | null>(null)
  const next = LADDER[taken.length]

  // one hint per request, so the page holds nothing it was not given
  async function hint() {
    if (next === undefined) return
    const { data, error } = await api.GET('/api/cards/{slug}/recall/{template_id}/hints/{hint}', {
      params: { path: { slug, template_id: templateId, hint: next } },
    })
    if (data) setTaken([...taken, { hint: data.hint, text: data.text }])
    else setRefused(described(error))
  }

  async function run() {
    setRunning(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/cards/{slug}/recall/{template_id}', {
        params: { path: { slug, template_id: templateId } },
        body: { code: code.current, hints: taken.map((one) => one.hint) },
      })
      if (data) setRan(data)
      else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setRunning(false)
    }
  }

  if (ran !== null) return <Ran ran={ran} slug={slug} onAnother={onAnother} />

  return (
    <div className="space-y-section">
      <section className="space-y-1">
        <h2 className="text-heading font-medium">When to reach for it</h2>
        <p>{trigger}</p>
      </section>
      {taken.map((one) => (
        <section key={one.hint} className="space-y-1 rounded-lg border p-4">
          <h3 className="text-meta text-muted-foreground">Hint: {NAMES[one.hint]}</h3>
          {one.hint === 'form' ? (
            <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
              {one.text}
            </pre>
          ) : (
            <Markdown>{one.text}</Markdown>
          )}
        </section>
      ))}
      <section className="space-y-stack">
        <div className="h-96">
          {/* the signature, and the file otherwise blank: `corpus.md` gives why
              the parameter order is stated rather than inferred */}
          <CodeEditor initial={blank} onChange={(typed) => (code.current = typed)} onSubmit={run} />
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run'}
          </Button>
          <span className="text-meta text-muted-foreground">⌘/Ctrl + Enter</span>
          {next !== undefined && (
            <Button variant="outline" className="ml-auto" onClick={hint}>
              Hint: {NAMES[next]}
            </Button>
          )}
        </div>
        {refused && <p className="text-destructive">The recall did not run: {refused}</p>}
      </section>
    </div>
  )
}

// a hinted pass is a pass with its hints, which the record keeps
function Ran({ ran, slug, onAnother }: { ran: RecallAttempt; slug: string; onAnother: () => void }) {
  return (
    <div className="space-y-section">
      <p className={cn('font-medium', verified(ran) ? 'text-verdict-passed' : 'text-verdict-wrong')}>
        {verified(ran) ? 'Recalled' : 'Not recalled'}: {passed(ran)} of {(ran.results ?? []).length}{' '}
        cases passed
      </p>
      {failures(ran.results ?? []).length > 0 && (
        <p className="text-meta text-muted-foreground">
          {failures(ran.results ?? []).join(' · ')}
        </p>
      )}
      <CaseStrip results={ran.results ?? []} />
      <p className="text-meta text-muted-foreground">
        {(ran.hints ?? []).length === 0
          ? 'Recalled cold, with no hint taken.'
          : `${(ran.hints ?? []).length} hint(s) taken: ${(ran.hints ?? []).join(', ')}.`}
      </p>
      <div className="flex items-center gap-3">
        <Button onClick={onAnother}>Recall another</Button>
        <Button variant="outline" asChild>
          <Link to={`/cards/${encodeURIComponent(slug)}`}>Back to the card</Link>
        </Button>
      </div>
    </div>
  )
}

function verified(ran: RecallAttempt): boolean {
  const results = ran.results ?? []
  return results.length > 0 && results.every((one) => one.outcome === 'passed')
}

function passed(ran: RecallAttempt): number {
  return (ran.results ?? []).filter((one) => one.outcome === 'passed').length
}
