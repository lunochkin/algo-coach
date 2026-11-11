import {
  cardRow as cardRowAt,
  lastAt as lastAtFrom,
  problemTried,
  recallLine as recallLineAt,
  techniqueStats,
} from '@algo-coach/core'

export { duration, share } from '@algo-coach/core'

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

export function recallLine(one: Parameters<typeof recallLineAt>[0]) {
  return recallLineAt(one, Date.now())
}

export function tried(picked: Parameters<typeof problemTried>[0]) {
  return problemTried(picked, Date.now())
}
