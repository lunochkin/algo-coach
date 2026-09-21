import { Link } from 'react-router'

import { api, type Card } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { plain } from '@/lib/format'

export function CardsPage() {
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  return (
    <section className="space-y-section">
      <PageHeader
        title="Cards"
        note="One card teaches one technique: when to reach for it, and the forms to reproduce from memory."
      />
      <Loaded of="the cards" state={cards} blank="No card is seeded yet.">
        {(cards) => (
          <div className="space-y-section">
            {blocks(cards).map((block) => (
              <Panel
                key={'technique' in block ? block.technique : block.cards[0].slug}
                technique={'technique' in block ? block.technique : null}
                cards={block.cards}
              />
            ))}
          </div>
        )}
      </Loaded>
    </section>
  )
}

// every block is the same panel: a technique several cards teach carries a
// header naming it, and the cards that teach a technique of their own carry
// the name on the row instead
function Panel({ technique, cards }: { technique: string | null; cards: Card[] }) {
  return (
    <section className="overflow-hidden rounded-xl border">
      {technique && (
        <div className="flex items-baseline gap-3 border-b bg-card px-4 py-3">
          <h2 className="font-mono text-heading font-medium">{technique}</h2>
          <span className="ml-auto text-meta text-muted-foreground">{cards.length} cards</span>
        </div>
      )}
      <div className="divide-y divide-border px-4">
        {cards.map((card) => (
          <CardRow key={card.slug} card={card} named={technique === null} />
        ))}
      </div>
    </section>
  )
}

// `named` carries the technique on the row, for a card that stands alone:
// only a group of cards has a heading to carry it instead
function CardRow({ card, named = false }: { card: Card; named?: boolean }) {
  const optional = card.templates.filter((one) => one.optional).length

  return (
    <Link
      to={`/cards/${encodeURIComponent(card.slug)}`}
      className="group -mx-3 block rounded-lg px-3 py-3 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline gap-3">
        <span className="font-medium underline-offset-4 group-hover:underline">{card.title}</span>
        {named && <span className="font-mono text-meta text-muted-foreground">{card.technique}</span>}
        <span className="ml-auto shrink-0 text-meta text-muted-foreground tabular-nums">
          {templates(card.templates.length, optional)}
        </span>
      </div>
      {/* the trigger says when to reach for the technique, which is what a
          reader picks a card by */}
      <p className="mt-1 line-clamp-2 text-meta text-muted-foreground">{plain(card.trigger)}</p>
    </Link>
  )
}

function templates(count: number, optional: number): string {
  const all = count === 1 ? '1 template' : `${count} templates`
  return optional === 0 ? all : `${all}, ${optional} optional`
}

type Block = { technique: string; cards: Card[] } | { cards: Card[] }

// the API orders the cards by technique. A technique with one card is a row
// like any other, since a heading over a single row names what the row says
function blocks(cards: Card[]): Block[] {
  const out: Block[] = []
  for (const card of cards) {
    const last = out.at(-1)
    const taught = cards.filter((one) => one.technique === card.technique)
    if (taught.length > 1) {
      if (last && 'technique' in last && last.technique === card.technique) last.cards.push(card)
      else out.push({ technique: card.technique, cards: [card] })
    } else if (last && !('technique' in last)) last.cards.push(card)
    else out.push({ cards: [card] })
  }
  return out
}
