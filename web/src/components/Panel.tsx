import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

// a bordered block on the card surface: what a page holds beside its reading,
// as the run's counts on a card and the press that starts a sitting
export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('space-y-stack rounded-xl border bg-card px-4 py-3', className)}>
      {children}
    </div>
  )
}

// the same edge with no inset, for a panel headed by its strip
export function PanelFrame({ children }: { children: ReactNode }) {
  return <div className="overflow-hidden rounded-xl border bg-card">{children}</div>
}

// the strip heading a panel: it names what the panel holds, and where it
// names a record it opens it
export function PanelStrip({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b bg-card px-4 py-3">
      {children}
    </div>
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
