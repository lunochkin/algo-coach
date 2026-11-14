import {
  cardRow as cardRowAt,
  lastAt as lastAtFrom,
  problemFacts as problemFactsAt,
  techniqueStats,
  templateView as templateViewAt,
} from '@climb/core'

export { duration, share } from '@climb/core'

// the core's wording, read at the moment the page renders
export function lastAt(at: string | null | undefined): string {
  return lastAtFrom(at, Date.now())
}

export function counts(row: Parameters<typeof techniqueStats>[0]) {
  return techniqueStats(row, Date.now())
}

export function cardRow(card: Parameters<typeof cardRowAt>[0], heading: string | null) {
  return cardRowAt(card, heading, Date.now())
}

export function templateView(
  template: Parameters<typeof templateViewAt>[0],
  recalled: Parameters<typeof templateViewAt>[1],
) {
  return templateViewAt(template, recalled, Date.now())
}

export function problemFacts<C extends Parameters<typeof problemFactsAt>[1][number]>(
  picked: Parameters<typeof problemFactsAt>[0],
  cards: C[],
  technique: string | null,
) {
  return problemFactsAt(picked, cards, technique, Date.now())
}
