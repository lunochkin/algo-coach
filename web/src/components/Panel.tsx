import type { ReactNode } from 'react'

// a bordered block on the card surface: what a page holds beside its reading,
// as the run's counts on a card and the press that starts a sitting
export function Panel({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-stack rounded-xl border bg-card px-4 py-3">{children}</div>
  )
}

// one count and what it counts, read as a pair
export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <span className="flex flex-col leading-tight">
      <span className="text-heading tabular-nums">{value}</span>
      <span className="text-meta text-muted-foreground">{label}</span>
    </span>
  )
}

// the counts of one panel, in a row that wraps
export function Stats({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-center gap-x-8 gap-y-stack">{children}</div>
}
