import type { ListedCard } from '@/api/client'

// the cards with a run open, the most recently active first: the ones the
// user is working through, on the cards list and on the board alike
export function inProgress(cards: ListedCard[]): ListedCard[] {
  return cards
    .filter((card) => card.status.started_at)
    .sort((a, b) => (b.status.last_at ?? '').localeCompare(a.status.last_at ?? ''))
}
