import { ChevronDown } from 'lucide-react'
import { type ReactNode, useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Gap, type Recalled, type Studied, type Template } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { Panel, Stat, Stats } from '@/components/Panel'
import { SectionBar } from '@/components/SectionBar'
import { TemplatePanel } from '@/components/TemplatePanel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt } from '@/lib/format'
import { type Item, useCurrent } from '@/lib/sections'
import { cn } from '@/lib/utils'

export function CardPage() {
  const { slug = '' } = useParams()
  const studied = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  // a section the reader closed, by id. Nothing is closed until they close
  // it, and a reload opens every one again
  const [closed, setClosed] = useState<string[]>([])
  const run = studied.data?.run ?? null
  const data = studied.data
  const items: Item[] = [
    { id: 'trigger', label: 'When to reach for it' },
    { id: 'brief', label: 'The brief' },
    { id: 'ladder', label: 'Ladder' },
    ...(run ? [{ id: 'recall', label: 'Recall' }] : []),
    ...(data && data.probes.length > 0 ? [{ id: 'probes', label: 'Probes' }] : []),
    { id: 'templates', label: 'Templates' },
  ]
  const current = useCurrent(items.map((item) => item.id))

  function toggle(id: string) {
    setClosed(closed.includes(id) ? closed.filter((one) => one !== id) : [...closed, id])
  }

  // a jump opens the section first: scrolling to a closed one lands on its
  // heading with nothing under it
  function jump(id: string) {
    setClosed(closed.filter((one) => one !== id))
    requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }))
  }

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
            {/* what studying this card has reached, or the press that starts
                measuring it: the ladder counts the attempts made after it */}
            {studied.run ? (
              <Progress studied={studied} />
            ) : (
              <Start onStart={study} starting={starting} refused={refused} />
            )}

            <SectionBar items={items} current={current} onJump={jump} />

            <Section
              id="trigger"
              title="When to reach for it"
              closed={closed.includes('trigger')}
              onToggle={toggle}
            >
              {/* authored as markdown, as the brief and the notes are */}
              <Markdown>{studied.card.trigger}</Markdown>
            </Section>

            <Section
              id="brief"
              title="The brief"
              closed={closed.includes('brief')}
              onToggle={toggle}
            >
              <Markdown>{studied.card.brief}</Markdown>
            </Section>

            <LadderView
              studied={studied}
              slug={slug}
              closed={closed.includes('ladder')}
              onToggle={toggle}
            />
            {studied.run && (
              <RecallView
                studied={studied}
                closed={closed.includes('recall')}
                onToggle={toggle}
              />
            )}
            {studied.probes.length > 0 && (
              <ProbesView
                studied={studied}
                slug={slug}
                closed={closed.includes('probes')}
                onToggle={toggle}
              />
            )}

            <Section
              id="templates"
              title="Templates"
              aside={countOf(studied.card.templates.length, 'template')}
              closed={closed.includes('templates')}
              onToggle={toggle}
            >
              <div className="space-y-stack">
                {studied.card.templates.map((template) => (
                  <TemplatePanel key={template.slug} template={template} />
                ))}
              </div>
            </Section>
          </div>
        )}
      </Loaded>
    </article>
  )
}

// the three folds a run makes readable, as counts: the ladder's progress, the
// forms recalled, and the probes the start drew
function Progress({ studied }: { studied: Studied }) {
  const solved = studied.rungs.filter((one) => one.solved).length
  const recalled = studied.recall.filter((one) => one.last_at !== null).length

  return (
    <Panel>
      <Stats>
        <Stat value={`${solved}/${studied.rungs.length}`} label="rungs solved" />
        <Stat value={`${recalled}/${studied.card.templates.length}`} label="forms recalled" />
        <Stat value={studied.probes.length} label="probes drawn" />
        <Button variant="outline" size="sm" className="ml-auto" asChild>
          <Link to={`/cards/${encodeURIComponent(studied.card.slug)}/recall`}>Recall a form</Link>
        </Button>
      </Stats>
    </Panel>
  )
}

function Start({
  onStart,
  starting,
  refused,
}: {
  onStart: () => void
  starting: boolean
  refused: string | null
}) {
  return (
    <Panel>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <p className="text-meta text-muted-foreground">
          The ladder is measured from the start, so a problem solved before it counts toward
          nothing.
        </p>
        <Button className="ml-auto" onClick={onStart} disabled={starting}>
          {starting ? 'Starting…' : 'Start studying this card'}
        </Button>
      </div>
      {refused && <p className="text-meta text-destructive">The card did not start: {refused}</p>}
    </Panel>
  )
}

// the rungs, their progress and the forms nothing covers. `content.md`: a gap
// is reported rather than filled with another problem
function LadderView({
  studied,
  slug,
  closed,
  onToggle,
}: {
  studied: Studied
  slug: string
  closed: boolean
  onToggle: (id: string) => void
}) {
  const solved = studied.rungs.filter((one) => one.solved).length
  const titles = new Map(studied.card.templates.map((one) => [one.id, one.title]))

  return (
    <Section
      id="ladder"
      title="Ladder"
      closed={closed}
      onToggle={onToggle}
      aside={
        studied.run
          ? `${solved} of ${studied.rungs.length} solved`
          : countOf(studied.rungs.length, 'rung')
      }
    >
      <div className="divide-y divide-border">
        {studied.rungs.map((rung) => (
          <Link
            key={rung.problem.id}
            to={`/problems/${encodeURIComponent(rung.problem.id)}?card=${encodeURIComponent(slug)}`}
            className="group -mx-3 flex items-baseline gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-accent"
          >
            {studied.run && <Mark solved={rung.solved} />}
            <span className="min-w-0">
              <span className="font-medium underline-offset-4 group-hover:underline">
                {rung.problem.title}
              </span>
              {rung.templates.length > 0 && (
                <span className="block text-meta text-muted-foreground">
                  covers {rung.templates.map((id) => titles.get(id) ?? id).join(', ')}
                </span>
              )}
            </span>
            <span className="ml-auto shrink-0 text-meta text-muted-foreground">
              {rung.required ? 'required' : 'optional'}
            </span>
          </Link>
        ))}
        {studied.gaps.map((gap: Gap) => (
          <p
            key={gap.template_id}
            className="flex items-baseline gap-3 py-3 text-meta text-muted-foreground"
          >
            No problem covers {gap.title} yet.
            <Badge variant="outline" className="ml-auto font-normal">
              gap
            </Badge>
          </p>
        ))}
      </div>
    </Section>
  )
}

