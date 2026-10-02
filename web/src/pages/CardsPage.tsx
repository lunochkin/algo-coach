import { api, type ListedCard } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { inProgress } from '@/lib/cards'

export function CardsPage() {
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  return (
    <section className="space-y-section">
      <PageHeader
        title="Cards"
        note="One card teaches one technique: when to reach for it, and the forms to reproduce from memory."
      />
      <Loaded of="the cards" state={cards} blank="No card is seeded yet.">
        {(cards) => {
          // the cards with a run open read first, the most recently active
          // first: they are the ones the user is working through
          const studying = inProgress(cards)
          const rest = cards.filter((card) => !card.status.started_at)
          return (
            <div className="space-y-section">
              {studying.length > 0 && (
                <section className="space-y-stack">
                  <SectionHeading title="Studying" count={studying.length} />
                  <CardPanel technique={null} cards={studying} />
                </section>
              )}
              {rest.length > 0 && (
                <section className="space-y-stack">
                  {studying.length > 0 && (
                    <SectionHeading title="Not started" count={rest.length} />
                  )}
                  {blocks(rest).map((block) => (
                    <CardPanel
                      key={'technique' in block ? block.technique : block.cards[0].slug}
                      technique={'technique' in block ? block.technique : null}
                      cards={block.cards}
                    />
                  ))}
                </section>
              )}
            </div>
          )
        }}
      </Loaded>
    </section>
  )
}

type Block = { technique: string; cards: ListedCard[] } | { cards: ListedCard[] }

// the API orders the cards by family, the technique a narrower one is a kind
// of. A family with one card is a row like any other, since a heading over a
// single row names what the row says
function blocks(cards: ListedCard[]): Block[] {
  const out: Block[] = []
  for (const card of cards) {
    const last = out.at(-1)
    const taught = cards.filter((one) => one.family === card.family)
    if (taught.length > 1) {
      if (last && 'technique' in last && last.technique === card.family) last.cards.push(card)
      else out.push({ technique: card.family, cards: [card] })
    } else if (last && !('technique' in last)) last.cards.push(card)
    else out.push({ cards: [card] })
  }
  return out
}
