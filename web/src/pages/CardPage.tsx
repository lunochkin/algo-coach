import {
  LADDER_GAP,
  LADDER_TITLE,
  ladderView,
  PROBES_ASIDE,
  PROBES_TITLE,
  RECALL_TITLE,
  probeState,
  RUN_START_NOTE,
  runLock,
  runStartLabel,
  runStartRefused,
  CARD_TRIGGER,
  briefParts,
  CARD_TEMPLATES,
  BACK_CARDS,
  OF,
  RUNGS_SOLVED,
  FORMS_RECALLED,
  PROBES_DRAWN,
  nextRung,
  cardNote,
  cardProgress,
  cardSections,
  startCardRun,
  judgeFrom,
} from '@climb/core'
import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Studied } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { ErrorLine } from '@/components/ErrorLine'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { PickList, PickRow } from '@/components/PickRow'
import { Panel, Stat, Stats } from '@/components/Panel'
import { PageSection as Section } from '@/components/PageSection'
import { SectionBar } from '@/components/SectionBar'
import { TemplatePanel } from '@/components/TemplatePanel'
import { ProgressBar } from '@/components/ProgressBar'
import { Tag } from '@/components/Tag'
import { Button } from '@/components/ui/button'
import { useSections } from '@/lib/sections'

export function CardPage() {
  // the moment the page opened, which a run's age is read at
  const [now] = useState(() => Date.now())
  const { slug = '' } = useParams()
  const studied = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )
  const [starting, setStarting] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const data = studied.data
  const items = cardSections(data)
  const { current, closed, toggle, jump } = useSections(items)

  // the ladder is measured from the start, so the press is what opens a run
  async function study() {
    setStarting(true)
    setRefused(null)
    const started = await startCardRun(api, slug)
    setStarting(false)
    if (started.ok) studied.retry()
    else setRefused(started.refused)
  }

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: '/cards', label: BACK_CARDS }}
        title={studied.data?.card.title ?? slug}
        note={studied.data && cardNote(studied.data, now)}
      />
      <Loaded of={OF.card} state={studied}>
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
                <Start
                  onStart={study}
                  starting={starting}
                  refused={refused}
                  lock={runLock(studied.waiting)}
                />
              )}

              <Link
                to={`/judge?card=${encodeURIComponent(slug)}`}
                className="text-meta underline-offset-4 hover:underline"
              >
                {judgeFrom(studied.card.title)}
              </Link>

              <SectionBar items={items} current={current} onJump={jump} />

              <Section
                id="trigger"
                title={CARD_TRIGGER}
                closed={closed('trigger')}
                onToggle={toggle}
              >
                {/* authored as markdown, as the brief and the notes are */}
                <Markdown>{studied.card.trigger}</Markdown>
              </Section>

              {briefParts(studied.card.brief).map((part) => (
                <Section
                  key={part.id}
                  id={part.id}
                  title={part.title}
                  closed={closed(part.id)}
                  onToggle={toggle}
                >
                  <Markdown>{part.text}</Markdown>
                </Section>
              ))}

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
                title={CARD_TEMPLATES}
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
  const { solved, rungs, recalled, forms, probes, next, recallable } = cardProgress(studied)

  return (
    <Panel>
      <Stats>
        <Stat value={`${solved}/${rungs}`} label={RUNGS_SOLVED} />
        <Stat value={`${recalled}/${forms}`} label={FORMS_RECALLED} />
        <Stat value={probes} label={PROBES_DRAWN} />
        {/* a recall is offered where some form carries the cases that check it */}
        {recallable && (
          <Button variant="outline" size="sm" className="ml-auto" asChild>
            <Link to={`/cards/${encodeURIComponent(studied.card.slug)}/recall`}>
              {RECALL_TITLE}
            </Link>
          </Button>
        )}
        {next && (
          <Button asChild>
            <Link
              to={`/problems/${encodeURIComponent(next.problemId)}?card=${encodeURIComponent(studied.card.slug)}`}
            >
              {nextRung(next.title)}
            </Link>
          </Button>
        )}
      </Stats>
      {/* the ladder's progress, drawn as the cards list draws it */}
      <ProgressBar value={solved} total={rungs} label={RUNGS_SOLVED} />
    </Panel>
  )
}

// a locked card reads the cards it waits on in place of the start note, and
// its press stays disabled until they are met
function Start({
  onStart,
  starting,
  refused,
  lock,
}: {
  onStart: () => void
  starting: boolean
  refused: string | null
  lock: string | null
}) {
  return (
    <Panel>
      <div className="flex flex-wrap items-center gap-stack">
        <p className="text-meta text-muted-foreground">{lock ?? RUN_START_NOTE}</p>
        <Button onClick={onStart} disabled={starting || lock !== null}>
          {runStartLabel(starting, lock !== null)}
        </Button>
      </div>
      {refused && <ErrorLine>{runStartRefused(refused)}</ErrorLine>}
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
            badge={rung.difficulty && <Tag>{rung.difficulty}</Tag>}
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
            <Tag className="ml-auto">{LADDER_GAP}</Tag>
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
            badge={one.problem.difficulty && <Tag>{one.problem.difficulty}</Tag>}
            stats={[{ label: '', value: probeState(one.attempted) }]}
          />
        ))}
      </PickList>
    </Section>
  )
}
