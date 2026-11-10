import {
  cardRow as cardRowAt,
  lastAt as lastAtFrom,
  problemTried,
  recallLine as recallLineAt,
  techniqueStats,
} from '@algo-coach/core'

export { share } from '@algo-coach/core'

export function duration(seconds: number): string {
  const whole = Math.floor(seconds)
  const hours = Math.floor(whole / 3600)
  const minutes = Math.floor((whole % 3600) / 60)
  const rest = String(whole % 60).padStart(2, '0')
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}` : `${minutes}:${rest}`
}

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
