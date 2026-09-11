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

export function lastAt(at: string | null | undefined): string {
  if (!at) return 'never'
  const days = Math.max(0, Math.floor((Date.now() - new Date(at).getTime()) / 86_400_000))
  return `${new Date(at).toLocaleDateString()} (${days}d ago)`
}
