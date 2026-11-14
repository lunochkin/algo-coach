import { cardEdges, depthSections, CARDS_TITLE, OF, CARDS_NONE, CARDS_NOTE } from '@climb/core'
import { useState } from 'react'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { CardGraph } from '@/components/CardGraph'
import { CardPanel } from '@/components/CardPanel'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'

export function CardsPage() {
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')
  const [hovered, setHovered] = useState<string | null>(null)

  return (
    <section className="space-y-section">
      <PageHeader title={CARDS_TITLE} note={CARDS_NOTE} />
      <Loaded of={OF.cards} state={cards} blank={CARDS_NONE}>
        {(cards) => (
          // the card graph by depth, the roots first: `pages.md`. A started
          // card reads its progress in its own row, so no card is listed twice
          <CardGraph edges={cardEdges(cards)} hovered={hovered}>
            <div className="space-y-section">
              {depthSections(cards).map((section) => (
                <section key={section.depth} className="space-y-stack">
                  <SectionHeading title={section.title} count={section.cards.length} />
                  <CardPanel technique={null} cards={section.cards} onHover={setHovered} />
                </section>
              ))}
            </div>
          </CardGraph>
        )}
      </Loaded>
    </section>
  )
}