// solved is folded from the attempts made since the run began, so the box is
// a reading rather than a control
function Mark({ solved }: { solved: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={
        solved
          ? 'size-4 shrink-0 self-center rounded-sm bg-foreground text-background'
          : 'size-4 shrink-0 self-center rounded-sm border'
      }
    >
      {solved && (
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M4 8.5l2.5 2.5L12 5.5" />
        </svg>
      )}
    </span>
  )
}

// the last reproduction of each form, and a row for one never recalled. Each
// row starts the recall of its own form, since a card teaches several and the
// draw reaches one of them at a time
function RecallView({
  studied,
  closed,
  onToggle,
}: {
  studied: Studied
  closed: boolean
  onToggle: (id: string) => void
}) {
  const templates = new Map(studied.card.templates.map((one) => [one.id, one]))

  return (
    <Section id="recall" title="Recall" closed={closed} onToggle={onToggle}>
      <div className="divide-y divide-border">
        {studied.recall.map((one: Recalled) => (
          <RecallRow
            key={one.template_id}
            slug={studied.card.slug}
            template={templates.get(one.template_id)}
            recalled={one}
          />
        ))}
      </div>
    </Section>
  )
}

function RecallRow({
  slug,
  template,
  recalled,
}: {
  slug: string
  template: Template | undefined
  recalled: Recalled
}) {
  const title = template?.title ?? recalled.template_id

  // `content.md`: a template no case checks is read on the card and never
  // recalled, so its row opens nothing
  if (!template || (template.cases ?? []).length === 0)
    return (
      <div className="flex flex-wrap items-baseline gap-3 py-3">
        <span>{title}</span>
        {template?.optional && <Badge variant="secondary">optional</Badge>}
        <span className="ml-auto text-meta text-muted-foreground">
          no case checks this form
        </span>
      </div>
    )

  return (
    <Link
      to={`/cards/${encodeURIComponent(slug)}/recall/${encodeURIComponent(template.slug)}`}
      className="group -mx-3 flex flex-wrap items-baseline gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-accent"
    >
      <span className="underline-offset-4 group-hover:underline">{title}</span>
      {template.optional && <Badge variant="secondary">optional</Badge>}
      <span className="ml-auto text-meta text-muted-foreground">{reads(recalled)}</span>
    </Link>
  )
}

// drawn at the start and never from the ladder, so they read apart from it
function ProbesView({
  studied,
  slug,
  closed,
  onToggle,
}: {
  studied: Studied
  slug: string
  closed: boolean
  onToggle: (id: string) => void
}) {
  return (
    <Section
      id="probes"
      title="Probes"
      aside="drawn at the start, never from the ladder"
      closed={closed}
      onToggle={onToggle}
    >
      <div className="divide-y divide-border">
        {studied.probes.map((one) => (
          <Link
            key={one.problem.id}
            to={`/problems/${encodeURIComponent(one.problem.id)}?card=${encodeURIComponent(slug)}`}
            className="group -mx-3 flex items-baseline gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-accent"
          >
            <span className="font-medium underline-offset-4 group-hover:underline">
              {one.problem.title}
            </span>
            <span className="ml-auto shrink-0 text-meta text-muted-foreground">
              {one.attempted ? 'attempted' : 'not attempted'}
            </span>
          </Link>
        ))}
      </div>
    </Section>
  )
}

// the heading is the press that closes its own section, and the bar above
// reaches every one of them by id
function Section({
  id,
  title,
  aside,
  closed,
  onToggle,
  children,
}: {
  id: string
  title: string
  aside?: string
  closed: boolean
  onToggle: (id: string) => void
  children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-16 space-y-stack">
      <div className="flex items-baseline justify-between gap-3">
        <button
          type="button"
          onClick={() => onToggle(id)}
          aria-expanded={!closed}
          className="flex items-baseline gap-2 text-heading font-medium"
        >
          <ChevronDown
            aria-hidden="true"
            className={cn('size-4 self-center transition-transform', closed && '-rotate-90')}
          />
          {title}
        </button>
        {aside && <span className="text-meta text-muted-foreground">{aside}</span>}
      </div>
      {!closed && children}
    </section>
  )
}

function countOf(count: number, noun: string): string {
  return count === 1 ? `1 ${noun}` : `${count} ${noun}s`
}

// a hinted pass is not a pass, so the hints read beside the moment
function reads(one: Recalled): string {
  if (one.last_at === null) return 'never recalled'
  const hints = one.hints.length === 0 ? 'no hint taken' : countOf(one.hints.length, 'hint')
  return `${lastAt(one.last_at)} · ${one.verified ? 'passed' : 'failed'} · ${hints}`
}
