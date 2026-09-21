import { Check, ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'

import { api, type Hint, type Named, type Prompted, type RecallAttempt } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { CodeEditor } from '@/components/CodeEditor'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { CaseStrip } from '@/components/Verdict'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { pieces } from '@/lib/python'
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
        title={
          drawn ? (
            'Recall a form'
          ) : (
            <span className="flex flex-wrap items-center gap-3">
              {prompt.data?.title ?? 'Recall a form'}
              {/* a card is covered without its optional form, so the page
                  says which kind this one is. Withheld on a drawn recall: a
                  card carries at most one optional template, and the badge
                  would name the form the trigger is asking for */}
              {optional(prompt.data) && <Badge variant="secondary">optional</Badge>}
            </span>
          )
        }
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

// whether the form this recall asks for is the card's optional one
function optional(prompt: Prompted | undefined): boolean {
  return prompt?.templates.some((one) => one.slug === prompt.template_slug && one.optional) ?? false
}

// every form the card teaches, so the user switches without reading the card
// again. A menu rather than a row of titles: six of them wrapped over four
// lines and pushed the prompt itself off the first screen
function Templates({
  slug,
  current,
  templates,
}: {
  slug: string
  current: string
  templates: Named[]
}) {
  const here = templates.find((one) => one.slug === current)

  return (
    <div className="flex flex-wrap items-center gap-2 text-meta text-muted-foreground">
      Recalling
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm">
            {here?.title ?? 'a form'}
            <ChevronDown />
          </Button>
        </DropdownMenuTrigger>
        {/* the copy sizes a menu to its trigger, which clipped the longer
            titles: this one sizes to them, and never past the reading column */}
        <DropdownMenuContent
          align="start"
          className="w-auto min-w-(--radix-dropdown-menu-trigger-width) max-w-[min(90vw,var(--container-form))]"
        >
          {templates.map((one) =>
            one.recallable ? (
              <DropdownMenuItem key={one.slug} asChild>
                <Link
                  to={`/cards/${encodeURIComponent(slug)}/recall/${encodeURIComponent(one.slug)}`}
                  aria-current={one.slug === current ? 'true' : undefined}
                >
                  <Check className={cn(one.slug !== current && 'invisible')} />
                  <span className="flex-1 whitespace-nowrap">{one.title}</span>
                  {one.optional && <span className="text-muted-foreground">optional</span>}
                </Link>
              </DropdownMenuItem>
            ) : (
              // named and never asked for: no case checks a reproduction of it
              <DropdownMenuItem key={one.slug} disabled>
                <Check className="invisible" />
                <span className="flex-1 whitespace-nowrap">{one.title}</span>
                <span className="text-muted-foreground">no cases</span>
              </DropdownMenuItem>
            ),
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
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
      <Panel>
        <p className="text-meta text-muted-foreground">When to reach for it</p>
        <p>{trigger}</p>
      </Panel>

      {taken.map((one) => (
        <div key={one.hint} className="overflow-hidden rounded-xl border">
          <p className="border-b bg-card px-4 py-2 text-meta text-muted-foreground">
            Hint taken: {NAMES[one.hint]}
          </p>
          <div className="px-4 py-3">
            {one.hint === 'form' ? (
              <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
                <code>
                  {pieces(one.text).map((piece, index) => (
                    <span key={index} className={piece.token}>
                      {piece.text}
                    </span>
                  ))}
                </code>
              </pre>
            ) : (
              <Markdown>{one.text}</Markdown>
            )}
          </div>
        </div>
      ))}

      <section className="space-y-stack">
        <div className="h-96">
          {/* the signature, and the file otherwise blank: `corpus.md` gives why
              the parameter order is stated rather than inferred */}
          <CodeEditor initial={blank} onChange={(typed) => (code.current = typed)} onSubmit={run} />
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <Button onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run'}
          </Button>
          <span className="text-meta text-muted-foreground">⌘/Ctrl + Enter</span>
          {/* the ladder, so the reader sees what a hint costs before taking
              it: each one answers more of the question than the last */}
          <span className="ml-auto flex items-center gap-2 text-meta text-muted-foreground">
            {LADDER.map((one) => (
              <span key={one} className={cn(taken.some((each) => each.hint === one) && 'line-through')}>
                {NAMES[one]}
              </span>
            ))}
            {next !== undefined && (
              <Button variant="outline" size="sm" onClick={hint}>
                Take: {NAMES[next]}
              </Button>
            )}
          </span>
        </div>
        {refused && <p className="text-meta text-destructive">The recall did not run: {refused}</p>}
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

  const results = ran.results ?? []
  const hints = ran.hints ?? []

  return (
    <div className="space-y-section">
      <Panel>
        <p
          className={cn('font-medium', verified(ran) ? 'text-verdict-passed' : 'text-verdict-wrong')}
        >
          {verified(ran) ? 'Recalled' : 'Not recalled'}: {passed(ran)} of {results.length} cases
          passed
        </p>
        {failures(results).length > 0 && (
          <p className="text-meta text-muted-foreground">{failures(results).join(' · ')}</p>
        )}
        <CaseStrip results={results} />
        {/* a hinted pass is a pass with its hints, which the record keeps */}
        <p className="text-meta text-muted-foreground">
          {hints.length === 0
            ? 'Recalled cold, with no hint taken.'
            : `Taken on the way: ${hints.map((one) => NAMES[one]).join(', ')}.`}
        </p>
      </Panel>

      {/* the form on a press: a user who failed to recall it learns which form
          it was and decides whether to read it */}
      <section className="space-y-stack">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-heading font-medium">The form</h2>
          {form === null && (
            <Button variant="outline" size="sm" onClick={reveal}>
              Reveal the form
            </Button>
          )}
        </div>
        {form === null ? (
          <p className="rounded-md border border-dashed px-3 py-2 text-meta text-muted-foreground">
            The form is still hidden.
          </p>
        ) : (
          <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
            <code>
              {pieces(form).map((piece, index) => (
                <span key={index} className={piece.token}>
                  {piece.text}
                </span>
              ))}
            </code>
          </pre>
        )}
      </section>

      <div className="flex flex-wrap items-center gap-3">
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
