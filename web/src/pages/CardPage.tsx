import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Gap, type Recalled, type Studied, type Template } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt } from '@/lib/format'

export function CardPage() {
  const { slug = '' } = useParams()
  const studied = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const run = studied.data?.run ?? null

  // the ladder is measured from the start, so the press is what opens a run
  async function study() {
    setStarting(true)
    setRefused(null)
    try {
      const { error } = await api.POST('/api/cards/{slug}/runs', { params: { path: { slug } } })
      if (error) setRefused(described(error))
      else studied.retry()
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setStarting(false)
    }
  }

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: '/cards', label: 'Cards' }}
        title={studied.data?.card.title ?? slug}
        note={
          studied.data &&
          [studied.data.card.technique, run && `studying since ${lastAt(run.started_at)}`]
            .filter(Boolean)
            .join(' · ')
        }
      />
      <Loaded of="the card" state={studied}>
        {(studied) => (
          <div className="space-y-section">
            <section className="space-y-1">
              <h2 className="text-heading font-medium">When to reach for it</h2>
              <p>{studied.card.trigger}</p>
            </section>
            {run === null && (
              <section className="space-y-stack">
                <div>
                  <Button onClick={study} disabled={starting}>
                    {starting ? 'Starting…' : 'Start studying this card'}
                  </Button>
                </div>
                <p className="text-meta text-muted-foreground">
                  The ladder is measured from the start, so a problem solved before it counts
                  toward nothing.
                </p>
                {refused && <p className="text-destructive">The card did not start: {refused}</p>}
              </section>
            )}
            <section>
              <Markdown>{studied.card.brief}</Markdown>
            </section>
            <LadderView studied={studied} slug={slug} />
            {run !== null && <RecallView studied={studied} />}
            {studied.probes.length > 0 && (
              <section className="space-y-1">
                <h2 className="text-heading font-medium">Probes</h2>
                <p className="text-meta text-muted-foreground">
                  Drawn at the start, and never from the ladder.
                </p>
                <ul className="space-y-1">
                  {studied.probes.map((one) => (
                    <li key={one.problem.id} className="flex flex-wrap items-baseline gap-2">
                      <Link
                        to={`/problems/${encodeURIComponent(one.problem.id)}?card=${encodeURIComponent(slug)}`}
                        className="underline-offset-4 hover:underline"
                      >
                        {one.problem.title}
                      </Link>
                      <span className="text-meta text-muted-foreground">
                        {one.attempted ? 'attempted' : 'not attempted'}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            <section className="space-y-stack">
              <h2 className="text-heading font-medium">Templates</h2>
              {studied.card.templates.map((template) => (
                <TemplateView key={template.slug} template={template} />
              ))}
            </section>
          </div>
        )}
      </Loaded>
    </article>
  )
}

// the rungs, their progress and the forms nothing covers. `content.md`: a gap
// is reported rather than filled with another problem
function LadderView({ studied, slug }: { studied: Studied; slug: string }) {
  const solved = studied.rungs.filter((one) => one.solved).length
  const titles = new Map(studied.card.templates.map((one) => [one.id, one.title]))

  return (
    <section className="space-y-stack">
      <div className="flex items-baseline justify-between">
        <h2 className="text-heading font-medium">Ladder</h2>
        <span className="text-meta text-muted-foreground">
          {studied.run
            ? `${solved} of ${studied.rungs.length} rungs solved`
            : `${studied.rungs.length} rungs`}
        </span>
      </div>
      <ul className="space-y-1">
        {studied.rungs.map((rung) => (
          <li key={rung.problem.id} className="flex flex-wrap items-baseline gap-2">
            <span aria-hidden="true" className="font-mono text-meta text-muted-foreground">
              {studied.run ? (rung.solved ? '[x]' : '[ ]') : '·'}
            </span>
            <Link
              to={`/problems/${encodeURIComponent(rung.problem.id)}?card=${encodeURIComponent(slug)}`}
              className="underline-offset-4 hover:underline"
            >
              {rung.problem.title}
            </Link>
            <span className="text-meta text-muted-foreground">
              {rung.required ? 'required' : 'optional'}
              {rung.templates.length > 0 &&
                ` · covers ${rung.templates.map((id) => titles.get(id) ?? id).join(', ')}`}
            </span>
          </li>
        ))}
      </ul>
      {studied.gaps.map((gap: Gap) => (
        <p key={gap.template_id} className="text-meta text-muted-foreground">
          No problem covers {gap.title} yet.
        </p>
      ))}
    </section>
  )
}

// the last reproduction of each form, and a row for one never recalled
function RecallView({ studied }: { studied: Studied }) {
  const titles = new Map(studied.card.templates.map((one) => [one.id, one.title]))

  return (
    <section className="space-y-1">
      <h2 className="text-heading font-medium">Recall</h2>
      <ul className="space-y-1">
        {studied.recall.map((one: Recalled) => (
          <li key={one.template_id} className="flex flex-wrap items-baseline gap-2">
            <span>{titles.get(one.template_id) ?? one.template_id}</span>
            <span className="text-meta text-muted-foreground">{reads(one)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

// a hinted pass is not a pass, so the hints read beside the moment
function reads(one: Recalled): string {
  if (one.last_at === null) return 'never recalled'
  const hints = one.hints.length === 0 ? 'no hint taken' : `${one.hints.length} hint(s)`
  return `${lastAt(one.last_at)} · ${one.verified ? 'passed' : 'failed'} · ${hints}`
}

// the code and the notes stay hidden until asked for: `content.md` gives why a
// form is worth deriving before it is read
function TemplateView({ template }: { template: Template }) {
  const [revealed, setRevealed] = useState(false)

  return (
    <div className="space-y-stack rounded-lg border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium">{template.title}</h3>
        {template.optional && <Badge variant="secondary">optional</Badge>}
        {template.kind === 'procedure' && <Badge variant="outline">procedure</Badge>}
      </div>
      <p>{template.trigger}</p>
      {revealed ? (
        <>
          <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
            {template.code}
          </pre>
          {template.notes && <Markdown>{template.notes}</Markdown>}
          <Button variant="ghost" size="sm" onClick={() => setRevealed(false)}>
            Hide
          </Button>
        </>
      ) : (
        <div className="relative">
          <pre
            aria-hidden="true"
            className="pointer-events-none max-h-40 overflow-hidden rounded-md bg-muted p-3 font-mono text-code blur-md select-none"
          >
            {template.code}
          </pre>
          <div className="absolute inset-0 flex items-center justify-center">
            <Button variant="secondary" onClick={() => setRevealed(true)}>
              Reveal the form
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
