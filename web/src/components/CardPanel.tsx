import { Link } from 'react-router'

import type { ListedCard } from '@/api/client'
import { ProgressBar } from '@/components/ProgressBar'
import { lastAt, plain } from '@/lib/format'
import { cn } from '@/lib/utils'

// every block is the same panel: a family several cards teach carries a
// header naming it, and the cards that teach a family of their own carry the
// name on the row instead
export function CardPanel({ technique, cards }: { technique: string | null; cards: ListedCard[] }) {
  return (
    <section className="overflow-hidden rounded-xl border">
      {technique && (
        <div className="flex items-baseline gap-3 border-b bg-card px-4 py-3">
          {/* a header naming a record opens it */}
          <h2 className="font-mono text-heading font-medium">
            <Link
              to={`/techniques/${encodeURIComponent(technique)}`}
              className="underline-offset-4 hover:underline"
            >
              {technique}
            </Link>
          </h2>
          <span className="ml-auto text-meta text-muted-foreground">{cards.length} cards</span>
        </div>
      )}
      <div className="divide-y divide-border">
        {cards.map((card) => (
          <CardRow key={card.slug} card={card} named={card.technique !== technique} />
        ))}
      </div>
    </section>
  )
}

// `named` carries the technique on the row wherever no heading names it: a
// card that stands alone, or a narrower technique under its family's heading
function CardRow({ card, named = false }: { card: ListedCard; named?: boolean }) {
  const optional = card.templates.filter((one) => one.optional).length
  const { status } = card

  return (
    <Link
      to={`/cards/${encodeURIComponent(card.slug)}`}
      className="group block px-4 py-3 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline gap-3">
        <span className="font-medium underline-offset-4 group-hover:underline">{card.title}</span>
        {named && (
          <span className="font-mono text-meta text-muted-foreground">{card.technique}</span>
        )}
        <span className="ml-auto shrink-0 text-meta text-muted-foreground tabular-nums">
          {status.started_at ? lastAt(status.last_at) : templates(card.templates.length, optional)}
        </span>
      </div>
      {status.started_at ? (
        // a started card was already chosen, so its progress replaces the
        // trigger it was chosen by
        <>
          <p className="mt-1 text-meta text-muted-foreground tabular-nums">
            started {new Date(status.started_at).toLocaleDateString()} · ladder {status.solved}/
            {status.rungs}, required {status.required_solved}/{status.required}
            {status.gaps > 0 && ` · ${uncovered(status.gaps)}`}
          </p>
          <div className="mt-2 max-w-xs">
            <ProgressBar value={status.solved} total={status.rungs} label="Rungs solved" />
          </div>
        </>
      ) : (
        // the trigger says when to reach for the technique, which is what a
        // reader picks a card by
        <p className="mt-1 line-clamp-2 text-meta text-muted-foreground">{plain(card.trigger)}</p>
      )}
      <RecallMarks card={card} />
    </Link>
  )
}

// one mark per template in the card's order: the last recall of each form
function RecallMarks({ card }: { card: ListedCard }) {
  const recalled = new Map(card.status.recall.map((one) => [one.template_id, one]))
  return (
    <p className="mt-1 flex items-center gap-1.5 text-meta text-muted-foreground">
      recall
      {card.templates.map((template) => {
        const [mark, reading] = recallMark(template.cases?.length ?? 0, recalled.get(template.id))
        return (
          <span
            key={template.id}
            title={`${template.title}: ${reading}`}
            // a pass and a fail read in the verdict's own colours, which mean
            // the same outcome here; a hinted pass and no recall stay grey
            className={cn(
              'font-mono',
              mark === '✓' && 'text-verdict-passed',
              mark === '✗' && 'text-verdict-wrong',
            )}
          >
            {mark}
          </span>
        )
      })}
    </p>
  )
}

function recallMark(
  cases: number,
  last: ListedCard['status']['recall'][number] | undefined,
): [string, string] {
  // a template no case checks is read on the card and never recalled
  if (cases === 0) return ['-', 'read, not recalled']
  if (!last?.last_at) return ['·', 'never recalled']
  if (!last.verified) return ['✗', 'failed']
  return last.hints.length > 0 ? ['◐', 'passed with hints'] : ['✓', 'recalled clean']
}

function uncovered(gaps: number): string {
  return gaps === 1 ? '1 form uncovered' : `${gaps} forms uncovered`
}

function templates(count: number, optional: number): string {
  const all = count === 1 ? '1 template' : `${count} templates`
  return optional === 0 ? all : `${all}, ${optional} optional`
}
