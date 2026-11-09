export function share(solved: number, attempts: number): string {
  return attempts === 0 ? '—' : `${solved}/${attempts}`
}

export function duration(seconds: number): string {
  const whole = Math.floor(seconds)
  const hours = Math.floor(whole / 3600)
  const minutes = Math.floor((whole % 3600) / 60)
  const rest = String(whole % 60).padStart(2, '0')
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}` : `${minutes}:${rest}`
}

// in the words the page reads in: a date is precision nobody acts on, and the
// distance is what says whether the technique has gone stale
export function lastAt(at: string | null | undefined): string {
  if (!at) return 'never'
  const days = Math.max(0, Math.floor((Date.now() - new Date(at).getTime()) / 86_400_000))
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 30) return `${days} days ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return new Date(at).toLocaleDateString()
}

// an untouched row reads as one word: three counts of nothing say less than
// `never` does
export function counts(row: {
  attempt_count: number
  solved_count: number
  last_attempt_at?: string | null
}): { label: string; value: string | number }[] {
  if (row.attempt_count === 0) return [{ label: 'attempted', value: 'never' }]
  return [
    { label: row.attempt_count === 1 ? 'attempt' : 'attempts', value: row.attempt_count },
    { label: 'solved', value: share(row.solved_count, row.attempt_count) },
    { label: '', value: lastAt(row.last_attempt_at) },
  ]
}

// a card's trigger is authored as markdown, and a clamped preview has no room
// to render it. The marks are dropped rather than printed as asterisks
export function plain(markdown: string): string {
  return markdown
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}
