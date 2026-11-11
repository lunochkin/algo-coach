import {
  LADDER_GAP,
  LADDER_TITLE,
  ladderView,
  PROBES_ASIDE,
  PROBES_TITLE,
  RECALL_TITLE,
  probeState,
  RUN_START_NOTE,
  runStartLabel,
  runStartRefused,
} from '@algo-coach/core'
import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Studied } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { PickList, PickRow } from '@/components/PickRow'
import { Panel, Stat, Stats } from '@/components/Panel'
import { PageSection as Section } from '@/components/PageSection'
import { SectionBar } from '@/components/SectionBar'
import { TemplatePanel } from '@/components/TemplatePanel'
import { ProgressBar } from '@/components/ProgressBar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt } from '@/lib/format'
import { type Item, useSections } from '@/lib/sections'

export function CardPage() {
  const { slug = '' } = useParams()
  const studied = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const run = studied.data?.run ?? null
  const data = studied.data
  const items: Item[] = [
    { id: 'trigger', label: 'When to reach for it' },
    { id: 'brief', label: 'The brief' },
    { id: 'ladder', label: 'Ladder' },
    ...(data && data.probes.length > 0 ? [{ id: 'probes', label: 'Probes' }] : []),
    { id: 'templates', label: 'Templates' },
  ]
  const { current, closed, toggle, jump } = useSections(items)

  // the ladder is measured from the start, so the press is what opens a run
  async function study() {
    setStarting(true)
    setRefused(null)
    try {
      const { error } = await api.POST('/api/cards/{slug}/runs', {
        params: { path: { slug } },
      })
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
        {(studied) => {
          // the recall of each form, read on the form itself
          const recall = new Map(studied.recall.map((one) => [one.template_id, one]))

          return (
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
                closed={closed('trigger')}
                onToggle={toggle}
              >
                {/* authored as markdown, as the brief and the notes are */}
                <Markdown>{studied.card.trigger}</Markdown>
              </Section>

              <Section id="brief" title="The brief" closed={closed('brief')} onToggle={toggle}>
                <Markdown>{studied.card.brief}</Markdown>
              </Section>

              <LadderView
                studied={studied}
                slug={slug}
                closed={closed('ladder')}
                onToggle={toggle}
              />
              {studied.probes.length > 0 && (
                <ProbesView
                  studied={studied}
                  slug={slug}
                  closed={closed('probes')}
                  onToggle={toggle}
                />
              )}

              <Section
                id="templates"
                title="Templates"
                count={studied.card.templates.length}
                body="bare"
                closed={closed('templates')}
                onToggle={toggle}
              >
                <div className="space-y-stack">
                  {studied.card.templates.map((template) => (
                    <TemplatePanel
                      key={template.slug}
                      template={template}
                      card={studied.card.slug}
                      recalled={recall.get(template.id)}
                    />
                  ))}
                </div>
              </Section>
            </div>
          )
        }}
      </Loaded>
    </article>
  )
}

// the three folds a run makes readable, as counts: the ladder's progress, the
// forms recalled, and the probes the start drew
function Progress({ studied }: { studied: Studied }) {
  const solved = studied.rungs.filter((one) => one.solved).length
  const recalled = studied.recall.filter((one) => one.last_at !== null).length
  // the next rung: the first unsolved required one, else the first unsolved,
  // each in the ladder's order. None once every rung is solved
  const open = studied.rungs.filter((one) => !one.solved)
  const next = open.find((one) => one.required) ?? open[0]

  return (
    <Panel>
      <Stats>
        <Stat value={`${solved}/${studied.rungs.length}`} label="rungs solved" />
        <Stat value={`${recalled}/${studied.card.templates.length}`} label="forms recalled" />
        <Stat value={studied.probes.length} label="probes drawn" />
        <Button variant="outline" size="sm" className="ml-auto" asChild>
          <Link to={`/cards/${encodeURIComponent(studied.card.slug)}/recall`}>{RECALL_TITLE}</Link>
        </Button>
        {next && (
          <Button size="sm" asChild>
            <Link
              to={`/problems/${encodeURIComponent(next.problem.id)}?card=${encodeURIComponent(studied.card.slug)}`}
            >
              Next rung: {next.problem.title}
            </Link>
          </Button>
        )}
      </Stats>
      {/* the ladder's progress, drawn as the cards list draws it */}
      <ProgressBar value={solved} total={studied.rungs.length} label="Rungs solved" />
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
        <p className="text-meta text-muted-foreground">{RUN_START_NOTE}</p>
        <Button className="ml-auto" onClick={onStart} disabled={starting}>
          {runStartLabel(starting)}
        </Button>
      </div>
      {refused && <p className="text-meta text-destructive">{runStartRefused(refused)}</p>}
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
  const view = ladderView(studied)
  return (
    <Section
      id="ladder"
      body="rows"
      title={LADDER_TITLE}
      closed={closed}
      onToggle={onToggle}
      count={view.count}
      aside={view.aside}
    >
      <PickList>
        {view.rows.map((rung) => (
          <PickRow
            key={rung.problemId}
            to={`/problems/${encodeURIComponent(rung.problemId)}?card=${encodeURIComponent(slug)}`}
            lead={rung.solved !== null && <Mark solved={rung.solved} />}
            title={rung.title}
            badge={
              rung.difficulty && (
                <Badge variant="outline" className="font-normal">
                  {rung.difficulty}
                </Badge>
              )
            }
            note={rung.covers}
            stats={[{ label: '', value: rung.need }]}
          />
        ))}
        {view.gaps.map((gap) => (
          <p
            key={gap}
            className="flex items-baseline gap-3 px-4 py-3 text-meta text-muted-foreground"
          >
            {gap}
            <Badge variant="outline" className="ml-auto font-normal">
              {LADDER_GAP}
            </Badge>
          </p>
        ))}
      </PickList>
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
      body="rows"
      title={PROBES_TITLE}
      count={studied.probes.length}
      aside={PROBES_ASIDE}
      closed={closed}
      onToggle={onToggle}
    >
      <PickList>
        {studied.probes.map((one) => (
          <PickRow
            key={one.problem.id}
            to={`/problems/${encodeURIComponent(one.problem.id)}?card=${encodeURIComponent(slug)}`}
            title={one.problem.title}
            badge={
              one.problem.difficulty && (
                <Badge variant="outline" className="font-normal">
                  {one.problem.difficulty}
                </Badge>
              )
            }
            stats={[{ label: '', value: probeState(one.attempted) }]}
          />
        ))}
      </PickList>
    </Section>
  )
}
