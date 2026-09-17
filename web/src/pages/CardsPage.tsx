import { Link } from 'react-router'

import { api, type Card } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'

export function CardsPage() {
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  return (
    <section className="space-y-section">
      <PageHeader title="Cards" />
      <Loaded of="the cards" state={cards} blank="No card is seeded yet.">
        {(cards) => (
          <div className="space-y-section">
            {byTechnique(cards).map(([technique, group]) => (
              <div key={technique} className="space-y-2">
                <h2 className="text-heading font-medium">{technique}</h2>
                <ul className="space-y-1">
                  {group.map((card) => (
                    <li key={card.slug} className="flex items-baseline gap-2">
                      <Link
                        to={`/cards/${encodeURIComponent(card.slug)}`}
                        className="font-medium underline-offset-4 hover:underline"
                      >
                        {card.title}
                      </Link>
                      <span className="text-meta text-muted-foreground">
                        {card.templates.length === 1
                          ? '1 template'
                          : `${card.templates.length} templates`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </Loaded>
    </section>
  )
}

// the API orders the cards by technique, so a group is a run of neighbours
function byTechnique(cards: Card[]): [string, Card[]][] {
  const groups: [string, Card[]][] = []
  for (const card of cards) {
    const last = groups.at(-1)
    if (last && last[0] === card.technique) last[1].push(card)
    else groups.push([card.technique, [card]])
  }
  return groups
}
