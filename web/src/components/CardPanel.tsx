import type { RecallMark } from '@algo-coach/core'
import { Link } from 'react-router'

import type { ListedCard } from '@/api/client'
import { ProgressBar } from '@/components/ProgressBar'
import { cardRow } from '@/lib/format'
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
          <CardRow key={card.slug} card={card} heading={technique} />
        ))}
      </div>
    </section>
  )
}

function CardRow({ card, heading }: { card: ListedCard; heading: string | null }) {
  const row = cardRow(card, heading)

  return (
    <Link
      to={`/cards/${encodeURIComponent(card.slug)}`}
      className="group block px-4 py-3 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline gap-3">
        <span className="font-medium underline-offset-4 group-hover:underline">{row.title}</span>
        {row.technique && (
          <span className="font-mono text-meta text-muted-foreground">{row.technique}</span>
        )}
        <span className="ml-auto shrink-0 text-meta text-muted-foreground tabular-nums">
          {row.aside}
        </span>
      </div>
      {row.state !== null && (
        <p className="mt-1 text-meta text-muted-foreground tabular-nums">{row.state}</p>
      )}
      {row.progress && (
        <div className="mt-2 max-w-xs">
          <ProgressBar value={row.progress.solved} total={row.progress.rungs} label="Rungs solved" />
        </div>
      )}
      {row.trigger !== null && (
        <p className="mt-1 line-clamp-2 text-meta text-muted-foreground">{row.trigger}</p>
      )}
      <RecallMarks marks={row.recall} />
    </Link>
  )
}

function RecallMarks({ marks }: { marks: RecallMark[] }) {
  return (
    <p className="mt-1 flex items-center gap-1.5 text-meta text-muted-foreground">
      recall
      {marks.map((one) => (
        <span
          key={one.templateId}
          title={`${one.title}: ${one.reading}`}
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
