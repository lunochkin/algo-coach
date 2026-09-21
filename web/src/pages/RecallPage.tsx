import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'

import { api, type Hint, type Named, type RecallAttempt } from '@/api/client'
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
const LADDER: Hint[] = ['notes', 'form']
const NAMES: Record<Hint, string> = { notes: 'the notes', form: 'the form' }

// the path names no template, so the trainer draws one and sends the browser
// to it: a reload then asks for the same form
export function DrawnRecallPage() {
  const { slug = '' } = useParams()
  const navigate = useNavigate()
  const prompt = useLoaded(
    (signal) => api.GET('/api/cards/{slug}/recall', { params: { path: { slug } }, signal }),
    `recall:${slug}`,
  )
  const drew = prompt.data?.template_slug

  useEffect(() => {
    if (drew === undefined) return
    const card = encodeURIComponent(slug)
    // `drawn` keeps the title withheld: the trainer chose the form, and
    // naming it would answer half the question before a line is typed
    navigate(`/cards/${card}/recall/${encodeURIComponent(drew)}?drawn=1`, { replace: true })
  }, [drew, navigate, slug])

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: `/cards/${encodeURIComponent(slug)}`, label: 'the card' }}
        title="Recall a form"
      />
      <Loaded of="the form to recall" state={prompt}>
        {() => null}
      </Loaded>
    </article>
  )
}

export function RecallPage() {
  const { slug = '', template = '' } = useParams()
  const [search] = useSearchParams()
  // the trainer drew this form, so its title is the first hint rather than
  // the page's own heading
  const drawn = search.get('drawn') === '1'
  const prompt = useLoaded(
    (signal) =>
      api.GET('/api/cards/{slug}/recall/{template_slug}', {
        params: { path: { slug, template_slug: template } },
        signal,
      }),
    `recall:${slug}:${template}`,
  )

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: `/cards/${encodeURIComponent(slug)}`, label: 'the card' }}
        title={drawn ? 'Recall a form' : (prompt.data?.title ?? 'Recall a form')}
        note={
          drawn
            ? 'The trigger names the form. Type it from memory, and reach for a hint where memory fails.'
            : 'The form is withheld. Type it from memory, and reach for a hint where memory fails.'
        }
      />
      <Loaded of="the form to recall" state={prompt}>
        {(prompt) => (
          <>
            {/* withheld while the trainer drew the form: a marked title names
                the one this attempt asks for */}
            {!drawn && (
              <Templates slug={slug} current={prompt.template_slug} templates={prompt.templates} />
            )}
            <Trainer
              key={prompt.template_slug}
              slug={slug}
              templateSlug={prompt.template_slug}
              trigger={prompt.trigger}
              signature={prompt.signature}
            />
          </>
        )}
      </Loaded>
    </article>
  )
}

// every form the card teaches, so the user switches without reading the card
// again. A template no case checks is named and never asked for
function Templates({
  slug,
  current,
  templates,
}: {
  slug: string
  current: string
  templates: Named[]
}) {
  return (
    <nav className="flex flex-wrap gap-1">
      {templates.map((one) =>
        one.recallable ? (
          <Link
            key={one.slug}
            to={`/cards/${encodeURIComponent(slug)}/recall/${encodeURIComponent(one.slug)}`}
            aria-current={one.slug === current ? 'true' : undefined}
            className={cn(
              'rounded-lg px-2.5 py-1 text-meta transition-colors',
              one.slug === current
                ? 'bg-secondary text-secondary-foreground'
                : 'text-muted-foreground hover:bg-accent',
            )}
          >
            {one.title}
            {one.optional && <span className="ml-1.5 opacity-70">· optional</span>}
          </Link>
        ) : (
          <span
            key={one.slug}
            title="No case checks this form"
            className="rounded-lg px-2.5 py-1 text-meta text-muted-foreground/60"
          >
            {one.title}
            {one.optional && <span className="ml-1.5">· optional</span>}
          </span>
        ),
      )}
    </nav>
  )
}

type Props = {
  slug: string
  templateSlug: string
  trigger: string
  signature: string
}

function Trainer({ slug, templateSlug, trigger, signature }: Props) {
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
    const { data, error } = await api.GET(
      '/api/cards/{slug}/recall/{template_slug}/hints/{hint}',
      { params: { path: { slug, template_slug: templateSlug, hint: next } } },
    )
    if (data) setTaken([...taken, { hint: data.hint, text: data.text }])
    else setRefused(described(error))
  }

  async function run() {
    setRunning(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/cards/{slug}/recall/{template_slug}', {
        params: { path: { slug, template_slug: templateSlug } },
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

  if (ran !== null) return <Ran ran={ran} slug={slug} templateSlug={templateSlug} />

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
// the verdict, and the form on a press: a user who failed to recall a form
// learns which form it was and decides whether to read it
function Ran({
  ran,
  slug,
  templateSlug,
}: {
  ran: RecallAttempt
  slug: string
  templateSlug: string
}) {
  const [form, setForm] = useState<string | null>(null)

  async function reveal() {
    const { data } = await api.GET('/api/cards/{slug}/recall/{template_slug}/hints/{hint}', {
      params: { path: { slug, template_slug: templateSlug, hint: 'form' } },
    })
    if (data) setForm(data.text)
  }

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
      {form === null ? (
        <Button variant="secondary" onClick={reveal}>
          Reveal the form
        </Button>
      ) : (
        <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">{form}</pre>
      )}
      <div className="flex items-center gap-3">
        <Button asChild>
          <Link to={`/cards/${encodeURIComponent(slug)}/recall`}>Recall another</Link>
        </Button>
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
