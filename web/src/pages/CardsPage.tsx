import { cardBlocks, inProgress } from '@algo-coach/core'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'

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
                  {cardBlocks(rest).map((block) => (
                    <CardPanel
                      key={block.technique ?? block.cards[0].slug}
                      technique={block.technique}
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
