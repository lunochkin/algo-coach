import { Link } from 'react-router'

import { api, type Card } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'

export function CardsPage() {
  const { data: cards, error } = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  if (error) return <p className="text-destructive">The cards did not load: {error}</p>
  if (!cards) return <p className="text-muted-foreground">Loading the cards…</p>

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Cards</h1>
      {cards.length === 0 ? (
        <p className="text-muted-foreground">No card is seeded yet.</p>
      ) : (
        byTechnique(cards).map(([technique, group]) => (
          <div key={technique} className="space-y-2">
            <h2 className="text-lg font-medium">{technique}</h2>
            <ul className="space-y-1">
              {group.map((card) => (
                <li key={card.slug} className="flex items-baseline gap-2">
                  <Link
                    to={`/cards/${encodeURIComponent(card.slug)}`}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {card.title}
                  </Link>
                  <span className="text-sm text-muted-foreground">
                    {card.templates.length} template(s)
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
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
