import {
  cardBlocks,
  inProgress,
  notInProgress,
  CARDS_TITLE,
  OF,
  CARDS_NONE,
  CARDS_STUDYING,
  CARDS_NOT_STARTED,
  CARDS_NOTE,
} from '@algo-coach/core'

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
      <PageHeader title={CARDS_TITLE} note={CARDS_NOTE} />
      <Loaded of={OF.cards} state={cards} blank={CARDS_NONE}>
        {(cards) => {
          // the cards with a run open read first, the most recently active
          // first: they are the ones the user is working through
          const studying = inProgress(cards)
          const rest = notInProgress(cards)
          return (
            <div className="space-y-section">
              {studying.length > 0 && (
                <section className="space-y-stack">
                  <SectionHeading title={CARDS_STUDYING} count={studying.length} />
                  <CardPanel technique={null} cards={studying} />
                </section>
              )}
              {rest.length > 0 && (
                <section className="space-y-stack">
                  {studying.length > 0 && (
                    <SectionHeading title={CARDS_NOT_STARTED} count={rest.length} />
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
