import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { cn } from '@/lib/utils'

type Props = {
  to: string
  title: string
  // before the title: a rung's solved mark
  lead?: ReactNode
  // the badge beside the title: a difficulty, a requiredness, a paused module
  badge?: ReactNode
  // the counts, right-aligned: each a label and its reading
  stats: { label: string; value: ReactNode }[]
  // the lines under the title, such as the techniques a problem carries
  note?: ReactNode
  // a note naming techniques reads in the code font
  mono?: boolean
  // a row the user cannot act on yet, such as a locked lesson
  dim?: boolean
  // presses beside the counts, such as a module's order
  aside?: ReactNode
}

// one pick on a list of picks: a technique on the board, a problem, a module,
// a lesson. The whole row is the link, so the pointer never hunts for the
// title, and the counts read as one cluster rather than as four columns. The
// title's link stretches over the row, so a press in `aside` stays its own
export function PickRow({ to, title, lead, badge, stats, note, mono, dim, aside }: Props) {
  return (
    <div
      className={cn(
        'group relative flex items-center gap-3 px-4 py-3 transition-colors hover:bg-accent',
        dim && 'opacity-70',
      )}
    >
      {lead}
      <span className="min-w-0">
        <span className="flex items-baseline gap-3">
          <Link
            to={to}
            className="font-medium underline-offset-4 after:absolute after:inset-0 group-hover:underline"
          >
            {title}
          </Link>
          {badge}
        </span>
        {note && (
          <span className={cn('mt-1 block text-meta text-muted-foreground', mono && 'font-mono')}>
            {note}
          </span>
        )}
      </span>
      <span className="ml-auto flex shrink-0 items-center gap-5 text-meta text-muted-foreground">
        {stats.map((stat, i) => (
          <span key={i} className="flex items-baseline gap-1.5">
            <span className="tabular-nums text-foreground">{stat.value}</span>
            {stat.label}
          </span>
        ))}
      </span>
      {aside && <span className="relative flex shrink-0 gap-1">{aside}</span>}
    </div>
  )
}

// the rows of one list, in one bordered panel and divided by a hairline
export function PickPanel({ children }: { children: ReactNode }) {
  return (
    <div className="divide-y divide-border overflow-hidden rounded-xl border bg-card">
      {children}
    </div>
  )
}

// the rows alone, for a panel some other part draws, such as a card's section
export function PickList({ children }: { children: ReactNode }) {
  return <div className="divide-y divide-border">{children}</div>
}
