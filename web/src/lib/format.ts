export function share(solved: number, attempts: number): string {
  return attempts === 0 ? '—' : `${solved}/${attempts}`
}

export function lastAt(at: string | null | undefined): string {
  if (!at) return 'never'
  const days = Math.max(0, Math.floor((Date.now() - new Date(at).getTime()) / 86_400_000))
  return `${new Date(at).toLocaleDateString()} (${days}d ago)`
}
