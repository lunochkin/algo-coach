import { Link } from 'react-router'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'

// offered beside the loop, never in its way: no sitting requires a card
export function TechniqueCards({ technique }: { technique: string }) {
  const { data: cards, error } = useLoaded(
    (signal) =>
      api.GET('/api/techniques/{technique}/cards', { params: { path: { technique } }, signal }),
    `technique-cards:${technique}`,
  )

  if (error) return <p className="text-sm text-destructive">The cards did not load: {error}</p>
  if (!cards || cards.length === 0) return null

  return (
    <p className="text-sm text-muted-foreground">
      {cards.length === 1 ? 'Card' : 'Cards'}:{' '}
      {cards.map((card, index) => (
        <span key={card.slug}>
          {index > 0 && ', '}
          <Link
            to={`/cards/${encodeURIComponent(card.slug)}`}
            className="font-medium text-foreground underline-offset-4 hover:underline"
          >
            {card.title}
          </Link>
        </span>
      ))}
    </p>
  )
}
