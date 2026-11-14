import { RUNGS_SOLVED, cardsCounted, RECALL_MARKS, recallMarkLabel } from '@climb/core'
import type { RecallMark } from '@climb/core'
import { Link } from 'react-router'

import type { ListedCard } from '@/api/client'
import { PanelStrip } from '@/components/Panel'
import { PickList, PickRow } from '@/components/PickRow'
import { cardRow } from '@/lib/format'
import { cn } from '@/lib/utils'

// every block is the same panel: a family several cards teach carries a
// header naming it, and the cards that teach a family of their own carry the
// name on the row instead
export function CardPanel({
  technique,
  cards,
  onHover,
}: {
  technique: string | null
  cards: ListedCard[]
  // the card graph's gutter brightens the edges of the row under the pointer
  onHover?: (slug: string | null) => void
}) {
  return (
    <section className="overflow-hidden rounded-xl border bg-card">
      {technique && (
        <PanelStrip>
          {/* a header naming a record opens it */}
          <h2 className="font-mono text-heading font-medium">
            <Link
              to={`/techniques/${encodeURIComponent(technique)}`}
              className="underline-offset-4 hover:underline"
            >
              {technique}
            </Link>
          </h2>
          <span className="ml-auto text-meta text-muted-foreground">
            {cardsCounted(cards.length)}
          </span>
        </PanelStrip>
      )}
      <PickList>
        {cards.map((card) => (
          // `data-card` is where the graph's gutter reads a row's position
          <div
            key={card.slug}
            data-card={card.slug}
            onMouseEnter={onHover && (() => onHover(card.slug))}
            onMouseLeave={onHover && (() => onHover(null))}
          >
            <CardRow card={card} heading={technique} />
          </div>
        ))}
      </PickList>
    </section>
  )
}

function CardRow({ card, heading }: { card: ListedCard; heading: string | null }) {
  const row = cardRow(card, heading)
  return (
    <PickRow
      to={`/cards/${encodeURIComponent(card.slug)}`}
      title={row.title}
      badge={
        row.technique && (
          <span className="font-mono text-meta text-muted-foreground">{row.technique}</span>
        )
      }
      stats={[{ label: '', value: row.aside }]}
      dim={row.waits !== null}
      note={row.state}
      progress={
        row.progress && {
          value: row.progress.solved,
          total: row.progress.rungs,
          label: RUNGS_SOLVED,
        }
      }
    >
      {row.waits !== null && <p className="mt-1 text-meta text-muted-foreground">{row.waits}</p>}
      {row.trigger !== null && (
        <p className="mt-1 line-clamp-2 text-meta text-muted-foreground">{row.trigger}</p>
      )}
      <RecallMarks marks={row.recall} />
    </PickRow>
  )
}

function RecallMarks({ marks }: { marks: RecallMark[] }) {
  return (
    <p className="mt-1 flex items-center gap-1.5 text-meta text-muted-foreground">
      {RECALL_MARKS}
      {marks.map((one) => (
        <span
          key={one.templateId}
          title={recallMarkLabel(one)}
          className={cn(
            'font-mono',
            one.tone === 'passed' && 'text-verdict-passed',
            one.tone === 'wrong' && 'text-verdict-wrong',
          )}
        >
          {one.mark}
        </span>
      ))}
    </p>
  )
}
